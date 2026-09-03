from functools import wraps

import jwt
from flask import current_app, jsonify, request


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")

        parts = auth_header.split()

        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({
                "error": "Invalid authorization header"
            }), 401

        token = parts[1]

        try:
            data = jwt.decode(
                token,
                current_app.config["SECRET_KEY"],
                algorithms=["HS256"]
            )

            if data.get("type") != "access":
                return jsonify({
                    "error": "Invalid token type"
                }), 401

            current_user = data.get("user_id")

            if current_user is None:
                return jsonify({
                    "error": "Invalid token"
                }), 401

        except jwt.ExpiredSignatureError:
            return jsonify({
                "error": "Token has expired"
            }), 401

        except jwt.InvalidTokenError:
            return jsonify({
                "error": "Invalid token"
            }), 401

        return f(current_user, *args, **kwargs)

    return decorated