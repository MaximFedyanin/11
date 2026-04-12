#!/usr/bin/env python3
import sqlite3
import os

DB_PATH = '/sdcard/english_learning_app/database/words.db'

def create_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Таблица слов
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS words (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word_en TEXT NOT NULL UNIQUE,
        translation TEXT,
        level TEXT CHECK(level IN ('A1','A2','B1','B2','C1','C2')),
        topic TEXT,
        frequency INTEGER DEFAULT 0,
        examples_json TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Таблица примеров предложений
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS examples (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word_id INTEGER,
        sentence_en TEXT NOT NULL,
        sentence_ru TEXT,
        source TEXT,
        FOREIGN KEY(word_id) REFERENCES words(id) ON DELETE CASCADE
    )
    ''')
    
    # Таблица прогресса пользователя
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        word_id INTEGER,
        session_date TEXT,
        session_time TEXT,
        result TEXT CHECK(result IN ('correct','incorrect','timeout','session_closed')),
        response_time REAL,
        attempt_number INTEGER DEFAULT 1,
        FOREIGN KEY(word_id) REFERENCES words(id) ON DELETE CASCADE
    )
    ''')
    
    # Индексы для ускорения поиска
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_words_topic ON words(topic)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_words_level ON words(level)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_progress_word ON user_progress(word_id)')
    
    conn.commit()
    conn.close()
    print(f"✅ База данных создана: {DB_PATH}")

if __name__ == '__main__':
    create_database()
