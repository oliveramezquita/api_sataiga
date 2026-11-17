from django.urls import path

from after_sales.views import (
    ActivateView,
    IdentifyView,
    LoginView,
    LogoutView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    TokenRefreshView,
    VerificationConfirmView,
    VerificationSendView,
)

urlpatterns = [
    path("auth/identify/", IdentifyView.as_view(), name="as-auth-identify"),
    path("auth/verification/send/", VerificationSendView.as_view(),
         name="as-auth-verification-send"),
    path("auth/verification/confirm/", VerificationConfirmView.as_view(),
         name="as-auth-verification-confirm"),
    path("auth/activate/", ActivateView.as_view(), name="as-auth-activate"),
    path("auth/login/", LoginView.as_view(), name="as-auth-login"),
    path("auth/token/refresh/", TokenRefreshView.as_view(),
         name="as-auth-token-refresh"),
    path("auth/logout/", LogoutView.as_view(), name="as-auth-logout"),
    path("auth/password/reset/request/", PasswordResetRequestView.as_view(),
         name="as-auth-password-reset-request"),
    path("auth/password/reset/confirm/", PasswordResetConfirmView.as_view(),
         name="as-auth-password-reset-confirm"),
]
