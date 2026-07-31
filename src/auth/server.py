import datetime
import os

import jwt
from flask import Flask, jsonify, request
from flask_mysqldb import MySQL
from werkzeug.security import check_password_hash

server = Flask(__name__)
mysql = MySQL(server)

JWT_SECRET = os.environ.get("JWT_SECRET")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD")
JWT_ISSUER = os.environ.get("JWT_ISSUER", "video-to-audio-auth")
JWT_AUDIENCE = os.environ.get("JWT_AUDIENCE", "video-to-audio-api")
JWT_TTL_SECONDS = int(os.environ.get("JWT_TTL_SECONDS", "3600"))

if (
    not JWT_SECRET
    or len(JWT_SECRET) < 32
    or JWT_SECRET.startswith("CHANGE_ME")
):
    raise RuntimeError("JWT_SECRET must be set to at least 32 characters")

if not MYSQL_PASSWORD or MYSQL_PASSWORD.startswith("CHANGE_ME"):
    raise RuntimeError("MYSQL_PASSWORD must be set to a deployment secret")

if JWT_TTL_SECONDS < 60 or JWT_TTL_SECONDS > 86400:
    raise RuntimeError("JWT_TTL_SECONDS must be between 60 and 86400")

# config
server.config["MYSQL_HOST"] = os.environ.get("MYSQL_HOST")
server.config["MYSQL_USER"] = os.environ.get("MYSQL_USER")
server.config["MYSQL_PASSWORD"] = MYSQL_PASSWORD
server.config["MYSQL_DB"] = os.environ.get("MYSQL_DB")
server.config["MYSQL_PORT"] = int(os.environ.get("MYSQL_PORT"))


@server.get("/healthz")
def healthz():
    return "ok", 200


@server.route("/login", methods=["POST"])
def login():
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return "missing credentials", 401

    cur = mysql.connection.cursor()
    try:
        res = cur.execute(
            "SELECT email, password, is_admin FROM user WHERE email=%s",
            (auth.username,),
        )
        user_row = cur.fetchone() if res > 0 else None
    finally:
        cur.close()

    if not user_row or not check_password_hash(user_row[1], auth.password):
        return "invalid credentials", 401

    return create_jwt(user_row[0], is_admin=bool(user_row[2]))


@server.route("/validate", methods=["POST"])
def validate():
    authorization = request.headers.get("Authorization")

    if not authorization:
        return "missing credentials", 401

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return "missing credentials", 401

    encoded_jwt = parts[1]

    try:
        decoded = jwt.decode(
            encoded_jwt,
            JWT_SECRET,
            algorithms=["HS256"],
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER,
            options={"require": ["exp", "iat", "sub", "admin"]},
        )
    except jwt.InvalidTokenError:
        return "not authorized", 401

    return jsonify(decoded), 200


def create_jwt(username, is_admin):
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    return jwt.encode(
        {
            "sub": username,
            "username": username,
            "iss": JWT_ISSUER,
            "aud": JWT_AUDIENCE,
            "exp": now + datetime.timedelta(seconds=JWT_TTL_SECONDS),
            "iat": now,
            "admin": is_admin,
        },
        JWT_SECRET,
        algorithm="HS256",
    )


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=5000)
