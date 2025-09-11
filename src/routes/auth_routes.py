from flask import Blueprint, request, jsonify
from services.auth_service import criar_usuario, login

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/usuarios', methods=['POST'])
def route_criar_usuario():
    data = request.json
    response, status = criar_usuario(data)
    return jsonify(response), status


@auth_bp.route('/login', methods=['POST'])
def route_login():
    data = request.json
    response, status = login(data)
    return jsonify(response), status
