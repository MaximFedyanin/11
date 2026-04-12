#!/usr/bin/env python3
"""Массовое добавление слов из файла"""

import sqlite3
import csv

DB_PATH = '/sdcard/english_learning_app/database/words.db'

def import_from_csv(filepath):
    """Импорт слов из CSV: word_en,translation,level,topic,frequency"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    count = 0
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader, None)  # пропустить заголовок
        
        for row in reader:
            if len(row) >= 4:
                word_en, translation, level, topic = row[:4]
                frequency = int(row[4]) if len(row) > 4 else 0
                
                cursor.execute('''
                INSERT OR IGNORE INTO words 
                (word_en, translation, level, topic, frequency)
                VALUES (?, ?, ?, ?, ?)
                ''', (word_en, translation, level, topic, frequency))
                
                if cursor.lastrowid:
                    count += 1
    
    conn.commit()
    conn.close()
    print(f"✅ Импортировано {count} новых слов")

if __name__ == '__main__':
    # Пример: создаём тестовый CSV
    import os
    csv_path = '/sdcard/english_learning_app/data/words_sample.csv'
    
    if not os.path.exists(csv_path):
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("word_en,translation,level,topic,frequency\n")
            f.write("water,вода,A1,food,100\n")
            f.write("house,дом;жилище,A1,objects,98\n")
            f.write("beautiful,красивый;прекрасный,A2,emotions,85\n")
            f.write("technology,технология;техника,B1,tech,80\n")
            f.write("environment,окружающая среда;экология,B2,science,75\n")
        print(f"📝 Создан тестовый файл: {csv_path}")
    
    import_from_csv(csv_path)
