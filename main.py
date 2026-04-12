#!/usr/bin/env python3
"""
English Learning App - Main Entry Point
Оффлайн-приложение для изучения английских слов
"""

import os
import sys
import sqlite3
from datetime import datetime
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.config import Config
from kivy.core.window import Window

# Настройки для Android
Config.set('graphics', 'multisamples', '0')
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
Window.clearcolor = (0.95, 0.95, 0.95, 1)

# Пути к базе данных
DB_PATH = '/sdcard/english_learning_app/database/words.db'

# ============================================================================
# КЛАССЫ ЭКРАНОВ
# ============================================================================

class LoginScreen(Screen):
    """Экран авторизации"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 15
        
        # Заголовок
        title = Label(
	            text='[b]English Learning[/b]\n[v0.1]',
            markup=True,
            font_size='28sp',
            size_hint=(1, 0.15),
            halign='center',            valign='middle'
        )
        self.add_widget(title)
        
        # Поле ввода имени
        self.username_input = TextInput(
	            hint_text='Введите ваше имя',
            multiline=False,
            write_tab=False,
            size_hint=(1, 0.1),
            font_size='18sp'
        )
        self.add_widget(self.username_input)
        
        # Кнопка входа
        login_btn = Button(
	            text='НАЧАТЬ',
            size_hint=(1, 0.12),
            font_size='20sp',
            background_color=(0.2, 0.6, 1, 1),
            color=(1, 1, 1, 1)
        )
        login_btn.bind(on_press=self.on_login)
        self.add_widget(login_btn)
        
        # Информационная подпись
        info = Label(
	            text='Данные хранятся локально на устройстве',
            font_size='12sp',
            color=(0.5, 0.5, 0.5, 1),
            size_hint=(1, 0.08)
        )
        self.add_widget(info)
    
    def on_login(self, instance):
        username = self.username_input.text.strip()
        if username:
            # Сохраняем имя пользователя в менеджере
            self.manager.username = username
            self.manager.current = 'main'
        else:
            # Показать подсказку
            self.username_input.hint_text = 'Введите имя!'
            self.username_input.foreground_color = (1, 0, 0, 1)


class MainScreen(Screen):
    """Главный экран: выбор темы и режима"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 8
        self.selected_level = None
        self.current_topic = None
        
        # === Блок ввода темы ===
        topic_box = BoxLayout(orientation='vertical', size_hint=(1, 0.18), spacing=5)
        
        topic_label = Label(
	            text='Тема для изучения:',
            font_size='14sp',
            size_hint=(1, 0.3),
            halign='left'
        )
        topic_box.add_widget(topic_label)
        
        self.topic_input = TextInput(
	            hint_text='Например: еда, спорт, путешествия',
            multiline=False,
            write_tab=False,
            font_size='16sp',
            size_hint=(1, 0.7)
        )
        topic_box.add_widget(self.topic_input)
        self.add_widget(topic_box)
        
        # === Блок выбора уровня ===
        level_label = Label(
	            text='Уровень сложности:',
            font_size='14sp',
            size_hint=(1, 0.08),
            halign='left'
        )
        self.add_widget(level_label)
        
        levels_layout = BoxLayout(size_hint=(1, 0.12), spacing=5)
        for level in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']:
            btn = Button(
	                text=level,
                font_size='14sp',
                background_normal='',
                background_color=(0.8, 0.8, 0.8, 1)
            )
            btn.bind(on_press=lambda x, l=level: self.select_level(l, btn))
            setattr(self, f'btn_{level}', btn)
            levels_layout.add_widget(btn)
        self.add_widget(levels_layout)
                # === Кнопки режимов ===
        modes_layout = BoxLayout(size_hint=(1, 0.25), spacing=10, padding=5)
        
        self.new_words_btn = Button(
	            text='[b]New Words[/b]\nновые слова',
            markup=True,
            font_size='16sp',
            background_color=(0.3, 0.8, 0.3, 1),
            color=(1, 1, 1, 1)
        )
        self.new_words_btn.bind(on_press=self.start_new_words)
        modes_layout.add_widget(self.new_words_btn)
        
        self.repetition_btn = Button(
	            text='[b]Repetition[/b]\nповторение',
            markup=True,
            font_size='16sp',
            background_color=(0.8, 0.6, 0.2, 1),
            color=(1, 1, 1, 1),
            disabled=True  # Активируется, если есть прогресс
        )
        self.repetition_btn.bind(on_press=self.start_repetition)
        modes_layout.add_widget(self.repetition_btn)
        
        self.add_widget(modes_layout)
        
        # === Кнопка смены темы ===
        change_btn = Button(
	            text='🔄 Change topic',
            size_hint=(1, 0.08),
            font_size='14sp',
            background_color=(0.6, 0.6, 0.8, 1)
        )
        change_btn.bind(on_press=self.change_topic)
        self.add_widget(change_btn)
        
        # === Статус ===
        self.status_label = Label(
	            text='Введите тему и выберите уровень',
            font_size='13sp',
            color=(0.4, 0.4, 0.4, 1),
            size_hint=(1, 0.1)
        )
        self.add_widget(self.status_label)
    
    def select_level(self, level, btn):
        """Выбор уровня сложности"""
        # Сбросить выделение всех кнопок
        for lvl in ['A1','A2','B1','B2','C1','C2']:
            getattr(self, f'btn_{lvl}').background_color = (0.8, 0.8, 0.8, 1)        
        # Выделить выбранную
        btn.background_color = (0.2, 0.6, 1, 1)
        self.selected_level = level
        self.status_label.text = f'Уровень: {level} | Тема: {self.current_topic or "не выбрана"}'
    
    def start_new_words(self, instance):
        """Запуск режима новых слов"""
        topic = self.topic_input.text.strip()
        if not topic:
            self.status_label.text = '⚠️ Введите тему!'
            self.status_label.color = (1, 0, 0, 1)
            return
        
        if not self.selected_level:
            self.status_label.text = '⚠️ Выберите уровень!'
            self.status_label.color = (1, 0, 0, 1)
            return
        
        self.current_topic = topic
        self.manager.topic = topic
        self.manager.level = self.selected_level
        self.manager.mode = 'new_words'
        self.manager.current = 'training'
    
    def start_repetition(self, instance):
        """Запуск режима повторения"""
        self.manager.mode = 'repetition'
        self.manager.current = 'training'
    
    def change_topic(self, instance):
        """Сброс темы и возврат к выбору"""
        self.topic_input.text = ''
        self.selected_level = None
        self.current_topic = None
        for lvl in ['A1','A2','B1','B2','C1','C2']:
            getattr(self, f'btn_{lvl}').background_color = (0.8, 0.8, 0.8, 1)
        self.status_label.text = 'Введите тему и выберите уровень'
        self.status_label.color = (0.4, 0.4, 0.4, 1)


