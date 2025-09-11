import io
import csv
from datetime import datetime
import pandas as pd
from sqlalchemy import and_, func
from models import session, Transacao
from utils.categorias import categorizar
from utils.faturas import gerar_transacoes_fake
from utils.validators import padronizar_categoria, validar_transacao
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def processar_csv(current_user, file):
    df = pd.read_csv(file)
    required_columns = ['data', 'descricao', 'valor']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Colunas obrigatórias faltando: {', '.join(missing_cols)}")

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
        raise ValueError(erros)

    session.commit()
    return {"message": "CSV processado com sucesso!"}


def processar_pdf(current_user, file):
    import pdfplumber
    transacoes = []

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
                data, descricao, valor_str = parts[0], parts[1], parts[2].strip() if parts[2].strip() != '-' else "0.0"
                categoria = parts[3] if len(parts) > 3 and parts[3] != '-' else None
                transacoes.append({"data": data, "descricao": descricao, "valor": valor_str, "categoria": categoria})

    erros = []
    transacoes_validas = []

    for i, t in enumerate(transacoes):
        try:
            data, descricao, valor, categoria = validar_transacao(t['data'], t['descricao'], t['valor'], t.get('categoria'))
            transacoes_validas.append({"data": data, "descricao": descricao, "valor": valor, "categoria": categoria})
        except Exception as e:
            erros.append(f"Linha {i+1}: {str(e)}")

    if erros:
        raise ValueError(erros)

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
    return {"message": "PDF processado com sucesso!", "transacoes_processadas": len(transacoes_validas)}


def listar_transacoes(current_user, filtros={}):
    query = session.query(Transacao).filter_by(user_id=current_user.id)
    filtro_list = []

    if categoria := filtros.get("categoria"):
        categorias = [c.strip().lower() for c in categoria.split(",") if c.strip()]
        if categorias:
            filtro_list.append(func.lower(Transacao.categoria).in_(categorias))

    if data_inicio := filtros.get("data_inicio"):
        dt_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
        filtro_list.append(Transacao.data >= dt_inicio)

    if data_fim := filtros.get("data_fim"):
        dt_fim = datetime.strptime(data_fim, '%Y-%m-%d')
        filtro_list.append(Transacao.data <= dt_fim)

    if valor_min := filtros.get("valor_min"):
        filtro_list.append(Transacao.valor >= float(valor_min))

    if valor_max := filtros.get("valor_max"):
        filtro_list.append(Transacao.valor <= float(valor_max))

    if busca := filtros.get("busca"):
        filtro_list.append(Transacao.descricao.ilike(f"%{busca}%"))

    if filtro_list:
        query = query.filter(and_(*filtro_list))

    return query.all()


def listar_categorias(current_user):
    categorias = session.query(func.lower(Transacao.categoria)).filter_by(user_id=current_user.id).distinct().all()
    return [c[0] for c in categorias if c[0]]


def criar_transacao(current_user, data):
    data_val, descricao, valor, categoria = validar_transacao(data['data'], data['descricao'], data['valor'], data.get('categoria'))
    categoria = padronizar_categoria(categoria)
    nova_transacao = Transacao(data=data_val, descricao=descricao, valor=valor, categoria=categoria, user_id=current_user.id)
    session.add(nova_transacao)
    session.commit()
    return nova_transacao


def editar_transacao(current_user, transacao_id, data):
    transacao = session.query(Transacao).filter_by(id=transacao_id, user_id=current_user.id).first()
    if not transacao:
        return None
    if 'data' in data:
        transacao.data = datetime.strptime(data['data'], '%Y-%m-%d')
    if 'valor' in data:
        transacao.valor = float(data['valor'])
    transacao.descricao = data.get('descricao', transacao.descricao)
    transacao.categoria = data.get('categoria', transacao.categoria)
    session.commit()
    return transacao


def deletar_transacao(current_user, transacao_id):
    transacao = session.query(Transacao).filter_by(id=transacao_id, user_id=current_user.id).first()
    if not transacao:
        return None
    session.delete(transacao)
    session.commit()
    return transacao


def gerar_fatura_pdf(qtd_itens=10):
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
    return buffer


def gerar_fatura_csv(qtd_itens=10):
    transacoes = gerar_transacoes_fake(qtd=qtd_itens)
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=["data", "descricao", "valor", "categoria"])
    writer.writeheader()
    writer.writerows(transacoes)
    buffer.seek(0)
    return io.BytesIO(buffer.getvalue().encode("utf-8"))
