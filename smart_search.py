#!/usr/bin/env python3
"""
Модуль интеллектуального поиска слов по теме
Упрощённая версия без ML-моделей (использует rapidfuzz/difflib)
"""

import sqlite3
from rapidfuzz import fuzz, process

class SimpleWordSearch:
    """Поиск слов по теме с оценкой релевантности"""
    
    def __init__(self, db_path):
        self.db_path = db_path
    
    def _get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def find_by_topic(self, keywords, level=None, limit=20, exclude_answered=None, username=None):
        """
        Найти слова по теме
        
        :param keywords: список ключевых слов ["еда", "кухня"]
        :param level: уровень "A1"-"C2" или None
        :param limit: максимальное число результатов
        :param exclude_answered: если True, исключить слова с ответами пользователя
        :param username: имя пользователя для фильтрации прогресса
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Базовый запрос
        query = 'SELECT id, word_en, translation, level, topic, frequency, examples_json FROM words WHERE 1=1'
        params = []
        
        # Фильтр по уровню
        if level:
            query += ' AND level = ?'
            params.append(level)
        
        # Исключить отвеченные слова
        if exclude_answered and username:
            query += '''
            AND id NOT IN (
                    SELECT word_id FROM user_progress WHERE user_id = ?
            )
            '''
            params.append(username)
        
        cursor.execute(query, params)
        all_words = cursor.fetchall()
        conn.close()
        
        if not keywords:
            return all_words[:limit]
        
        # Оценка релевантности
        scored = []
        for word in all_words:
            word_id, word_en, translation, lvl, topic, freq, examples = word
            score = 0
            
            for kw in keywords:
                kw_lower = kw.lower()
                
                # Совпадение с темой
                if topic:
                    ratio = fuzz.ratio(kw_lower, topic.lower())
                    if ratio > 50:
                        score += ratio * 0.3
                
                # Совпадение с переводом
                if translation and kw_lower in translation.lower():
                    score += 25
                
                # Частичное совпадение с английским словом
                if fuzz.partial_ratio(kw_lower, word_en.lower()) > 60:
                    score += 15
                
                # Бонус за частотность
                score += min(freq, 50) * 0.1
            
            if score > 0:
                scored.append((score, word))
        
        # Сортировка и возврат топ-результатов
        scored.sort(reverse=True, key=lambda x: x[0])
        return [word for score, word in scored[:limit]]
    
    def find_unanswered_words(self, keywords, level=None, limit=20):
        """Найти новые слова (без ответов пользователя)"""
        return self.find_by_topic(
                keywords=keywords,
            level=level,
            limit=limit,
            exclude_answered=True,
            username=getattr(self, '_username', None)
        )
    
    def find_words_for_repetition(self, username, level=None, limit=20):
        """Найти слова для повторения (с низким % правильных ответов)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Найти слова с низким процентом правильных ответов
        cursor.execute('''
        SELECT w.id, w.word_en, w.translation, w.level, w.topic, w.frequency, w.examples_json,
               COUNT(up.id) as attempts,
               SUM(CASE WHEN up.result = 'correct' THEN 1 ELSE 0 END) as correct_count
        FROM words w
        LEFT JOIN user_progress up ON w.id = up.word_id AND up.user_id = ?
        WHERE w.level = ? OR ? IS NULL
        GROUP BY w.id
        HAVING attempts > 0
        ORDER BY 
            CASE WHEN attempts > 0 THEN correct_count * 1.0 / attempts ELSE 0 END ASC,
            frequency DESC
        LIMIT ?
        ''', (username, level, level, limit))
        
        results = cursor.fetchall()
        conn.close()
        return results
    
    def set_username(self, username):
        """Установить имя пользователя для фильтрации"""
        self._username = username
    
    def close(self):
        """Закрыть соединения (если нужно)"""
        pass
