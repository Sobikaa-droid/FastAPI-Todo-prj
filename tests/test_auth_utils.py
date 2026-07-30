import pytest
import bcrypt
from unittest.mock import patch
from datetime import timedelta

from src.auth.utils import encode_jwt, decode_jwt, hash_password, validate_password
from src.exceptions import jwt_exceptions


def test_encode_and_decode_jwt_success():
    token = encode_jwt(
        payload={
            "sub": "1",
            "username": "testusername",
            "type": "access",
        },
        expire_timedelta=timedelta(seconds=35)
    )

    decoded = decode_jwt(token)

    assert decoded["sub"] == "1"
    assert decoded["username"] == "testusername"
    assert decoded["type"] == "access"
    assert "iat" in decoded
    assert "exp" in decoded
    assert decoded["exp"] - decoded["iat"] == 35


def test_encode_jwt_missing_type():
    with pytest.raises(jwt_exceptions.JWTTypeError) as exc_info:
        encode_jwt(payload={"sub": "1"})

    assert "Missing token type" in str(exc_info.value)


def test_encode_jwt_wrong_type():
    wrong_type = 12345
    with pytest.raises(jwt_exceptions.JWTTypeError) as exc_info:
        encode_jwt(payload={"sub": "1", "type": wrong_type})

    assert f"Invalid token type: {wrong_type}" in str(exc_info.value)


def test_encode_jwt_missing_sub():
    with pytest.raises(jwt_exceptions.JWTInvalidError) as exc_info:
        encode_jwt(payload={"type": "access"})

    assert "Invalid token: missing subject" in str(exc_info.value)


def test_encode_jwt_failure():
    err_msg = "Some error message"
    with patch("jwt.encode") as mock_encode:
        mock_encode.side_effect = Exception(err_msg)

        with pytest.raises(jwt_exceptions.JWTEncodeError) as exc_info:
            encode_jwt(payload={"sub": "1", "type": "access"})

        assert f"Failed to encode JWT: {err_msg}" in str(exc_info.value)


def test_decode_jwt_missing_token():
    with pytest.raises(jwt_exceptions.JWTMissingError) as exc_info:
        decode_jwt(token=None)

    assert "Missing token" in str(exc_info.value)


def test_decode_jwt_invalid_token():
    with pytest.raises(jwt_exceptions.JWTInvalidError) as exc_info:
        decode_jwt(token="INVALID TOKEN")

    assert "Invalid token: Not enough segments" in str(exc_info.value)


def test_decode_jwt_expired_token():
    token = encode_jwt(
        payload={
            "sub": "1",
            "type": "access",
        },
        expire_timedelta=timedelta(seconds=-1)
    )

    with pytest.raises(jwt_exceptions.JWTExpiredError) as exc_info:
        decode_jwt(token)

    assert "Token is expired" in str(exc_info.value)


def test_decode_jwt_failure():
    token = encode_jwt(
        payload={
            "sub": "1",
            "type": "access",
        }
    )

    err_msg = "Some error message"
    with patch("jwt.decode") as mock_encode:
        mock_encode.side_effect = Exception(err_msg)

        with pytest.raises(jwt_exceptions.JWTDecodeError) as exc_info:
            decode_jwt(token)

        assert f"Failed to decode JWT: {err_msg}" in str(exc_info.value)


def test_decode_jwt_invalid_token_type():
    wrong_type = 12345
    with patch("jwt.decode") as mock_decode:
        mock_decode.return_value = {
            "sub": "1",
            "type": wrong_type,
            "exp": 1234567890,
            "iat": 1234567880
        }

        with pytest.raises(jwt_exceptions.JWTTypeError) as exc_info:
            decode_jwt("fake.token.string")

        assert f"Invalid token type: {wrong_type}" in str(exc_info.value)


def test_hash_password_success():
    password = "SomePassword12345"
    hashed_password = hash_password(password)
    assert bcrypt.checkpw(password.encode('utf-8'), hashed_password)


def test_validate_password_success():
    password = "SomePassword12345"
    hashed_password = hash_password(password)
    assert validate_password(password, hashed_password)


def test_validate_password_failure():
    password = "SomePassword12345"
    other_password = "OtherPassword12345"
    hashed_password = hash_password(other_password)
    assert not validate_password(password, hashed_password)