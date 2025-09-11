import os
import jwt
from functools import wraps
from flask import request, jsonify
from models import session, Usuario
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.environ.get("SECRET_KEY")


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

        if not token:
            return jsonify({"error": "Token ausente"}), 401

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user = session.query(Usuario).filter_by(id=data['user_id']).first()
            if not current_user:
                return jsonify({"error": "Usuário inválido"}), 401
        except Exception:
            return jsonify({"error": "Token inválido"}), 401

        return f(current_user, *args, **kwargs)

    return decorated
