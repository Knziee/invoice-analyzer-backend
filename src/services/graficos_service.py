from sqlalchemy import func, extract, and_
from datetime import datetime
from models import session, Transacao

def gastos_por_categoria_service(current_user, categoria=None, data_inicio=None, data_fim=None):
    filtros = [Transacao.user_id == current_user.id]

    if categoria:
        filtros.append(func.lower(Transacao.categoria) == categoria.lower())

    if data_inicio:
        dt_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
        filtros.append(Transacao.data >= dt_inicio)

    if data_fim:
        dt_fim = datetime.strptime(data_fim, '%Y-%m-%d')
        filtros.append(Transacao.data <= dt_fim)

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
    return [
        {
            "categoria": r.categoria,
            "valor": float(r.valor_total),
            "percentual": round(float(r.valor_total)/total*100, 2) if total > 0 else 0
        }
        for r in resultado
    ]


def gastos_gerais_service(current_user, categoria=None, data_inicio=None, data_fim=None):
    filtros = [Transacao.user_id == current_user.id]

    if categoria:
        filtros.append(func.lower(Transacao.categoria) == categoria.lower())

    if data_inicio:
        dt_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
        filtros.append(Transacao.data >= dt_inicio)

    if data_fim:
        dt_fim = datetime.strptime(data_fim, '%Y-%m-%d')
        filtros.append(Transacao.data <= dt_fim)

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

    return {
        "meses": [{"mes": mes_nome[int(m.mes)], "valor": float(m.valor_total)} for m in meses],
        "soma_total": float(total)
    }


def insights_service(current_user, data_inicio=None, data_fim=None):
    filtros = [Transacao.user_id == current_user.id]

    if data_inicio:
        dt_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
        filtros.append(Transacao.data >= dt_inicio)

    if data_fim:
        dt_fim = datetime.strptime(data_fim, '%Y-%m-%d')
        filtros.append(Transacao.data <= dt_fim)

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
        session.query(func.avg(Transacao.valor).label('media'))
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

    return {
        "maior_categoria": maior_categoria.categoria if maior_categoria else None,
        "maior_categoria_valor": float(maior_categoria.valor_total) if maior_categoria else 0,
        "media_semanal": float(media_semanal) if media_semanal else 0,
        "maior_gasto": {"descricao": maior_gasto.descricao, "valor": float(maior_gasto.valor) if maior_gasto else 0} if maior_gasto else None,
        "menor_gasto": {"descricao": menor_gasto.descricao, "valor": float(menor_gasto.valor) if menor_gasto else 0} if menor_gasto else None,
        "dia_maior_gasto_media": int(dia_mes_media.dia_mes) if dia_mes_media else None
    }
