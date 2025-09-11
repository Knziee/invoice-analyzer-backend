import random
from datetime import datetime, timedelta

from utils.categorias import CATEGORIAS_KEYWORDS

def gerar_transacoes_fake(qtd=20):
    transacoes = []

    hoje = datetime.today()
    todas_categorias = list(CATEGORIAS_KEYWORDS.keys())
    ano = hoje.year - random.randint(0, 2)
    mes = random.randint(1, 12)

    if mes == 12:
        ultimo_dia = datetime(ano + 1, 1, 1) - timedelta(days=1)
    else:
        ultimo_dia = datetime(ano, mes + 1, 1) - timedelta(days=1)

    for _ in range(qtd):
        dia = random.randint(1, ultimo_dia.day)
        data = datetime(ano, mes, dia).strftime('%Y-%m-%d')

        categoria = random.choice(todas_categorias + [None])

        if categoria:
            descricao = random.choice(CATEGORIAS_KEYWORDS[categoria])
        else:
            descricao = f"Item {random.randint(1, 100)}"

        valor = round(random.uniform(5, 500), 2) if random.random() > 0.1 else None
        transacoes.append({
            "data": data,
            "descricao": descricao,
            "valor": valor,
            "categoria": categoria
        })

    return transacoes
