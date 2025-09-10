import jwt
import os
from flask import Blueprint, request, jsonify
from functools import wraps
from models import session, Usuario, Transacao
import pandas as pd
from datetime import datetime
from sqlalchemy import and_, func
from dotenv import load_dotenv
from utils.categorias import categorizar

transacoes_bp = Blueprint('transacoes', __name__)

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
# Upload CSV
# ----------------------
@transacoes_bp.route('/upload', methods=['POST'])
@token_required
def upload_csv(current_user):
    file = request.files.get('file')
    if not file:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    try:
        df = pd.read_csv(file)
    except Exception as e:
        return jsonify({"error": f"Erro ao ler CSV: {str(e)}"}), 400

    required_columns = ['data', 'descricao', 'valor']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        return jsonify({"error": f"Colunas obrigatórias faltando: {', '.join(missing_cols)}"}), 400

    erros = []
    for i, row in df.iterrows():
        try:
            data = datetime.strptime(str(row['data']), '%Y-%m-%d')
            descricao = str(row['descricao'])
            valor = float(row['valor'])
            
            categoria = None
            if 'categoria' in row and pd.notna(row['categoria']):
                categoria = str(row['categoria'])
            else:
                categoria = categorizar(descricao)

            transacao = Transacao(
                data=data,
                descricao=descricao,
                valor=valor,
                categoria=categoria,
                user_id=current_user.id
            )
            session.add(transacao)
        except Exception as e:
            erros.append(f"Linha {i+1}: {str(e)}")
    
    if erros:
        return jsonify({"error": "Erros encontrados no CSV", "detalhes": erros}), 400

    session.commit()
    return jsonify({"message": "CSV processado com sucesso!"})


# ----------------------
# Listar transações
# ----------------------
@transacoes_bp.route('/transacoes', methods=['GET'])
@token_required
def listar_transacoes(current_user):
    query = session.query(Transacao).filter_by(user_id=current_user.id)

    categoria = request.args.get('categoria')  
    data_inicio = request.args.get('data_inicio')  # YYYY-MM-DD
    data_fim = request.args.get('data_fim')        # YYYY-MM-DD
    valor_min = request.args.get('valor_min')
    valor_max = request.args.get('valor_max')

    filtros = []

    if categoria:
        categorias = [c.strip().lower() for c in categoria.split(",") if c.strip()]
        if categorias:
            filtros.append(func.lower(Transacao.categoria).in_(categorias))


    if data_inicio:
        try:
            dt_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
            filtros.append(Transacao.data >= dt_inicio)
        except ValueError:
            return jsonify({"error": "Formato de data_inicio inválido, use YYYY-MM-DD"}), 400

    if data_fim:
        try:
            dt_fim = datetime.strptime(data_fim, '%Y-%m-%d')
            filtros.append(Transacao.data <= dt_fim)
        except ValueError:
            return jsonify({"error": "Formato de data_fim inválido, use YYYY-MM-DD"}), 400

    if valor_min:
        try:
            filtros.append(Transacao.valor >= float(valor_min))
        except ValueError:
            return jsonify({"error": "valor_min deve ser um número"}), 400

    if valor_max:
        try:
            filtros.append(Transacao.valor <= float(valor_max))
        except ValueError:
            return jsonify({"error": "valor_max deve ser um número"}), 400

    if filtros:
        query = query.filter(and_(*filtros))

    transacoes = query.all()

    return jsonify([{
        "id": t.id,
        "data": t.data.strftime('%Y-%m-%d'),
        "descricao": t.descricao,
        "valor": t.valor,
        "categoria": t.categoria
    } for t in transacoes])

# ----------------------
# Listar categorias do usuário
# ----------------------
@transacoes_bp.route('/categorias', methods=['GET'])
@token_required
def listar_categorias(current_user):
    categorias = (
        session.query(func.lower(Transacao.categoria)) 
        .filter_by(user_id=current_user.id)
        .distinct()
        .all()
    )

    categorias_lista = [c[0] for c in categorias if c[0]]  # remove None ou vazios

    return jsonify({"categorias": categorias_lista})


# ----------------------
# Criar transação manualmente
# ----------------------
@transacoes_bp.route('/transacoes', methods=['POST'])
@token_required
def criar_transacao(current_user):
    data = request.json or {}
    campos_obrigatorios = ['data', 'descricao', 'valor']
    faltando = [campo for campo in campos_obrigatorios if campo not in data]
    if faltando:
        return jsonify({"error": f"Campos obrigatórios faltando: {', '.join(faltando)}"}), 400

    try:
        valor = float(data['valor'])

        nova_transacao = Transacao(
            data=datetime.strptime(data['data'], '%Y-%m-%d'),
            descricao=data['descricao'],
            valor=valor,
            categoria=data.get('categoria'), 
            user_id=current_user.id
        )
        session.add(nova_transacao)
        session.commit()

        return jsonify({
            "message": "Transação criada com sucesso!",
            "transacao": {
                "id": nova_transacao.id,
                "data": nova_transacao.data.strftime('%Y-%m-%d'),
                "descricao": nova_transacao.descricao,
                "valor": nova_transacao.valor,
                "categoria": nova_transacao.categoria
            }
        }), 201
    except ValueError:
        return jsonify({"error": "Formato de data inválido. Use YYYY-MM-DD"}), 400

# ----------------------
# Editar transação
# ----------------------
@transacoes_bp.route('/transacoes/<int:id>', methods=['PUT'])
@token_required
def editar_transacao(current_user, id):
    data = request.json or {}
    transacao = session.query(Transacao).filter_by(id=id, user_id=current_user.id).first()
    if not transacao:
        return jsonify({"error": "Transação não encontrada"}), 404

    if 'data' in data:
        try:
            transacao.data = datetime.strptime(data['data'], '%Y-%m-%d')
        except ValueError:
            return jsonify({"error": "Formato de data inválido. Use YYYY-MM-DD"}), 400

    if 'valor' in data:
        try:
            transacao.valor = float(data['valor'])
        except ValueError:
            return jsonify({"error": "Valor deve ser numérico"}), 400

    transacao.descricao = data.get('descricao', transacao.descricao)
    transacao.categoria = data.get('categoria', transacao.categoria)
    session.commit()
    return jsonify({"message": "Transação atualizada"})

# ----------------------
# Deletar transação
# ----------------------
@transacoes_bp.route('/transacoes/<int:id>', methods=['DELETE'])
@token_required
def deletar_transacao(current_user, id):
    transacao = session.query(Transacao).filter_by(id=id, user_id=current_user.id).first()
    if not transacao:
        return jsonify({"error": "Transação não encontrada"}), 404
    session.delete(transacao)
    session.commit()
    return jsonify({"message": "Transação deletada"})
