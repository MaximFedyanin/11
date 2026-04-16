#!/usr/bin/env python3
"""
Модуль интеллектуального поиска слов по теме
"""
import sqlite3
from rapidfuzz import fuzz, process

class SimpleWordSearch:
    def __init__(self, db_path):
        self.db_path = db_path
        self._username = "local_user" # Значение по умолчанию

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def find_by_topic(self, keywords, level=None, limit=20, exclude_answered=False, username=None):
        conn = self._get_connection()
        cursor = conn.cursor()
        uid = username or self._username
        
        query = 'SELECT id, word_en, translation, level, topic, frequency, examples_json FROM words WHERE 1=1'
        params = []
        
        if level:
            query += ' AND level = ?'
            params.append(level)
            
        if exclude_answered and uid:
            query += ''' AND id NOT IN (SELECT word_id FROM user_progress WHERE user_id = ?) '''
            params.append(uid)
            
        cursor.execute(query, params)
        all_words = cursor.fetchall()
        conn.close()
        
        if not keywords:
            return all_words[:limit]
            
        scored = []
        for word in all_words:
            word_id, word_en, translation, lvl, topic, freq, examples = word
            score = 0
            for kw in keywords:
                kw_lower = kw.lower()
                if topic and fuzz.ratio(kw_lower, topic.lower()) > 50:
                    score += 25
                if translation and kw_lower in translation.lower():
                    score += 30
                if fuzz.partial_ratio(kw_lower, word_en.lower()) > 60:
                    score += 15
                score += min(freq, 50) * 0.1
            if score > 0:
                scored.append((score, word))
                
        scored.sort(reverse=True, key=lambda x: x[0])
        return [word for score, word in scored[:limit]]

    def find_unanswered_words(self, keywords, level=None, limit=20):
        return self.find_by_topic(keywords=keywords, level=level, limit=limit, 
                                  exclude_answered=True, username=self._username)

    def find_words_for_repetition(self, username=None, level=None, limit=20):
        conn = self._get_connection()
        cursor = conn.cursor()
        uid = username or self._username
        
        cursor.execute('''
            SELECT w.id, w.word_en, w.translation, w.level, w.topic, w.frequency, w.examples_json,
                   COUNT(up.id) as attempts,
                   SUM(CASE WHEN up.result = 'correct' THEN 1 ELSE 0 END) as correct_count
            FROM words w
            LEFT JOIN user_progress up ON w.id = up.word_id AND up.user_id = ?
            WHERE (? IS NULL OR w.level = ?)
            GROUP BY w.id
            HAVING attempts > 0
            ORDER BY (correct_count * 1.0 / attempts) ASC, frequency DESC
            LIMIT ?
        ''', (uid, level, level, limit))
        
        results = cursor.fetchall()
        conn.close()
        return results

    def set_username(self, username):
        self._username = username

    def close(self):
        pass