class TrainingScreen(Screen):
    """Экран тренировочной сессии"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 8
                # Переменные сессии
        self.current_word = None
        self.session_start = None
        self.timer_event = None
        self.elapsed_time = 0
        self.words_queue = []
        
        # === Верхняя панель: тема и таймер ===
        header = BoxLayout(size_hint=(1, 0.12), spacing=10)
        
        self.topic_label = Label(
	            text='Тема: -',
            font_size='14sp',
            halign='left',
            size_hint=(0.6, 1)
        )
        header.add_widget(self.topic_label)
        
        self.timer_label = Label(
	            text='⏱ 0.00с',
            font_size='16sp',
            color=(0.2, 0.6, 1, 1),
            halign='right',
            size_hint=(0.4, 1)
        )
        header.add_widget(self.timer_label)
        self.add_widget(header)
        
        # === Область слова ===
        self.word_display = Label(
	            text='[b]Слово[/b]',
            markup=True,
            font_size='42sp',
            size_hint=(1, 0.25),
            halign='center',
            valign='middle'
        )
        self.add_widget(self.word_display)
        
        # === Поле ввода ответа ===
        self.answer_input = TextInput(
	            hint_text='Введите перевод...',
            multiline=False,
            write_tab=False,
            font_size='20sp',
            size_hint=(1, 0.12)
        )
        self.answer_input.bind(on_text_validate=self.on_answer_enter)
        self.add_widget(self.answer_input)
                # === Кнопки действий ===
        buttons = BoxLayout(size_hint=(1, 0.15), spacing=8)
        
        check_btn = Button(
	            text='✅ Проверить',
            font_size='14sp',
            background_color=(0.2, 0.7, 0.2, 1),
            color=(1, 1, 1, 1)
        )
        check_btn.bind(on_press=self.check_answer)
        buttons.add_widget(check_btn)
        
        example_btn = Button(
	            text='📝 Example',
            font_size='14sp',
            background_color=(0.6, 0.6, 0.9, 1)
        )
        example_btn.bind(on_press=self.show_example)
        buttons.add_widget(example_btn)
        
        self.add_widget(buttons)
        
        # === Область примера (скрыта по умолчанию) ===
        self.example_box = BoxLayout(
	            orientation='vertical',
            size_hint=(1, 0.15),
            padding=8,
            spacing=3
        )
        self.example_box.opacity = 0
        self.example_box.disabled = True
        
        self.example_label = Label(
	            text='',
            font_size='15sp',
            halign='center',
            valign='middle'
        )
        self.example_box.add_widget(self.example_label)
        
        self.add_widget(self.example_box)
        
        # === Результат ответа ===
        self.result_label = Label(
	            text='',
            font_size='16sp',
            size_hint=(1, 0.08),
            halign='center'
        )
        self.add_widget(self.result_label)        
        # === Прогресс ===
        self.progress_label = Label(
	            text='Слово 0/0',
            font_size='13sp',
            color=(0.5, 0.5, 0.5, 1),
            size_hint=(1, 0.08)
        )
        self.add_widget(self.progress_label)
    
    def on_enter(self):
        """Вызывается при переходе на экран"""
        # Инициализация сессии
        topic = getattr(self.manager, 'topic', 'общая')
        level = getattr(self.manager, 'level', 'A1')
        mode = getattr(self.manager, 'mode', 'new_words')
        
        self.topic_label.text = f'📚 {topic} | {level} | {mode}'
        self.load_words(topic, level, mode)
    
    def on_leave(self):
        """Вызывается при уходе с экрана"""
        # Остановить таймер
        if self.timer_event:
            self.timer_event.cancel()
            self.timer_event = None
    
    def load_words(self, topic, level, mode):
        """Загрузка слов для сессии"""
        from smart_search import SimpleWordSearch
        
        search = SimpleWordSearch(DB_PATH)
        
        if mode == 'new_words':
            # Новые слова: только те, на которые ещё не было ответов
            self.words_queue = search.find_unanswered_words(
	                keywords=[topic], 
                level=level, 
                limit=20
            )
        else:
            # Повторение: слова с низким процентом правильных ответов
            self.words_queue = search.find_words_for_repetition(
	                username=self.manager.username,
                level=level,
                limit=20
            )
        
        search.close()
        if self.words_queue:
            self.show_next_word()
        else:
            self.word_display.text = '[i]Нет слов для этой темы[/i]'
            self.result_label.text = 'Добавьте больше слов в базу'
    
    def show_next_word(self):
        """Показать следующее слово"""
        if not self.words_queue:
            self.word_display.text = '[b]🎉 Сессия завершена![/b]'
            self.result_label.text = f'Пройдено слов: {getattr(self, "answered_count", 0)}'
            return
        
        self.current_word = self.words_queue.pop(0)
        # word = (id, word_en, translation, level, topic, freq, examples_json)
        
        self.word_display.text = f'[b]{self.current_word[1]}[/b]'
        self.answer_input.text = ''
        self.answer_input.focus = True
        self.example_box.opacity = 0
        self.example_box.disabled = True
        self.example_label.text = ''
        self.result_label.text = ''
        
        # Запуск таймера
        self.session_start = datetime.now()
        self.elapsed_time = 0
        if self.timer_event:
            self.timer_event.cancel()
        self.timer_event = Clock.schedule_interval(self.update_timer, 0.01)
        
        # Обновить прогресс
        total = getattr(self, 'total_words', 20)
        answered = getattr(self, 'answered_count', 0)
        self.progress_label.text = f'Слово {answered + 1}/{total}'
    
    def update_timer(self, dt):
        """Обновление таймера на экране"""
        if self.session_start:
            elapsed = (datetime.now() - self.session_start).total_seconds()
            self.timer_label.text = f'⏱ {elapsed:.2f}с'
            # Авто-таймаут через 10 секунд
            if elapsed >= 10.0 and not self.result_label.text:
                self.handle_timeout()
    
    def on_answer_enter(self, instance):
        """Обработка нажатия Enter в поле ответа"""
        self.check_answer(None)
    
    def check_answer(self, instance):
        """Проверка ответа пользователя"""
        if not self.current_word or self.result_label.text:
            return
        
        # Остановить таймер
        if self.timer_event:
            self.timer_event.cancel()
        
        user_answer = self.answer_input.text.strip().lower()
        correct_answer = self.current_word[2].lower()  # translation
        
        # Простая проверка (можно усложнить)
        is_correct = (
	            user_answer == correct_answer or
            user_answer in correct_answer or
            correct_answer in user_answer or
            any(user_answer in variant.lower() for variant in correct_answer.split(';'))
        )
        
        # Вычислить время ответа
        response_time = (datetime.now() - self.session_start).total_seconds()
        
        # Сохранить результат в БД
        self.save_result(is_correct, response_time)
        
        # Визуальная обратная связь
        if is_correct:
            self.result_label.text = '✅ Правильно!'
            self.result_label.color = (0, 0.7, 0, 1)
            self.word_display.color = (0, 0.8, 0, 1)
        else:
            self.result_label.text = f'❌ Правильно: {self.current_word[2]}'
            self.result_label.color = (0.9, 0.2, 0.2, 1)
            self.word_display.color = (0.9, 0.2, 0.2, 1)
        
        # Обновить счётчики
        self.answered_count = getattr(self, 'answered_count', 0) + 1
        
        # Показать следующее слово через 1.5 секунды
        Clock.schedule_once(lambda dt: self.show_next_word(), 1.5)
    
    def handle_timeout(self):
        """Обработка таймаута (10 секунд)"""
        if self.timer_event:
            self.timer_event.cancel()
        
        self.result_label.text = '⏰ Время вышло!'
        self.result_label.color = (0.9, 0.6, 0, 1)
        
        # Сохранить таймаут в БД        self.save_result(False, 10.0, result_type='timeout')
        
        self.answered_count = getattr(self, 'answered_count', 0) + 1
        Clock.schedule_once(lambda dt: self.show_next_word(), 1.5)
    
    def show_example(self, instance):
        """Показать пример использования слова"""
        if not self.current_word:
            return
        
        # Примеры хранятся в examples_json как строка "en1|ru1;en2|ru2"
        examples_json = self.current_word[6]
        if examples_json:
            examples = examples_json.split(';')
            if examples:
                en_sent, ru_sent = examples[0].split('|')
                self.example_label.text = f'[i]{en_sent}[/i]\n{ru_sent}'
        else:
            # Сгенерировать простой пример
            word = self.current_word[1]
            templates = [
	                f"I like {word}.",
                f"This is a {word}.",
                f"I have a {word}.",
            ]
            import random
            self.example_label.text = f"[i]{random.choice(templates)}[/i]"
        
        # Показать блок с примером
        self.example_box.opacity = 1
        self.example_box.disabled = False
    
    def save_result(self, is_correct, response_time, result_type=None):
        """Сохранение результата в базу данных"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Определить тип результата
            if result_type:
                result = result_type
            elif self.result_label.text and 'вышло' in self.result_label.text:
                result = 'timeout'
            else:
                result = 'correct' if is_correct else 'incorrect'
            
            # Получить номер попытки
            cursor.execute('''
            SELECT COUNT(*) FROM user_progress 
            WHERE word_id = ? AND user_id = ?            ''', (self.current_word[0], self.manager.username))
            attempt_num = cursor.fetchone()[0] + 1
            
            # Записать лог
            now = datetime.now()
            cursor.execute('''
            INSERT INTO user_progress 
            (user_id, word_id, session_date, session_time, result, response_time, attempt_number)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
	                self.manager.username,
                self.current_word[0],
                now.strftime('%d.%m.%Y'),
                now.strftime('%H:%M:%S'),
                result,
                round(response_time, 2),
                attempt_num
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Ошибка сохранения: {e}")


# ============================================================================
# ГЛАВНЫЙ КЛАСС ПРИЛОЖЕНИЯ
# ============================================================================

class EnglishLearningApp(App):
    """Основной класс приложения"""
    
    def build(self):
        self.title = 'English Learning'
        self.username = None
        self.topic = None
        self.level = None
        self.mode = None
        
        # Менеджер экранов
        sm = ScreenManager(transition=FadeTransition(duration=0.3))
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(TrainingScreen(name='training'))
        
        return sm
    
    def on_pause(self):
        """Обработка сворачивания приложения (Android)"""
        # Здесь можно сохранить состояние сессии
        return True
    
    def on_resume(self):
        """Обработка разворачивания приложения"""
        # Восстановить состояние при необходимости
        pass


# ============================================================================
# ТОЧКА ВХОДА
# ============================================================================

if __name__ == '__main__':
    # Проверка наличия БД
    if not os.path.exists(DB_PATH):
        print(f"⚠️ База данных не найдена: {DB_PATH}")
        print("Запустите сначала: python3 database/create_db.py")
        sys.exit(1)
    
    EnglishLearningApp().run()
