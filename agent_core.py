# agent_core.py
import spacy

# Carrega o modelo de linguagem do spaCy
# Usaremos um bloco try-except para dar uma mensagem de erro amigável se o modelo não for baixado
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Modelo 'en_core_web_sm' do spaCy não encontrado.")
    print("Por favor, execute: python -m spacy download en_core_web_sm")
    nlp = None

# Palavras-chave para identificar "inovação" nos produtos.
# Em um sistema real, essa lista seria muito maior e mais sofisticada.
INNOVATION_KEYWORDS = [
    'smart', 'intelligent', 'interactive', 'custom', 'personalized', 
    '3d', 'led', 'tech', 'digital'
]

def process_prompt(prompt_text):
    """
    Agente 1: Receptor/Processador de Prompt.
    Extrai os substantivos e adjetivos principais do prompt como termos de busca.
    """
    if not nlp:
        # Fallback para caso o spaCy não carregue
        return prompt_text.lower().split()
        
    doc = nlp(prompt_text.lower())
    search_terms = [
        token.lemma_ for token in doc 
        if token.pos_ in ['NOUN', 'PROPN', 'ADJ'] and not token.is_stop
    ]
    # Se não encontrar termos, usa o texto original como fallback
    return search_terms if search_terms else prompt_text.lower().split()

def calculate_innovation_score(product):
    """
    Agente 3 (Classificador): Calcula um score de inovação simples
    baseado na presença de palavras-chave no título.
    """
    score = 0
    title = product.get('title', '').lower()
    for keyword in INNOVATION_KEYWORDS:
        if keyword in title:
            score += 1
    return score

def calculate_utility_score(product, min_price, max_price, min_innovation, max_innovation, weights):
    """
    Agente 4 (Ranker): Implementa a Função de Utilidade U(P).
    """
    # Normalização do Preço (invertido: preço menor = score maior)
    # Evita divisão por zero se todos os preços forem iguais
    price_range = max_price - min_price
    if price_range > 0:
        norm_price = (max_price - product['price_gbp']) / price_range
    else:
        norm_price = 1.0

    # Normalização da Inovação
    innovation_range = max_innovation - min_innovation
    if innovation_range > 0:
        norm_innovation = (product['innovation_score'] - min_innovation) / innovation_range
    else:
        norm_innovation = 1.0

    # Fórmula de Utilidade U(P) = (Inovação * w1) + (Preço * w2)
    # Note que a "sobrecarga" (w3) é tratada ao limitar o número de resultados exibidos.
    utility = (norm_innovation * weights['w1']) + (norm_price * weights['w2'])
    
    return utility


def find_and_rank_products(prompt, all_products, weights, max_results=12):
    """
    Orquestrador principal do Módulo 3.
    """
    # 1. Agente 1: Processa o prompt para obter termos de busca
    search_terms = process_prompt(prompt)
    print(f"Termos de busca extraídos: {search_terms}")
    
    # 2. Agente 2: Faz a busca/filtro inicial
    filtered_products = [
        p for p in all_products
        if all(term in p['title'].lower() for term in search_terms)
    ]
    
    if not filtered_products:
        return []

    # 3. Agente 3: Calcula o score de inovação para cada produto filtrado
    for p in filtered_products:
        p['innovation_score'] = calculate_innovation_score(p)

    # 4. Agente 4: Prepara para o ranking
    prices = [p['price_gbp'] for p in filtered_products]
    innovations = [p['innovation_score'] for p in filtered_products]
    
    min_price, max_price = min(prices), max(prices)
    min_innovation, max_innovation = min(innovations), max(innovations)

    # 5. Agente 4: Calcula a utilidade para cada produto
    for p in filtered_products:
        p['utility_score'] = calculate_utility_score(
            p, min_price, max_price, min_innovation, max_innovation, weights
        )

    # 6. Agente 4: Ordena os produtos pelo score de utilidade (do maior para o menor)
    ranked_products = sorted(filtered_products, key=lambda p: p['utility_score'], reverse=True)
    
    # 7. Limita o resultado para evitar "Sobrecarga de Informação"
    return ranked_products[:max_results]