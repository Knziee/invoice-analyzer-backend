import random
import jwt
import os
import io
import csv
from flask import Blueprint, request, jsonify, send_file
import pdfplumber
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from functools import wraps
from models import session, Usuario, Transacao
import pandas as pd
from datetime import datetime
from sqlalchemy import and_, func
from dotenv import load_dotenv
from utils.categorias import categorizar
from utils.faturas import gerar_transacoes_fake
from utils.validators import padronizar_categoria, validar_transacao

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
                categoria = padronizar_categoria(str(row['categoria']))
            else:
                categoria = padronizar_categoria(categorizar(descricao))
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
# Upload PDF 
# ---------------------- 
@transacoes_bp.route('/upload/pdf', methods=['POST']) 
@token_required 
def upload_pdf(current_user): 
    file = request.files.get('file') 
    if not file: 
        return jsonify({"error": "Nenhum arquivo enviado"}), 400 
 
    if not file.filename.lower().endswith(".pdf"): 
        return jsonify({"error": "Arquivo deve ser PDF"}), 400 
 
    transacoes = [] 
    try: 
        with pdfplumber.open(file) as pdf: 
            for page in pdf.pages: 
                text = page.extract_text() 
                if not text: 
                    continue 
                 
                for linha in text.split("\n"): 
                    if "Fatura de Cartão" in linha or linha.strip() == "":
                        continue
                        
                    parts = [p.strip() for p in linha.split("|")] 
                    if len(parts) < 3: 
                        continue 
                    
                    data = parts[0] 
                    descricao = parts[1] 
                    valor_str = parts[2].strip() if parts[2].strip() != '-' else "0.0"
                    categoria = parts[3] if len(parts) > 3 and parts[3] != '-' else None 
                    
                    transacoes.append({ 
                        "data": data, 
                        "descricao": descricao, 
                        "valor": valor_str,  
                        "categoria": categoria 
                    }) 
                    
    except Exception as e: 
        return jsonify({"error": f"Erro ao ler PDF: {str(e)}"}), 400 
 
    erros = [] 
    transacoes_validas = []
    
    for i, t in enumerate(transacoes): 
        try: 
            data, descricao, valor, categoria = validar_transacao( 
                t['data'], t['descricao'], t['valor'], t.get('categoria') 
            ) 
            
            transacoes_validas.append({
                'data': data,
                'descricao': descricao, 
                'valor': valor,
                'categoria': categoria
            })
            
        except Exception as e: 
            erros.append(f"Linha {i+1}: {str(e)}") 
 
    if erros: 
        return jsonify({"error": "Erros encontrados no PDF", "detalhes": erros}), 400 

    try:
        for transacao_data in transacoes_validas:
            transacao = Transacao( 
                data=transacao_data['data'], 
                descricao=transacao_data['descricao'], 
                valor=transacao_data['valor'], 
                categoria=transacao_data['categoria'], 
                user_id=current_user.id 
            ) 
            session.add(transacao)
        
        session.commit() 
        return jsonify({
            "message": "PDF processado com sucesso!",
            "transacoes_processadas": len(transacoes_validas)
        })
        
    except Exception as e:
        session.rollback()
        return jsonify({"error": f"Erro ao salvar no banco: {str(e)}"}), 400

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
    busca = request.args.get('busca') 

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

    if busca:
        filtros.append(Transacao.descricao.ilike(f"%{busca}%"))

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
        data_val, descricao, valor, categoria = validar_transacao(
            data['data'], data['descricao'], data['valor'], data.get('categoria')
        )

        categoria = padronizar_categoria(categoria)

        nova_transacao = Transacao(
            data=data_val,
            descricao=descricao,
            valor=valor,
            categoria=categoria,
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
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

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

# ----------------------
# Rota - Gerar PDF
# ----------------------
@transacoes_bp.route("/fatura/pdf", methods=["GET"])
@token_required
def gerar_fatura_pdf(current_user):
    qtd_itens = random.randint(5, 30)
    transacoes = gerar_transacoes_fake(qtd=qtd_itens)

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    p.setFont("Helvetica-Bold", 16)
    p.drawString(200, height - 50, "Fatura de Cartão - Simulação")


    y = height - 100
    p.setFont("Helvetica", 10)
    for t in transacoes:
        linha = f"{t['data']} | {t['descricao']} | {t['valor'] if t['valor'] else '-'} | {t['categoria'] or '-'}"
        p.drawString(50, y, linha)
        y -= 15
        if y < 50:
            p.showPage()
            p.setFont("Helvetica", 10)
            y = height - 50

    p.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="fatura_simulada.pdf",
        mimetype="application/pdf"
    )

# ----------------------
# Rota - Gerar CSV
# ----------------------
@transacoes_bp.route("/fatura/csv", methods=["GET"])
@token_required
def gerar_fatura_csv(current_user):
    qtd_itens = random.randint(5, 30)
    transacoes = gerar_transacoes_fake(qtd=qtd_itens)

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=["data", "descricao", "valor", "categoria"])
    writer.writeheader()
    writer.writerows(transacoes)

    buffer.seek(0)
    return send_file(
        io.BytesIO(buffer.getvalue().encode("utf-8")),
        as_attachment=True,
        download_name="fatura_simulada.csv",
        mimetype="text/csv"
    )
