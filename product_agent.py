from database import fetch_products
from utils import calcular_utilidade

def handle_request(data_structured):
    produtos = fetch_products()
    
    # Filtro por inovação e preço
    produtos_filtrados = [p for p in produtos if p["inovador"]]
    if data_structured["preco_maximo"]:
        produtos_filtrados = [p for p in produtos_filtrados if p["preco"] <= data_structured["preco_maximo"]]

    # Cálculo da utilidade
    for p in produtos_filtrados:
        p["utilidade"] = calcular_utilidade(p["inovacao"], p["preco"], len(produtos_filtrados))

    # Ordena por utilidade
    produtos_ordenados = sorted(produtos_filtrados, key=lambda x: x["utilidade"], reverse=True)
    return produtos_ordenados[:10]
