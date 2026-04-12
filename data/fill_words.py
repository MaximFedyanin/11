#!/usr/bin/env python3
import sqlite3

DB_PATH = '/sdcard/english_learning_app/database/words.db'

def add_word(word_en, translation, level, topic, frequency=0, examples=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
        INSERT OR IGNORE INTO words (word_en, translation, level, topic, frequency)
        VALUES (?, ?, ?, ?, ?)
        ''', (word_en, translation, level, topic, frequency))
        
        if cursor.lastrowid and examples:
            word_id = cursor.lastrowid
            for en_sent, ru_sent in examples:
                cursor.execute('''
                INSERT INTO examples (word_id, sentence_en, sentence_ru)
                VALUES (?, ?, ?)
                ''', (word_id, en_sent, ru_sent))
        
        conn.commit()
    except Exception as e:
        print(f"Ошибка при добавлении {word_en}: {e}")
    finally:
        conn.close()

# Базовый набор слов для теста
test_words = [
    ("apple", "яблоко", "A1", "food", 100, [
        ("I eat an apple every day.", "Я ем яблоко каждый день."),
        ("This apple is red and sweet.", "Это яблоко красное и сладкое.")
    ]),
    ("book", "книга", "A1", "objects", 95, [
        ("I read a book before sleep.", "Я читаю книгу перед сном."),
        ("This book is very interesting.", "Эта книга очень интересная.")
    ]),
    ("computer", "компьютер", "A2", "technology", 90, [
        ("I work on my computer.", "Я работаю на своём компьютере."),
        ("The computer is fast.", "Компьютер быстрый.")
    ]),
    ("run", "бежать", "A1", "actions", 88, [
        ("I run in the park every morning.", "Я бегаю в парке каждое утро."),
        ("She runs very fast.", "Она бегает очень быстро.")
    ]),
    ("happy", "счастливый", "A1", "emotions", 85, [
        ("I am happy today.", "Я счастлив сегодня."),
        ("She has a happy smile.", "У неё счастливая улыбка.")
    ]),
]

if __name__ == '__main__':
    for word_data in test_words:
        add_word(*word_data)
    print(f"✅ Добавлено {len(test_words)} тестовых слов")
