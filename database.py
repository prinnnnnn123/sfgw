import sqlite3
import hashlib
import os
from pathlib import Path

DB_FILE = 'users.db'

def get_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_configs (
            user_id INTEGER PRIMARY KEY,
            chat_id TEXT,
            name_prefix TEXT,
            delay INTEGER DEFAULT 5,
            cookies TEXT,
            messages TEXT,
            automation_running INTEGER DEFAULT 0,
            admin_e2ee_thread_id TEXT,
            admin_cookies TEXT,
            admin_chat_type TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        hashed_pw = hash_password(password)
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_pw))
        user_id = cursor.lastrowid
        
        cursor.execute('''
            INSERT INTO user_configs (user_id, chat_id, name_prefix, delay, cookies, messages)
            VALUES (?, '', '', 5, '', 'Hello!')
        ''', (user_id,))
        
        conn.commit()
        conn.close()
        return True, "Account created successfully!"
    except sqlite3.IntegrityError:
        return False, "Username already exists!"
    except Exception as e:
        return False, f"Error: {str(e)}"

def verify_user(username, password):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        hashed_pw = hash_password(password)
        cursor.execute('SELECT id FROM users WHERE username = ? AND password = ?', (username, hashed_pw))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return user['id']
        return None
    except Exception:
        return None

def get_username(user_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        return user['username'] if user else None
    except Exception:
        return None

def get_user_config(user_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM user_configs WHERE user_id = ?', (user_id,))
        config = cursor.fetchone()
        conn.close()
        
        if config:
            return {
                'chat_id': config['chat_id'],
                'name_prefix': config['name_prefix'],
                'delay': config['delay'],
                'cookies': config['cookies'],
                'messages': config['messages']
            }
        return None
    except Exception:
        return None

def update_user_config(user_id, chat_id, name_prefix, delay, cookies, messages):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE user_configs 
            SET chat_id = ?, name_prefix = ?, delay = ?, cookies = ?, messages = ?
            WHERE user_id = ?
        ''', (chat_id, name_prefix, delay, cookies, messages, user_id))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def get_automation_running(user_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT automation_running FROM user_configs WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        return bool(result['automation_running']) if result else False
    except Exception:
        return False

def set_automation_running(user_id, running):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE user_configs SET automation_running = ? WHERE user_id = ?', (1 if running else 0, user_id))
        conn.commit()
        conn.close()
    except Exception:
        pass

def get_admin_e2ee_thread_id(user_id, current_cookies):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT admin_e2ee_thread_id, admin_chat_type FROM user_configs WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result and result['admin_e2ee_thread_id']:
            return {
                'thread_id': result['admin_e2ee_thread_id'],
                'chat_type': result['admin_chat_type']
            }
        return None
    except Exception:
        return None

def set_admin_e2ee_thread_id(user_id, thread_id, cookies, chat_type):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE user_configs 
            SET admin_e2ee_thread_id = ?, admin_cookies = ?, admin_chat_type = ?
            WHERE user_id = ?
        ''', (thread_id, cookies, chat_type, user_id))
        conn.commit()
        conn.close()
    except Exception:
        pass

def clear_admin_e2ee_thread_id(user_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE user_configs SET admin_e2ee_thread_id = NULL WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
    except Exception:
        pass
