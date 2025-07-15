# learning_engine.py
import json
import os

FEEDBACK_FILE = 'feedback.json'
PROFILES_FILE = 'user_profiles.json'
PRODUCTS_FILE = 'products_history.json' # Aponta para o novo nome do arquivo
LEARNING_RATE = 0.05

def load_json_file(filepath, default_data={}):
    if not os.path.exists(filepath): return default_data
    try:
        with open(filepath, 'r', encoding='utf-8') as f: return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError): return default_data

def save_json_file(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def update_weights_from_feedback():
    feedback_log = load_json_file(FEEDBACK_FILE, default_data=[])
    user_profiles = load_json_file(PROFILES_FILE, default_data={
        "Empresário de Brindes": {"w1_innovation": 0.5, "w2_price": 0.5},
        "Loja de Presentes para Festas": {"w1_innovation": 0.5, "w2_price": 0.5},
        "Consumidor Final": {"w1_innovation": 0.5, "w2_price": 0.5}
    })
    all_products = load_json_file(PRODUCTS_FILE)
    
    if not feedback_log or not all_products:
        print("Aprendizado adiado: sem feedbacks ou histórico de produtos.")
        return

    # Para evitar importar o agent_core, duplicamos a função de score aqui.
    INNOVATION_KEYWORDS = ['smart', 'inteligente', 'interativo', 'customizado', 'personalizado', '3d', 'led', 'tech', 'digital', 'inovador', 'diferente', 'moderno', 'sustentável', 'conectado']
    def calculate_innovation_score(product):
        score = 0
        text_to_analyze = (product.get('title', '') + ' ' + product.get('description', '')).lower()
        for keyword in INNOVATION_KEYWORDS:
            if keyword in text_to_analyze: score += 1
        return score

    for feedback in feedback_log:
        user_profile, product_url, action = feedback.get('user_id'), feedback.get('product_url'), feedback.get('action')
        if user_profile not in user_profiles or product_url not in all_products: continue

        product = all_products[product_url]
        has_high_innovation = calculate_innovation_score(product) > 0
        adjustment = LEARNING_RATE if action == 'like' else -LEARNING_RATE
        
        current_weights = user_profiles[user_profile]
        if has_high_innovation: current_weights['w1_innovation'] += adjustment
        else: current_weights['w2_price'] += adjustment

        current_weights['w1_innovation'] = max(0.01, min(0.99, current_weights['w1_innovation']))
        current_weights['w2_price'] = max(0.01, min(0.99, current_weights['w2_price']))
        total_weight = current_weights['w1_innovation'] + current_weights['w2_price']
        current_weights['w1_innovation'] /= total_weight
        current_weights['w2_price'] /= total_weight
        user_profiles[user_profile] = current_weights

    save_json_file(PROFILES_FILE, user_profiles)
    save_json_file(FEEDBACK_FILE, [])
    print("Pesos dos perfis atualizados com sucesso e log de feedback limpo.")

def get_user_weights(user_profile):
    user_profiles = load_json_file(PROFILES_FILE, default_data={
        "Empresário de Brindes": {"w1_innovation": 0.5, "w2_price": 0.5},
        "Loja de Presentes para Festas": {"w1_innovation": 0.5, "w2_price": 0.5},
        "Consumidor Final": {"w1_innovation": 0.5, "w2_price": 0.5}
    })
    profile_data = user_profiles.get(user_profile, {"w1_innovation": 0.5, "w2_price": 0.5})
    return {"w1": profile_data['w1_innovation'], "w2": profile_data['w2_price']}
