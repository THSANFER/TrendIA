# database.py
import json
import os
import datetime

DB_FILE = 'products_history.json' # Renomeado para refletir seu propósito
FEEDBACK_FILE = 'feedback.json'

def save_products(products_list):
    """Adiciona uma lista de produtos ao histórico JSON, evitando duplicatas."""
    print(f"Salvando/Atualizando {len(products_list)} produtos no histórico {DB_FILE}...")
    db_data = {}
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                db_data = json.load(f)
        except json.JSONDecodeError:
            db_data = {}

    new_products_dict = {p['product_url']: p for p in products_list}
    db_data.update(new_products_dict)

    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db_data, f, indent=4, ensure_ascii=False)

def log_feedback(product_url, user_id, action):
    """Registra uma ação de feedback em um arquivo JSON."""
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
