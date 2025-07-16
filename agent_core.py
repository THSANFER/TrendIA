# agent_core.py
import google.generativeai as genai
import datetime
import json
import os

# --- CONFIGURAÇÃO DA API ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyDP98kkMB5QQgf_xg5AGcPKjhYAS7srnUg")

INNOVATION_KEYWORDS = ['smart', 'inteligente', 'interativo', 'customizado', 'personalizado', '3d', 'led', 'tech', 'digital', 'inovador', 'diferente', 'moderno', 'sustentável', 'conectado']

def configure_llm():
    """Configura e retorna o modelo de IA."""
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        return model
    except Exception as e:
        print(f"Erro ao configurar a API do Google: {e}")
        return None

def _generate_ideas_from_llm(model, user_prompt):
    """Função interna para chamar a API e obter a lista bruta de ideias."""
    print(f"Gerando ideias de produtos em tempo real para: '{user_prompt}'...")
    prompt = f"""
    Aja como um especialista em tendências de produtos.
    Gere uma lista de 12 ideias de produtos inovadores baseados na busca: "{user_prompt}".

    Para cada produto, retorne um objeto JSON com: "product_name", "description" e "estimated_price_brl".
    Retorne APENAS uma lista de objetos JSON.
    """
    try:
        response = model.generate_content(prompt)
        json_response_text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(json_response_text)
    except Exception as e:
        print(f"Erro ao gerar ou processar ideias do LLM: {e}")
        return []

def _calculate_innovation_score(product_idea):
    """Calcula um score de inovação a partir do nome e descrição."""
    score = 0
    text_to_analyze = (product_idea.get('product_name', '') + ' ' + product_idea.get('description', '')).lower()
    for keyword in INNOVATION_KEYWORDS:
        if keyword in text_to_analyze:
            score += 1
    return score

def _calculate_utility_score(product, min_price, max_price, min_innovation, max_innovation, weights):
    """Calcula o score final de utilidade com base nos pesos."""
    price_range = max_price - min_price
    norm_price = (max_price - product['price_brl']) / price_range if price_range > 0 else 1.0
    innovation_range = max_innovation - min_innovation
    norm_innovation = (product['innovation_score'] - min_innovation) / innovation_range if innovation_range > 0 else 1.0
    return (norm_innovation * weights['w1']) + (norm_price * weights['w2'])

def generate_and_rank_products(user_prompt, weights):
    """
    Função principal: Gera, formata, analisa e classifica os produtos.
    """
    model = configure_llm()
    if not model: return []

    # 1. Geração
    product_ideas = _generate_ideas_from_llm(model, user_prompt)
    if not product_ideas: return []

    # 2. Formatação e Análise Inicial
    formatted_products = []
    for idea in product_ideas:
        if not all(k in idea for k in ['product_name', 'estimated_price_brl']): continue
        
        google_search_link = f"https://www.google.com/search?tbm=shop&q={idea.get('product_name').replace(' ', '+')}"
        product = {
            'product_url': google_search_link,
            'title': idea.get('product_name'),
            'description': idea.get('description', ''),
            'price_brl': float(idea.get('estimated_price_brl', 0.0)),
            'image_url': f"https://via.placeholder.com/300x300.png?text={idea.get('product_name').replace(' ', '+')}",
            'source': 'Gerado por IA (Real-time)',
            'innovation_score': _calculate_innovation_score(idea)
        }
        formatted_products.append(product)
    
    if not formatted_products: return []

    # 3. Classificação (Ranking)
    prices = [p['price_brl'] for p in formatted_products if p['price_brl'] > 0]
    innovations = [p['innovation_score'] for p in formatted_products]
    if not prices: return formatted_products

    min_price, max_price = min(prices), max(prices)
    min_innovation, max_innovation = min(innovations), max(innovations)

    for p in formatted_products:
        p['utility_score'] = _calculate_utility_score(p, min_price, max_price, min_innovation, max_innovation, weights)

    return sorted(formatted_products, key=lambda p: p.get('utility_score', 0), reverse=True)
