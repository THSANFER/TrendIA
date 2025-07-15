# database.py
import json
import os
import datetime

DB_FILE = 'products.json'
FEEDBACK_FILE = 'feedback.json'

def save_products(products_list):
    """
    Salva uma lista de produtos no arquivo JSON.
    Se o arquivo já existir, atualiza os dados, evitando duplicatas.
    """
    print(f"Salvando {len(products_list)} produtos em {DB_FILE}...")
    db_data = {}
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                db_data = json.load(f)
        except json.JSONDecodeError:
            print(f"Aviso: O arquivo {DB_FILE} estava corrompido e será recriado.")
            db_data = {}

    new_products_dict = {p['product_url']: p for p in products_list}
    db_data.update(new_products_dict)

    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db_data, f, indent=4, ensure_ascii=False)
    print("Banco de dados de produtos salvo com sucesso!")

def load_products():
    """
    Carrega todos os produtos do arquivo JSON. Retorna um dicionário.
    """
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

# --- NOVA FUNÇÃO PARA O MÓDULO 2 ---
def log_feedback(product_url, user_id, action):
    """
    Registra uma ação de feedback (ex: 'like', 'dislike') em um arquivo JSON.

    Args:
        product_url (str): A URL do produto que recebeu o feedback.
        user_id (str): O identificador do usuário que deu o feedback.
        action (str): A ação realizada ('like', 'dislike', 'click_link', etc.).
    """
    feedback_entry = {
        'timestamp': datetime.datetime.now().isoformat(),
        'user_id': user_id,
        'product_url': product_url,
        'action': action
    }
    
    all_feedback = []
    if os.path.exists(FEEDBACK_FILE):
        try:
            with open(FEEDBACK_FILE, 'r', encoding='utf-8') as f:
                all_feedback = json.load(f)
        except json.JSONDecodeError:
            all_feedback = []

    all_feedback.append(feedback_entry)

    with open(FEEDBACK_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_feedback, f, indent=4, ensure_ascii=False)