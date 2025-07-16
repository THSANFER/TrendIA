# db_manager.py
import sqlite3
import json
import datetime
import os

DB_NAME = 'trendia.db'

def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados."""
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row # Permite acessar colunas por nome
    return conn

def setup_database():
    """Cria as tabelas do banco de dados se elas não existirem."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Tabela de produtos para evitar duplicatas e ter IDs estáveis
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_url TEXT UNIQUE,
            title TEXT,
            description TEXT,
            price_brl REAL,
            image_url TEXT,
            source TEXT,
            full_data TEXT -- Armazena o dicionário JSON completo do produto
        )
    ''')
    
    # Tabela de favoritos, ligando um usuário a um produto
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products (id),
            UNIQUE(username, product_id) -- Garante que um usuário não pode favoritar o mesmo produto duas vezes
        )
    ''')

    # Tabela para registrar o feedback de like/dislike para o sistema de aprendizado
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_profile TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            action TEXT NOT NULL, -- 'like' ou 'dislike'
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Banco de dados verificado/configurado com sucesso.")

def save_product_if_not_exists(product_dict):
    """Salva um produto no DB se ele não existir e retorna seu ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Usa a URL do produto como chave única para evitar duplicatas
    product_url = product_dict.get('product_url')
    cursor.execute("SELECT id FROM products WHERE product_url = ?", (product_url,))
    result = cursor.fetchone()
    
    if result:
        product_id = result['id']
    else:
        # Insere o novo produto
        cursor.execute('''
            INSERT INTO products (product_url, title, description, price_brl, image_url, source, full_data)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            product_url,
            product_dict.get('title'),
            product_dict.get('description'),
            product_dict.get('price_brl'),
            product_dict.get('image_url'),
            product_dict.get('source'),
            json.dumps(product_dict) # Salva o dicionário original como texto JSON
        ))
        product_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    return product_id

def add_favorite(username, product_id):
    """Adiciona um produto aos favoritos de um usuário, ignorando se já for favorito."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # A restrição UNIQUE(username, product_id) na tabela já previne duplicatas,
    # mas usamos 'INSERT OR IGNORE' para evitar erros.
    cursor.execute("INSERT OR IGNORE INTO favorites (username, product_id) VALUES (?, ?)", (username, product_id))
    
    conn.commit()
    conn.close()
    print(f"Tentativa de adicionar favorito para o usuário {username} concluída.")

def remove_favorite(username, product_id):
    """Remove um produto dos favoritos de um usuário."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM favorites WHERE username = ? AND product_id = ?", (username, product_id))
    conn.commit()
    conn.close()
    print(f"Favorito removido para o usuário {username}.")

def get_user_favorites(username):
    """Retorna uma lista de dicionários dos produtos favoritos de um usuário."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT p.full_data FROM products p
        JOIN favorites f ON p.id = f.product_id
        WHERE f.username = ?
    ''', (username,))
    
    favorites = [json.loads(row['full_data']) for row in cursor.fetchall()]
    conn.close()
    return favorites

def log_feedback(product_url, user_profile, action):
    """Registra uma ação de feedback (like/dislike) no banco de dados."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Primeiro, obtem o ID do produto com base na URL
    cursor.execute("SELECT id FROM products WHERE product_url = ?", (product_url,))
    result = cursor.fetchone()
    
    if not result:
        print(f"Feedback ignorado: Produto com URL {product_url} não encontrado no DB.")
        conn.close()
        return

    product_id = result['id']
    
    # Insere o novo registro de feedback
    cursor.execute(
        "INSERT INTO feedback (user_profile, product_id, action) VALUES (?, ?, ?)",
        (user_profile, product_id, action)
    )
    conn.commit()
    conn.close()
    print(f"Feedback '{action}' para o perfil '{user_profile}' registrado com sucesso.")

def get_all_feedback():
    """Busca todos os registros de feedback para o motor de aprendizado."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_profile, product_id, action FROM feedback")
    feedback_log = cursor.fetchall()
    conn.close()
    return feedback_log

def clear_feedback_log():
    """Limpa a tabela de feedback após o processamento pelo motor de aprendizado."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM feedback")
    conn.commit()
    conn.close()
    print("Tabela de feedback limpa.")