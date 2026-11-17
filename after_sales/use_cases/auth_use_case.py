"""
Orquestación del flujo de autenticación de la app móvil de postventa.

Endpoints (ver `after_sales/urls.py`):
    identify                -> a qué pantalla enrutar según el estatus de cuenta
    verification_send       -> (re)enviar código SMS de 2FA
    verification_confirm    -> validar código SMS
    activate                -> establecer contraseña de una cuenta nueva (status 0)
    login                   -> correo/teléfono + contraseña
    token_refresh           -> intercambiar refresh token
    logout                  -> revocar refresh token (blacklist)
    password_reset_request  -> enviar código SMS para restablecer contraseña
    password_reset_confirm  -> validar código y fijar nueva contraseña
"""
from datetime import datetime, timedelta, timezone

from django.conf import settings

from after_sales.constants import (
    LOCKOUT_STATUS,
    PURPOSE_TO_VERIFICATION_TYPE,
    STATUS_ACTIVE,
    STATUS_DISABLED,
    STATUS_LOCKED,
    STATUS_PENDING,
    STATUS_ROUTE,
    VERIFICATION_LOGIN,
    VERIFICATION_PASSWORD_RESET,
)
from after_sales.helpers.errors import AuthError
from after_sales.helpers.identifiers import classify_identifier, mask_phone
from after_sales.helpers.otp import generate_code, hash_code, verify_code
from after_sales.helpers.passwords import (
    hash_password,
    validate_password_strength,
    verify_password,
)
from after_sales.helpers.responses import ok
from after_sales.helpers.service_method import endpoint
from after_sales.helpers.timeutils import to_utc, utcnow
from after_sales.helpers.tokens import (
    TOKEN_ACTIVATION,
    TOKEN_REFRESH,
    decode_token,
    issue_onboarding_token,
    issue_token_pair,
)
from after_sales.repositories.mongo import (
    AuthRepository,
    DeviceRepository,
    TokenBlacklistRepository,
    VerificationRepository,
)
from after_sales.serializers import (
    ActivateSerializer,
    IdentifySerializer,
    LoginSerializer,
    LogoutSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RefreshSerializer,
    VerificationConfirmSerializer,
    VerificationSendSerializer,
)
from after_sales.services.sms import send_verification_sms


def _code_ttl():
    return getattr(settings, "AUTH_SMS_CODE_LIFETIME", timedelta(minutes=10))


def _resend_cooldown():
    return getattr(settings, "AUTH_SMS_RESEND_COOLDOWN", timedelta(seconds=60))


def _max_code_attempts():
    return getattr(settings, "AUTH_SMS_MAX_ATTEMPTS", 5)


def _max_failed_logins():
    return getattr(settings, "AUTH_MAX_FAILED_ATTEMPTS", 5)


