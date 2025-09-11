import jwt
import os
from datetime import datetime, timedelta, timezone
from models import session, Usuario

SECRET_KEY = os.environ.get("SECRET_KEY")

def criar_usuario(data):
    if session.query(Usuario).filter_by(username=data['username']).first():
        return {"error": "Usuário já existe"}, 400
    
    user = Usuario(username=data['username'])
    user.set_password(data['password'])
    session.add(user)
    session.commit()
    return {"message": "Usuário criado com sucesso"}, 201


def login(data):
    user = session.query(Usuario).filter_by(username=data['username']).first()
    if not user or not user.check_password(data['password']):
        return {"error": "Usuario ou senha incorretos"}, 401
    
    token = jwt.encode({
        "user_id": user.id,
        "exp": datetime.now(timezone.utc) + timedelta(days=30)
    }, SECRET_KEY, algorithm="HS256")

    return {"token": token}, 200
