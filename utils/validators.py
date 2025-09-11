from datetime import datetime
from utils.categorias import categorizar
import pandas as pd

def validar_transacao(data, descricao, valor, categoria=None):
    try:
        data = datetime.strptime(str(data), '%Y-%m-%d')
    except ValueError:
        raise ValueError("Data inválida, use YYYY-MM-DD")

    if valor is not None and not pd.isna(valor):
        try:
            valor = float(valor)
        except ValueError:
            raise ValueError("Valor deve ser numérico")
    else:
        valor = None

    if categoria:
        categoria = categoria.strip().title()
    else:
        categoria = categorizar(descricao)

    return data, descricao.strip(), valor, categoria

import unicodedata

def padronizar_categoria(categoria):
    categoria = categoria.strip().lower()
    return ''.join(c for c in unicodedata.normalize('NFD', categoria)
                   if unicodedata.category(c) != 'Mn')