class AuthUseCase:
    def __init__(self, data=None):
        self.data = data or {}
        self.auth_repo = AuthRepository()
        self.verification_repo = VerificationRepository()
        self.device_repo = DeviceRepository()
        self.blacklist_repo = TokenBlacklistRepository()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _validated(self, serializer_cls):
        serializer = serializer_cls(data=self.data)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data

    def _resolve_identifier(self, raw):
        kind, value = classify_identifier(raw)
        if not kind:
            raise AuthError(
                "El identificador debe ser un correo o un teléfono válido.",
                code="invalid_identifier",
            )
        return kind, value

    def _get_auth(self, raw, leak=True):
        kind, value = self._resolve_identifier(raw)
        auth = self.auth_repo.find_by_identifier(kind, value)
        if not auth:
            if leak:
                raise AuthError(
                    "No encontramos una cuenta con ese dato.",
                    code="account_not_found",
                    status_code=404,
                )
            raise AuthError(
                "Usuario o contraseña no son válidos.",
                code="invalid_credentials",
            )
        return auth

    @staticmethod
    def _public_user(auth):
        return {
            "id": str(auth["_id"]),
            "user_id": str(auth["user_id"]) if auth.get("user_id") else None,
            "user_type": auth.get("user_type"),
            "email": auth.get("email"),
            "phone": auth.get("phone"),
            "status": auth.get("status"),
        }

    def _recently_sent(self, auth_id, verification_type):
        last = self.verification_repo.latest(auth_id, verification_type)
        if not last or not last.get("sent_at"):
            return False
        return utcnow() - to_utc(last["sent_at"]) < _resend_cooldown()

    def _enforce_cooldown(self, auth_id, verification_type):
        last = self.verification_repo.latest(auth_id, verification_type)
        if not last or not last.get("sent_at"):
            return
        elapsed = utcnow() - to_utc(last["sent_at"])
        cooldown = _resend_cooldown()
        if elapsed < cooldown:
            wait = int((cooldown - elapsed).total_seconds()) + 1
            raise AuthError(
                f"Espera {wait} segundos antes de solicitar otro código.",
                code="resend_cooldown",
                status_code=429,
            )

    def _issue_verification(self, auth, verification_type, device_id=None):
        code = generate_code()
        now = utcnow()
        self.verification_repo.create({
            "auth_id": str(auth["_id"]),
            "device_id": device_id,
            "verification_type": verification_type,
            "verification_method": "sms",
            "code": hash_code(code),
            "sent_at": now,
            "expires_at": now + _code_ttl(),
            "attempts": 0,
            "verified": False,
            "verified_at": None,
        })
        send_verification_sms(auth.get("phone"), code)
        return code

    def _consume_verification(self, auth, verification_type, raw_code):
        record = self.verification_repo.latest_pending(
            str(auth["_id"]), verification_type
        )
        if not record:
            raise AuthError(
                "No hay una verificación pendiente. Solicita un código nuevo.",
                code="verification_not_found",
            )
        if to_utc(record["expires_at"]) < utcnow():
            raise AuthError(
                "El código expiró. Solicita uno nuevo.", code="code_expired"
            )
        if record.get("attempts", 0) >= _max_code_attempts():
            raise AuthError(
                "Se agotaron los intentos. Solicita un código nuevo.",
                code="code_attempts_exceeded",
                status_code=429,
            )
        if not verify_code(raw_code, record.get("code")):
            self.verification_repo.increment_attempts(record["_id"])
            raise AuthError("El código no es correcto.", code="invalid_code")

        self.verification_repo.mark_verified(record["_id"])
        return record

    def _register_failed_login(self, auth):
        attempts = auth.get("failed_login_attempts", 0) + 1
        update = {"failed_login_attempts": attempts}
        disabled_now = attempts >= _max_failed_logins()
        if disabled_now:
            # No hay mecanismo de reactivación definido todavía
            # (manual por admin vs. expiración automática). Se deja como
            # estado terminal; ver resumen de la feature.
            update["status"] = LOCKOUT_STATUS
            update["locked_until"] = None
        self.auth_repo.update(auth["_id"], update)
        return disabled_now

    # ------------------------------------------------------------------
    # 1. identify
    # ------------------------------------------------------------------
    @endpoint
    def identify(self):
        data = self._validated(IdentifySerializer)
        # Decisión de producto: /auth/identify revela existencia y estatus
        # (404 si no existe), como el flujo de restablecimiento del panel.
        auth = self._get_auth(data["identifier"], leak=True)
        status = auth.get("status", STATUS_PENDING)
        kind, _ = classify_identifier(data["identifier"])
        return ok({
            "identifier_type": kind,
            "status": status,
            "next": STATUS_ROUTE.get(status, "login"),
            "has_password": bool(auth.get("password")),
        })

    # ------------------------------------------------------------------
    # 2. verification_send
    # ------------------------------------------------------------------
    @endpoint
    def verification_send(self):
        data = self._validated(VerificationSendSerializer)
        auth = self._get_auth(data["identifier"], leak=True)
        verification_type = PURPOSE_TO_VERIFICATION_TYPE[data["purpose"]]
        device_id = data.get("device_id")

        if verification_type == VERIFICATION_LOGIN:
            if auth.get("status") != STATUS_ACTIVE:
                raise AuthError(
                    "La cuenta no está activa.", code="account_not_active"
                )
            if not device_id:
                raise AuthError(
                    "device_id es obligatorio para verificar un dispositivo.",
                    code="device_id_required",
                )
            if self.device_repo.is_known(auth["_id"], device_id):
                raise AuthError(
                    "El dispositivo ya está registrado.", code="device_known"
                )
        else:  # activación
            if auth.get("status") != STATUS_PENDING:
                raise AuthError(
                    "La cuenta ya fue activada.", code="already_active"
                )

        self._enforce_cooldown(auth["_id"], verification_type)
        self._issue_verification(auth, verification_type, device_id=device_id)
        return ok({
            "sent": True,
            "channel": "sms",
            "phone_hint": mask_phone(auth.get("phone")),
            "expires_in": int(_code_ttl().total_seconds()),
            "resend_available_in": int(_resend_cooldown().total_seconds()),
        })

    # ------------------------------------------------------------------
    # 3. verification_confirm
    # ------------------------------------------------------------------
    @endpoint
    def verification_confirm(self):
        data = self._validated(VerificationConfirmSerializer)
        auth = self._get_auth(data["identifier"], leak=True)
        verification_type = PURPOSE_TO_VERIFICATION_TYPE[data["purpose"]]
        record = self._consume_verification(
            auth, verification_type, data["code"]
        )

        if verification_type == VERIFICATION_LOGIN:
            device_id = data.get("device_id") or record.get("device_id")
            if not device_id:
                raise AuthError(
                    "device_id es obligatorio.", code="device_id_required"
                )
            self.device_repo.register(
                auth["_id"],
                device_id,
                name=data.get("device_name"),
                device_type=data.get("device_type"),
            )
            self.auth_repo.update(
                auth["_id"],
                {"failed_login_attempts": 0, "last_login": utcnow()},
            )
            return ok({
                "verified": True,
                "user": self._public_user(auth),
                **issue_token_pair(auth),
            })

        # Activación: entregamos un token corto para /auth/activate/
        return ok({
            "verified": True,
            "next": "activate",
            "activation_token": issue_onboarding_token(auth, TOKEN_ACTIVATION),
        })

    # ------------------------------------------------------------------
    # 4. activate
    # ------------------------------------------------------------------
    @endpoint
    def activate(self):
        data = self._validated(ActivateSerializer)
        payload = decode_token(data["activation_token"], expected_type=TOKEN_ACTIVATION)
        auth = self.auth_repo.find_by_id(payload["sub"])
        if not auth:
            raise AuthError(
                "Cuenta no encontrada.", code="account_not_found", status_code=404
            )
        if auth.get("status") != STATUS_PENDING:
            raise AuthError("La cuenta ya fue activada.", code="already_active")

        password = data["password"]
        confirm = data.get("confirm_password")
        if confirm is not None and confirm != password:
            raise AuthError(
                "Las contraseñas no coinciden.", code="password_mismatch"
            )
        validate_password_strength(password)

        now = utcnow()
        self.auth_repo.update(auth["_id"], {
            "password": hash_password(password),
            "status": STATUS_ACTIVE,
            "failed_login_attempts": 0,
            "locked_until": None,
            "activated_at": now,
            "password_changed_at": now,
        })
        auth = {**auth, "status": STATUS_ACTIVE}

        device_id = data.get("device_id")
        if device_id:
            self.device_repo.register(
                auth["_id"],
                device_id,
                name=data.get("device_name"),
                device_type=data.get("device_type"),
                biometric=bool(data.get("biometric_enabled")),
            )

        return ok({
            "activated": True,
            "user": self._public_user(auth),
            **issue_token_pair(auth),
        })

    # ------------------------------------------------------------------
    # 5. login
    # ------------------------------------------------------------------
    @endpoint
    def login(self):
        data = self._validated(LoginSerializer)
        auth = self._get_auth(data["identifier"], leak=False)
        status = auth.get("status", STATUS_PENDING)

        if status == STATUS_PENDING:
            raise AuthError(
                "La cuenta no ha sido activada. Completa el primer acceso.",
                code="activation_required",
                status_code=403,
            )
        if status == STATUS_LOCKED:
            raise AuthError(
                "Tu cuenta está bloqueada. Contacta al administrador.",
                code="account_locked",
                status_code=403,
            )
        if status == STATUS_DISABLED:
            raise AuthError(
                "Tu cuenta fue deshabilitada por múltiples intentos fallidos. "
                "Contacta al administrador.",
                code="account_disabled",
                status_code=403,
            )
        if status != STATUS_ACTIVE:
            raise AuthError(
                "Usuario o contraseña no son válidos.",
                code="invalid_credentials",
            )

        if not verify_password(data["password"], auth.get("password")):
            disabled_now = self._register_failed_login(auth)
            if disabled_now:
                raise AuthError(
                    "Tu cuenta fue deshabilitada por múltiples intentos "
                    "fallidos. Contacta al administrador.",
                    code="account_disabled",
                    status_code=403,
                )
            raise AuthError(
                "Usuario o contraseña no son válidos.",
                code="invalid_credentials",
            )

        device_id = data.get("device_id")

        # Contraseña correcta pero dispositivo desconocido -> disparar 2FA.
        if device_id and not self.device_repo.is_known(auth["_id"], device_id):
            self.auth_repo.update(auth["_id"], {"failed_login_attempts": 0})
            # Evita reenviar SMS si ya se envió uno hace poco (mismo cooldown
            # que el reenvío manual); no es un error, sólo no se re-manda.
            if not self._recently_sent(auth["_id"], VERIFICATION_LOGIN):
                self._issue_verification(
                    auth, VERIFICATION_LOGIN, device_id=device_id
                )
            return ok({
                "verification_required": True,
                "channel": "sms",
                "phone_hint": mask_phone(auth.get("phone")),
                "expires_in": int(_code_ttl().total_seconds()),
            })

        self.auth_repo.update(
            auth["_id"], {"failed_login_attempts": 0, "last_login": utcnow()}
        )
        if device_id:
            self.device_repo.touch(auth["_id"], device_id)

        return ok({
            "user": self._public_user(auth),
            **issue_token_pair(auth),
        })

    # ------------------------------------------------------------------
    # 6. token_refresh
    # ------------------------------------------------------------------
    @endpoint
    def token_refresh(self):
        data = self._validated(RefreshSerializer)
        payload = decode_token(data["refresh"], expected_type=TOKEN_REFRESH)
        jti = payload.get("jti")
        if self.blacklist_repo.contains(jti):
            raise AuthError(
                "La sesión expiró. Inicia sesión nuevamente.",
                code="token_revoked",
                status_code=401,
            )
        auth = self.auth_repo.find_by_id(payload["sub"])
        if not auth or auth.get("status") != STATUS_ACTIVE:
            raise AuthError(
                "La sesión no es válida.",
                code="invalid_session",
                status_code=401,
            )

        # Rotación: se revoca el refresh usado y se emite un par nuevo.
        self.blacklist_repo.add(
            jti,
            datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
        )
        return ok(issue_token_pair(auth))

    # ------------------------------------------------------------------
    # 7. logout
    # ------------------------------------------------------------------
    @endpoint
    def logout(self):
        data = self._validated(LogoutSerializer)
        try:
            payload = decode_token(data["refresh"], expected_type=TOKEN_REFRESH)
        except AuthError:
            # Logout idempotente: un token ya inválido no es un error.
            return ok({"success": True})

        jti = payload.get("jti")
        if jti and not self.blacklist_repo.contains(jti):
            self.blacklist_repo.add(
                jti,
                datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
            )
        # NOTA: los access tokens son stateless y siguen siendo válidos hasta
        # su expiración (vida corta). Ver resumen de la feature.
        return ok({"success": True})

    # ------------------------------------------------------------------
    # 8a. password_reset_request
    # ------------------------------------------------------------------
    @endpoint
    def password_reset_request(self):
        data = self._validated(PasswordResetRequestSerializer)
        auth = self._get_auth(data["identifier"], leak=True)
        if auth.get("status") == STATUS_PENDING:
            raise AuthError(
                "La cuenta aún no ha sido activada. Completa el primer acceso.",
                code="activation_required",
            )
        if auth.get("status") == STATUS_LOCKED:
            raise AuthError(
                "Tu cuenta está bloqueada. Contacta al administrador.",
                code="account_locked",
                status_code=403,
            )

        self._enforce_cooldown(auth["_id"], VERIFICATION_PASSWORD_RESET)
        self._issue_verification(auth, VERIFICATION_PASSWORD_RESET)
        return ok({
            "sent": True,
            "channel": "sms",
            "phone_hint": mask_phone(auth.get("phone")),
            "expires_in": int(_code_ttl().total_seconds()),
        })

    # ------------------------------------------------------------------
    # 8b. password_reset_confirm
    # ------------------------------------------------------------------
    @endpoint
    def password_reset_confirm(self):
        data = self._validated(PasswordResetConfirmSerializer)
        auth = self._get_auth(data["identifier"], leak=True)
        self._consume_verification(
            auth, VERIFICATION_PASSWORD_RESET, data["code"]
        )

        password = data["password"]
        confirm = data.get("confirm_password")
        if confirm is not None and confirm != password:
            raise AuthError(
                "Las contraseñas no coinciden.", code="password_mismatch"
            )
        validate_password_strength(password)

        self.auth_repo.update(auth["_id"], {
            "password": hash_password(password),
            "password_changed_at": utcnow(),
            "failed_login_attempts": 0,
        })
        # NOTA: si la cuenta estaba deshabilitada (status 3) por intentos
        # fallidos, restablecer la contraseña NO la reactiva: no hay mecanismo
        # de reactivación definido. Ver resumen de la feature.
        return ok({"success": True})
