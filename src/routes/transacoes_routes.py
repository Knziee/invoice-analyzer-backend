import os
import random
from flask import Blueprint, request, jsonify, send_file
from dotenv import load_dotenv
from services.transacoes_service import (
    processar_csv, processar_pdf, listar_transacoes, listar_categorias,
    criar_transacao, editar_transacao, deletar_transacao,
    gerar_fatura_pdf, gerar_fatura_csv
)
from utils.decorator import token_required

load_dotenv()
SECRET_KEY = os.environ.get("SECRET_KEY")

transacoes_bp = Blueprint('transacoes', __name__)


@transacoes_bp.route('/upload', methods=['POST'])
@token_required
def route_upload_csv(current_user):
    file = request.files.get('file')
    try:
        resp = processar_csv(current_user, file)
        return jsonify(resp)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@transacoes_bp.route('/upload/pdf', methods=['POST'])
@token_required
def route_upload_pdf(current_user):
    file = request.files.get('file')
    try:
        resp = processar_pdf(current_user, file)
        return jsonify(resp)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@transacoes_bp.route('/transacoes', methods=['GET'])
@token_required
def route_listar_transacoes(current_user):
    filtros = {
        "categoria": request.args.get('categoria'),
        "data_inicio": request.args.get('data_inicio'),
        "data_fim": request.args.get('data_fim'),
        "valor_min": request.args.get('valor_min'),
        "valor_max": request.args.get('valor_max'),
        "busca": request.args.get('busca')
    }
    try:
        transacoes = listar_transacoes(current_user, filtros)
        return jsonify([{
            "id": t.id,
            "data": t.data.strftime('%Y-%m-%d'),
            "descricao": t.descricao,
            "valor": t.valor,
            "categoria": t.categoria
        } for t in transacoes])
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@transacoes_bp.route('/categorias', methods=['GET'])
@token_required
def route_listar_categorias(current_user):
    categorias = listar_categorias(current_user)
    return jsonify({"categorias": categorias})


@transacoes_bp.route('/transacoes', methods=['POST'])
@token_required
def route_criar_transacao(current_user):
    data = request.json or {}
    try:
        transacao = criar_transacao(current_user, data)
        return jsonify({
            "message": "Transação criada com sucesso!",
            "transacao": {
                "id": transacao.id,
                "data": transacao.data.strftime('%Y-%m-%d'),
                "descricao": transacao.descricao,
                "valor": transacao.valor,
                "categoria": transacao.categoria
            }
        }), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@transacoes_bp.route('/transacoes/<int:id>', methods=['PUT'])
@token_required
def route_editar_transacao(current_user, id):
    data = request.json or {}
    transacao = editar_transacao(current_user, id, data)
    if not transacao:
        return jsonify({"error": "Transação não encontrada"}), 404
    return jsonify({"message": "Transação atualizada"})


@transacoes_bp.route('/transacoes/<int:id>', methods=['DELETE'])
@token_required
def route_deletar_transacao(current_user, id):
    transacao = deletar_transacao(current_user, id)
    if not transacao:
        return jsonify({"error": "Transação não encontrada"}), 404
    return jsonify({"message": "Transação deletada"})


@transacoes_bp.route("/fatura/pdf", methods=["GET"])
@token_required
def route_gerar_fatura_pdf(current_user):
    buffer = gerar_fatura_pdf(qtd_itens=random.randint(5, 30))
    return send_file(buffer, as_attachment=True, download_name="fatura_simulada.pdf", mimetype="application/pdf")


@transacoes_bp.route("/fatura/csv", methods=["GET"])
@token_required
def route_gerar_fatura_csv(current_user):
    buffer = gerar_fatura_csv(qtd_itens=random.randint(5, 30))
    return send_file(buffer, as_attachment=True, download_name="fatura_simulada.csv", mimetype="text/csv")
