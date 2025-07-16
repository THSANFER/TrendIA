# main_llm_collector.py
import google.generativeai as genai
import datetime
import json
import database
import time
import os

# --- CONFIGURAÇÃO CENTRAL ---

# Cole sua API Key do Google AI Studio aqui. 
# É mais seguro usar variáveis de ambiente: GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_API_KEY = "AIzaSyCr77EwSHserX4vg0SOdHg2SvbCQbzCDZk"

# Define os tópicos de busca para o LLM
SEARCH_QUERIES = [
    "presentes criativos para millennials",
    "lembrancinhas de casamento personalizadas e modernas",
    "decoração de festa infantil com tema de espaço",
    "brindes corporativos de tecnologia e sustentáveis"
]

def configure_llm():
    """Configura a API do Google AI."""
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        return model
    except Exception as e:
        print(f"Erro ao configurar a API do Google: {e}")
        return None

def generate_product_ideas(model, query):
    """Envia um prompt para o LLM e pede para ele gerar uma lista de produtos."""
    print(f"Gerando ideias de produtos para: '{query}'...")
    
    prompt = f"""
    Aja como um especialista em tendências de produtos e e-commerce.
    Sua tarefa é gerar uma lista de 5 ideias de produtos inovadores e interessantes baseados na busca: "{query}".

    Para cada produto, forneça as seguintes informações em formato JSON, dentro de uma lista JSON:
    - "product_name": O nome do produto.
    - "description": Uma descrição curta, criativa e atrativa (máximo 2 frases).
    - "estimated_price_brl": Uma estimativa de preço de venda em Reais (BRL), apenas o número (ex: 79.90).
    - "target_audience": O público-alvo principal.
    - "innovation_factor": Um breve motivo pelo qual este produto é considerado inovador.

    Exemplo de formato de saída para um único produto:
    {{
      "product_name": "Luminária de Lua 3D Personalizada",
      "description": "Uma réplica da lua impressa em 3D que pode ser personalizada com uma foto e texto. Perfeita para criar um ambiente aconchegante e único.",
      "estimated_price_brl": 149.90,
      "target_audience": "Casais, amantes de astronomia, decoração de casa",
      "innovation_factor": "Combina impressão 3D, personalização e iluminação decorativa."
    }}

    Retorne APENAS a lista JSON, sem nenhum texto ou explicação adicional.
    """

    try:
        response = model.generate_content(prompt)
        json_response_text = response.text.strip().replace("```json", "").replace("```", "")
        product_ideas = json.loads(json_response_text)
        return product_ideas
    except (json.JSONDecodeError, Exception) as e:
        print(f"Erro ao processar a resposta do LLM: {e}")
        print(f"Resposta recebida: {response.text}")
        return None

def format_product_for_db(product_idea):
    """Formata a ideia de produto para o nosso padrão de banco de dados."""
    google_search_link = f"https://www.google.com/search?tbm=shop&q={product_idea.get('product_name', '').replace(' ', '+')}"
    
    return {
        'product_url': google_search_link,
        'title': product_idea.get('product_name', 'Produto Sem Nome'),
        'description': product_idea.get('description', ''),
        'price_brl': product_idea.get('estimated_price_brl', 0.0),
        'image_url': 'https://via.placeholder.com/300x300.png?text=Produto+Gerado',
        'source': 'Gerado por IA (Gemini)',
        'scraped_at': datetime.datetime.now().isoformat(),
        'innovation_score': None
    }

def main_collection_cycle():
    """Ciclo principal que itera sobre as queries, gera ideias e as salva."""
    print(f"\n[{datetime.datetime.now()}] +++ INICIANDO CICLO DE GERAÇÃO DE PRODUTOS COM IA +++")
    
    model = configure_llm()
    if not model:
        return

    all_collected_products = []
    for query in SEARCH_QUERIES:
        product_ideas = generate_product_ideas(model, query)
        if product_ideas:
            for idea in product_ideas:
                formatted_product = format_product_for_db(idea)
                all_collected_products.append(formatted_product)
            print(f"Sucesso! {len(product_ideas)} ideias geradas para '{query}'.")
        time.sleep(2)

    if all_collected_products:
        database.save_products(all_collected_products)
        print(f"\n+++ CICLO CONCLUÍDO. Total de {len(all_collected_products)} produtos gerados e salvos. +++")
    else:
        print("\n+++ CICLO CONCLUÍDO. Nenhum produto foi gerado. +++")

if __name__ == '__main__':
    if GOOGLE_API_KEY == "SUA_CHAVE_DE_API_DO_GOOGLE_AI_STUDIO":
        print("ERRO: Por favor, adicione sua API Key do Google AI Studio na variável GOOGLE_API_KEY.")
    else:
        main_collection_cycle()
