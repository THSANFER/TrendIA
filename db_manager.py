# db_manager.py
import sqlite3
import json
from datetime import datetime
import pytz
import os

DB_NAME = 'trendia.db'

def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados."""
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def setup_database():
    """Cria todas as tabelas do banco de dados se elas ainda não existirem."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_url TEXT UNIQUE,
            title TEXT,
            description TEXT,
            price_brl REAL,
            image_url TEXT,
            source TEXT,
            marketing_persona TEXT,
            full_data TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products (id),
            UNIQUE(username, product_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_profile TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Banco de dados verificado/configurado com sucesso.")

def save_product_if_not_exists(product_dict):
    """Salva um produto no DB se ele não existir e retorna seu ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    product_url = product_dict.get('product_url')
    cursor.execute("SELECT id FROM products WHERE product_url = ?", (product_url,))
    result = cursor.fetchone()
    if result:
        product_id = result['id']
    else:
        cursor.execute('''
            INSERT INTO products (product_url, title, description, price_brl, image_url, source, marketing_persona, full_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            product_url, product_dict.get('title'), product_dict.get('description'),
            product_dict.get('price_brl'), product_dict.get('image_url'),
            product_dict.get('source'), product_dict.get('marketing_persona'),
            json.dumps(product_dict)
        ))
        product_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return product_id

def load_products_as_dict():
    """Carrega todos os produtos do DB e retorna um dicionário com product_id como chave."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, full_data FROM products")
    products = {row['id']: json.loads(row['full_data']) for row in cursor.fetchall()}
    conn.close()
    return products

def add_favorite(username, product_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO favorites (username, product_id) VALUES (?, ?)", (username, product_id))
    conn.commit()
    conn.close()

def remove_favorite(username, product_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM favorites WHERE username = ? AND product_id = ?", (username, product_id))
    conn.commit()
    conn.close()

def get_user_favorites(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.full_data FROM products p
        JOIN favorites f ON p.id = f.product_id
        WHERE f.username = ? ORDER BY f.id DESC
    ''', (username,))
    favorites = [json.loads(row['full_data']) for row in cursor.fetchall()]
    conn.close()
    return favorites

def log_feedback(product_url, user_profile, action):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM products WHERE product_url = ?", (product_url,))
    result = cursor.fetchone()
    if not result:
        conn.close()
        return
    product_id = result['id']
    cursor.execute("INSERT INTO feedback (user_profile, product_id, action) VALUES (?, ?, ?)", (user_profile, product_id, action))
    conn.commit()
    conn.close()

def get_all_feedback():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_profile, product_id, action FROM feedback")
    feedback_log = cursor.fetchall()
    conn.close()
    return [dict(row) for row in feedback_log] # Retorna como lista de dicionários

def clear_feedback_log():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM feedback")
    conn.commit()
    conn.close()

def save_search_prompt(prompt):
    conn = get_db_connection()
    cursor = conn.cursor()
    fuso_horario_brasil = pytz.timezone('America/Sao_Paulo')
    agora_no_brasil = datetime.now(fuso_horario_brasil)
    timestamp_str = agora_no_brasil.isoformat()
    cursor.execute("INSERT INTO search_history (prompt, timestamp) VALUES (?, ?)", (prompt, timestamp_str))
    conn.commit()
    conn.close()

def get_search_history(limit=25):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, prompt, timestamp FROM search_history ORDER BY timestamp DESC LIMIT ?", (limit,))
    history = cursor.fetchall()
    conn.close()
    return history

def get_all_prompts_as_text():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT prompt FROM search_history")
    all_text = ' '.join([row['prompt'] for row in cursor.fetchall()])
    conn.close()
    return all_text

def delete_search_item(item_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM search_history WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()

def clear_search_history():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM search_history")
    conn.commit()
    conn.close()
