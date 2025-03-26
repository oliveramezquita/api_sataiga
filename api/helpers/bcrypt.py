import bcrypt


def encrypt_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())


def verify_password(password, hash_password):
    return bcrypt.checkpw(password.encode('utf-8'), hash_password)
