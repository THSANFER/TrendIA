# learning_engine.py
import json
import os

FEEDBACK_FILE = 'feedback.json'
PROFILES_FILE = 'user_profiles.json'
PRODUCTS_FILE = 'products.json'

LEARNING_RATE = 0.05  # Quão rápido os pesos se ajustam. Um valor pequeno torna o aprendizado mais estável.

def load_json_file(filepath, default_data={}):
    """Função auxiliar para carregar um arquivo JSON de forma segura."""
    if not os.path.exists(filepath):
        return default_data
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return default_data

def save_json_file(filepath, data):
    """Função auxiliar para salvar dados em um arquivo JSON."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def update_weights_from_feedback():
    """
    Função principal do motor de aprendizado.
    Analisa todos os feedbacks e ajusta os pesos dos perfis.
    """
    feedback_log = load_json_file(FEEDBACK_FILE, default_data=[])
    user_profiles = load_json_file(PROFILES_FILE)
    all_products = load_json_file(PRODUCTS_FILE)
    
    if not feedback_log or not user_profiles or not all_products:
        print("Aprendizado adiado: arquivos de feedback, perfis ou produtos não encontrados.")
        return

    print(f"Processando {len(feedback_log)} registros de feedback para ajustar os pesos...")

    for feedback in feedback_log:
        user_profile = feedback.get('user_id')
        product_url = feedback.get('product_url')
        action = feedback.get('action')

        if user_profile not in user_profiles or product_url not in all_products:
            continue

        product = all_products[product_url]
        # Usamos uma função do agent_core para consistência
        from agent_core import calculate_innovation_score
        product_innovation_score = calculate_innovation_score(product)

        # Simplificação: consideramos a inovação alta se tiver score > 0
        # Em um sistema real, poderíamos normalizar isso.
        has_high_innovation = product_innovation_score > 0
        
        # Lógica de Aprendizado por Reforço (Simplificada)
        # Se o usuário GOSTOU (like) de um produto inovador, aumentamos o peso da inovação (w1).
        # Se NÃO GOSTOU (dislike), diminuímos.
        
        current_weights = user_profiles[user_profile]
        
        adjustment = 0
        if action == 'like':
            adjustment = LEARNING_RATE
        elif action == 'dislike':
            adjustment = -LEARNING_RATE

        if has_high_innovation:
            current_weights['w1_innovation'] += adjustment
        else: # Se o produto não é inovador, o feedback provavelmente se refere ao preço/estilo.
              # Se ele gostou de um produto "comum", valoriza mais o preço (ou outros fatores).
            current_weights['w2_price'] += adjustment

        # Normalização: Garantir que os pesos fiquem entre 0 e 1 e que a soma seja 1.
        current_weights['w1_innovation'] = max(0.01, min(0.99, current_weights['w1_innovation']))
        current_weights['w2_price'] = max(0.01, min(0.99, current_weights['w2_price']))
        
        total_weight = current_weights['w1_innovation'] + current_weights['w2_price']
        current_weights['w1_innovation'] /= total_weight
        current_weights['w2_price'] /= total_weight

        user_profiles[user_profile] = current_weights

    # Salva os perfis atualizados
    save_json_file(PROFILES_FILE, user_profiles)
    
    # Limpa o log de feedback para não reprocessar os mesmos dados
    # Em um sistema de produção, você moveria os dados processados para outro lugar.
    # save_json_file(FEEDBACK_FILE, []) 
    # Por enquanto, vamos comentar a linha acima para poder testar várias vezes com os mesmos dados.
    
    print("Pesos dos perfis atualizados com sucesso.")
    return user_profiles

def get_user_weights(user_profile):
    """
    Carrega os pesos mais recentes para um perfil de usuário específico.
    """
    user_profiles = load_json_file(PROFILES_FILE)
    if user_profile in user_profiles:
        profile_data = user_profiles[user_profile]
        return {"w1": profile_data['w1_innovation'], "w2": profile_data['w2_price']}
    else:
        # Retorna pesos padrão se o perfil for novo ou não existir
        return {"w1": 0.5, "w2": 0.5}