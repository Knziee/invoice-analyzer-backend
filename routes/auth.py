import jwt
import os
from flask import Blueprint, request, jsonify
from models import session, Usuario
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

auth_bp = Blueprint('auth', __name__)

load_dotenv() 
SECRET_KEY = os.environ.get("SECRET_KEY")

# ----------------------
# Criar usuário
# ----------------------
@auth_bp.route('/usuarios', methods=['POST'])
def criar_usuario():
    data = request.json
    if session.query(Usuario).filter_by(username=data['username']).first():
        return jsonify({"error": "Usuário já existe"}), 400
    user = Usuario(username=data['username'])
    user.set_password(data['password'])
    session.add(user)
    session.commit()
    return jsonify({"message": "Usuário criado com sucesso"}), 201

# ----------------------
# Login
# ----------------------
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    user = session.query(Usuario).filter_by(username=data['username']).first()
    if not user or not user.check_password(data['password']):
        return jsonify({"error": "Usuário ou senha incorretos"}), 401
    
    token = jwt.encode({
        "user_id": user.id,
        "exp": datetime.now(timezone.utc) + timedelta(days=30)
    }, SECRET_KEY, algorithm="HS256")

    return jsonify({"token": token})
