import os
from flask import Blueprint, request, jsonify
from functools import wraps
from sqlalchemy import func, extract, and_
from datetime import datetime
from models import session, Transacao, Usuario
import jwt
from dotenv import load_dotenv

charts_bp = Blueprint('charts', __name__)

load_dotenv()
SECRET_KEY = os.environ.get("SECRET_KEY")

# ----------------------
# Decorator JWT
# ----------------------
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
        if not token:
            return jsonify({"error": "Token ausente"}), 401
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user = session.query(Usuario).filter_by(id=data['user_id']).first()
            if not current_user:
                return jsonify({"error": "Usuário inválido"}), 401
        except:
            return jsonify({"error": "Token inválido"}), 401
        return f(current_user, *args, **kwargs)
    return decorated

# ----------------------
# Gastos por categoria
# ----------------------
@charts_bp.route('/charts/categoria', methods=['GET'])
@token_required
def gastos_por_categoria(current_user):
    categoria = request.args.get('categoria') 
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')

    filtros = [Transacao.user_id == current_user.id]

    if categoria:
        filtros.append(func.lower(Transacao.categoria) == categoria.lower())

    if data_inicio:
        try:
            dt_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
            filtros.append(Transacao.data >= dt_inicio)
        except ValueError:
            return jsonify({"error": "Formato de data_inicio inválido"}), 400

    if data_fim:
        try:
            dt_fim = datetime.strptime(data_fim, '%Y-%m-%d')
            filtros.append(Transacao.data <= dt_fim)
        except ValueError:
            return jsonify({"error": "Formato de data_fim inválido"}), 400

    resultado = (
        session.query(
            Transacao.categoria,
            func.sum(Transacao.valor).label('valor_total')
        )
        .filter(and_(*filtros))
        .group_by(Transacao.categoria)
        .order_by(func.sum(Transacao.valor).desc())
        .all()
    )
    
    total = sum([r.valor_total for r in resultado])
    resposta = [
        {
            "categoria": r.categoria,
            "valor": float(r.valor_total),
            "percentual": round(float(r.valor_total)/total*100, 2) if total > 0 else 0
        }
        for r in resultado
    ]
    return jsonify(resposta)

# ----------------------
# Gastos gerais por mês
# ----------------------
@charts_bp.route('/charts/geral', methods=['GET'])
@token_required
def gastos_gerais(current_user):
    categoria = request.args.get('categoria') 
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')

    filtros = [Transacao.user_id == current_user.id]

    if categoria:
        filtros.append(func.lower(Transacao.categoria) == categoria.lower())

    if data_inicio:
        try:
            dt_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
            filtros.append(Transacao.data >= dt_inicio)
        except ValueError:
            return jsonify({"error": "Formato de data_inicio inválido"}), 400

    if data_fim:
        try:
            dt_fim = datetime.strptime(data_fim, '%Y-%m-%d')
            filtros.append(Transacao.data <= dt_fim)
        except ValueError:
            return jsonify({"error": "Formato de data_fim inválido"}), 400

    meses = (
        session.query(
            extract('month', Transacao.data).label('mes'),
            func.sum(Transacao.valor).label('valor_total')
        )
        .filter(and_(*filtros))
        .group_by('mes')
        .order_by('mes')
        .all()
    )

    mes_nome = {
        1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr",
        5: "Mai", 6: "Jun", 7: "Jul", 8: "Ago",
        9: "Set", 10: "Out", 11: "Nov", 12: "Dez"
    }

    total = sum([m.valor_total for m in meses])

    return jsonify({
        "meses": [{"mes": mes_nome[int(m.mes)], "valor": float(m.valor_total)} for m in meses],
        "soma_total": float(total)
    })


# ----------------------
# Insights / curiosidades
# ----------------------
@charts_bp.route('/charts/insights', methods=['GET'])
@token_required
def insights(current_user):
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')

    filtros = [Transacao.user_id == current_user.id]

    if data_inicio:
        try:
            dt_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
            filtros.append(Transacao.data >= dt_inicio)
        except ValueError:
            return jsonify({"error": "Formato de data_inicio inválido"}), 400

    if data_fim:
        try:
            dt_fim = datetime.strptime(data_fim, '%Y-%m-%d')
            filtros.append(Transacao.data <= dt_fim)
        except ValueError:
            return jsonify({"error": "Formato de data_fim inválido"}), 400

    maior_categoria = (
        session.query(
            Transacao.categoria,
            func.sum(Transacao.valor).label('valor_total')
        )
        .filter(and_(*filtros))
        .group_by(Transacao.categoria)
        .order_by(func.sum(Transacao.valor).desc())
        .first()
    )

    media_semanal = (
        session.query(
            func.avg(Transacao.valor).label('media')
        )
        .filter(and_(*filtros))
        .scalar()
    )

    maior_gasto = (
        session.query(Transacao)
        .filter(and_(*filtros))
        .order_by(Transacao.valor.desc())
        .first()
    )

    menor_gasto = (
        session.query(Transacao)
        .filter(and_(*filtros))
        .order_by(Transacao.valor.asc())
        .first()
    )

    dia_mes_media = (
        session.query(
            extract('day', Transacao.data).label('dia_mes'),
            func.avg(Transacao.valor).label('media_valor')
        )
        .filter(and_(*filtros))
        .group_by('dia_mes')
        .order_by(func.avg(Transacao.valor).desc())
        .first()
    )

    return jsonify({
        "maior_categoria": maior_categoria.categoria if maior_categoria else None,
        "maior_categoria_valor": float(maior_categoria.valor_total) if maior_categoria else 0,
        "media_semanal": float(media_semanal) if media_semanal else 0,
        "maior_gasto": {"descricao": maior_gasto.descricao, "valor": float(maior_gasto.valor)} if maior_gasto else None,
        "menor_gasto": {"descricao": menor_gasto.descricao, "valor": float(menor_gasto.valor)} if menor_gasto else None,
        "dia_maior_gasto_media": int(dia_mes_media.dia_mes) if dia_mes_media else None
    })
