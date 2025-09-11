import os
from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
from services.graficos_service import gastos_por_categoria_service, gastos_gerais_service, insights_service
from utils.decorator import token_required

load_dotenv()
SECRET_KEY = os.environ.get("SECRET_KEY")

charts_bp = Blueprint('charts', __name__)

@charts_bp.route('/charts/categoria', methods=['GET'])
@token_required
def route_gastos_por_categoria(current_user):
    categoria = request.args.get('categoria')
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')

    try:
        resposta = gastos_por_categoria_service(current_user, categoria, data_inicio, data_fim)
        return jsonify(resposta)
    except ValueError:
        return jsonify({"error": "Formato de data inválido"}), 400


@charts_bp.route('/charts/geral', methods=['GET'])
@token_required
def route_gastos_gerais(current_user):
    categoria = request.args.get('categoria')
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')

    try:
        resposta = gastos_gerais_service(current_user, categoria, data_inicio, data_fim)
        return jsonify(resposta)
    except ValueError:
        return jsonify({"error": "Formato de data inválido"}), 400


@charts_bp.route('/charts/insights', methods=['GET'])
@token_required
def route_insights(current_user):
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')

    try:
        resposta = insights_service(current_user, data_inicio, data_fim)
        return jsonify(resposta)
    except ValueError:
        return jsonify({"error": "Formato de data inválido"}), 400
