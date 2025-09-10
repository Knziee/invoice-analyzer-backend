import re

CATEGORIAS_KEYWORDS = {
    "padaria": ["padaria"],
    "farmacia": ["farmacia", "drogaria", "panvel", "raia", "pacheco"],
    "transporte": ["uber", "99app", "99 pop", "cabify"],
    "delivery": ["ifood", "ifd", "dudapasteis", "fnp", "rappi", "ubereats"],
    "mercado": ["rissul", "asun", "carrefour", "zaffari", "big", "angeloni"],
    "assinaturas": ["netflix", "spotify", "prime", "google one", "microsoft", "office", "hbo", "disney", "pier", "boo", "vivo", "ebn"],
    "compras": ["amazon", "shopee", "mercadolivre", "aliexpress", "magalu"],
    "carro": ["posto", "ipiranga", "br mania", "shell", "combustivel", "oficina", "pneu"],
    "games": ["steam", "riot", "epic", "playstation", "xbox", "nintendo"],
    "restaurante": ["churrascaria", "pizzaria", "mcdonalds", "bk", "burguer king", "subway", "restaurante"],
    "bebidas": ["bar", "pub", "bebidas", "adega", "heineken", "budweiser", "vinho", "whisky"],
    "saude": ["academia", "gympass", "consulta", "clinica", "hospital"],
    "educacao": ["curso", "udemy", "alura", "coursera", "faculdade", "universidade"],
}
# ----------------------
# Retorna a categoria com base nas palavras-chave.
# Caso nenhuma seja encontrada, retorna 'outros'.
# ----------------------
def categorizar(descricao: str) -> str:
    if not descricao:
        return "outros"
    
    desc_lower = descricao.lower()
    for categoria, palavras in CATEGORIAS_KEYWORDS.items():
        for palavra in palavras:
            if re.search(rf"\b{re.escape(palavra.lower())}\b", desc_lower):
                return categoria
    
    return "outros"
