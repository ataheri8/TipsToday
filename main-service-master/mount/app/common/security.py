import string
import secrets
import bcrypt
import random

from app.common import logger


MIN_PASSWORD_LEN = 8


def generate_reset_code():
    return random.randint(100000, 999999)


def is_valid_password(pwd):
    if not pwd:
        return False

    if len(pwd) < MIN_PASSWORD_LEN:
        return False

    return True


def gen_random_password():
    alphabet = string.ascii_letters + string.digits
    length = 10
    rando = ''.join(secrets.choice(alphabet) for i in range(length))
    return rando


def hash_pass(password, encoding='utf-8'):
    return bcrypt.hashpw(password.encode(encoding), bcrypt.gensalt())


def pass_match(password, hashword, encoding='utf-8'):
    try:
        _pass = password.encode(encoding)
        _hash = hashword.encode(encoding)

        _match = bcrypt.checkpw(_pass, _hash)
        return _match

    except Exception as e:
        logger.warning("Password matching exception: ", e=e)
        return False


def get_hashword(raw_pass):
    hashword = hash_pass(raw_pass.strip()).decode('utf-8')
    return hashword
