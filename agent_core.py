# agent_core.py
import google.generativeai as genai
from googleapiclient.discovery import build
import json
import os
import time

# --- CONFIGURAÇÃO DAS APIs ---
GOOGLE_AI_API_KEY = os.getenv("GOOGLE_AI_API_KEY", "AIzaSyCaPrmpjk42-LX6ec5nDYnVOLTkK8XUFg0")

# Palavras-chave para o score de inovação
INNOVATION_KEYWORDS = ['smart', 'inteligente', 'interativo', 'personalizado', '3d', 'led', 'tech', 'digital', 'inovador', 'diferente', 'moderno', 'aumentada', 'sustentável', 'ecológico']

def configure_llm():
    """Configura e retorna o modelo de IA do Google (Gemini)."""
    try:
        if not GOOGLE_AI_API_KEY or "SUA_CHAVE" in GOOGLE_AI_API_KEY:
            print("ERRO: A chave da API do Google AI não está configurada.")
            return None
        genai.configure(api_key=GOOGLE_AI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        return model
    except Exception as e:
        print(f"Erro ao configurar a API do Google AI: {e}")
        return None

def calculate_innovation_score(product_dict):
    """Calcula um score de inovação simples baseado no título e descrição."""
    score = 0
    text_to_analyze = (product_dict.get('title', '') + ' ' + product_dict.get('description', '')).lower()
    for keyword in INNOVATION_KEYWORDS:
        if keyword in text_to_analyze:
            score += 1
    return score

def generate_and_rank_products(user_prompt, weights):
    """
    Gera ideias de produtos, calcula scores e retorna a lista.
    """
    model = configure_llm()
    if not model:
        return []

    print(f"Gerando e classificando ideias para: '{user_prompt}'...")
    
    prompt = f"""
    Aja como um especialista em tendências de produtos e e-commerce.
    Sua tarefa é gerar uma lista de 8 ideias de produtos inovadores e interessantes baseados na busca do usuário: "{user_prompt}".

    Para cada produto, forneça as seguintes informações em formato JSON, dentro de uma lista JSON:
    - "product_name": O nome do produto.
    - "description": Uma descrição curta e atrativa.
    - "estimated_price_brl": Uma estimativa de preço de venda em Reais (BRL), apenas o número.
    - "marketing_persona": Uma descrição curta (uma frase) do cliente ideal para este produto.

    Retorne APENAS a lista JSON. Não use aspas duplas dentro dos valores das strings. Use aspas simples se necessário.
    """

    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # <<< MUDANÇA PRINCIPAL AQUI >>>
        # Passo de "saneamento" para lidar com aspas duplas inválidas
        # Primeiro, extraímos o conteúdo JSON de forma segura
        start_index = response_text.find('[')
        end_index = response_text.rfind(']')
        
        if start_index == -1 or end_index == -1:
            raise ValueError("Resposta da IA não contém uma lista JSON válida (faltam colchetes).")
            
        json_response_text = response_text[start_index : end_index + 1]
        
        # Agora, tentamos corrigir o JSON se ele falhar
        try:
            product_ideas = json.loads(json_response_text)
        except json.JSONDecodeError as e:
            print(f"Erro inicial de JSON: {e}. Tentando corrigir aspas...")
            # Esta é uma correção "bruta" mas eficaz: substitui aspas duplas problemáticas por aspas simples
            # Funciona substituindo a combinação " : " (chave-valor) por um marcador temporário,
            # trocando todas as aspas restantes, e depois restaurando o marcador.
            corrected_text = json_response_text.replace('": "', '": "PLACEHOLDER_QUOTE')
            corrected_text = corrected_text.replace('"', "'")
            corrected_text = corrected_text.replace("': 'PLACEHOLDER_QUOTE", '": "')
            
            print("Tentando decodificar o JSON corrigido...")
            product_ideas = json.loads(corrected_text)

        # O resto da função continua como antes...
        formatted_products = []
        for idea in product_ideas:
            product_name = idea.get('product_name', 'Produto Sem Nome')
            image_url = f"https://via.placeholder.com/400x300.png?text={product_name.replace(' ', '+')}"
            google_search_link = f"https://www.google.com/search?tbm=shop&q={product_name.replace(' ', '+')}"
            
            product_data = {
                'product_url': google_search_link,
                'title': product_name,
                'description': idea.get('description', ''),
                'price_brl': float(idea.get('estimated_price_brl', 0.0)),
                'image_url': image_url,
                'source': 'Gerado por IA',
                'marketing_persona': idea.get('marketing_persona', 'Não definido')
            }
            product_data['innovation_score'] = calculate_innovation_score(product_data)
            formatted_products.append(product_data)
        
        print(f"--- SUCESSO: {len(formatted_products)} produtos gerados. ---")
        return formatted_products
        
    except Exception as e:
        print(f"Falha ao gerar ou processar produtos: {e}")
        if 'response' in locals():
            print(f"Resposta bruta recebida da IA que causou o erro: {response.text}")
        return []
