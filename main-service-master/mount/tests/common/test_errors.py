from app.common import errors


def test_errors_1():
    val = errors.E.get('members_credentials_not_available')
    assert val is not None

