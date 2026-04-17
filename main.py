#!/usr/bin/env python3
"""English Learning App - Main Entry Point
Оффлайн-приложение для изучения английских слов"""
import os
import sqlite3
import shutil
import json
from datetime import datetime
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.config import Config
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout

Config.set('graphics', 'multisamples', '0')
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

# Цвета фона по умолчанию
DEFAULT_BG_COLOR = (0.95, 0.95, 0.95, 1)
COLOR_OPTIONS = {
    'light_blue': (0.80, 0.92, 0.98, 1),    # светло-голубой
    'light_pink': (0.98, 0.90, 0.92, 1),    # светло-розовый
    'light_green': (0.90, 0.98, 0.90, 1),   # светло-зелёный
    'light_yellow': (0.98, 0.98, 0.85, 1),  # светло-жёлтый
    'white': (1.0, 1.0, 1.0, 1)             # белый
}

# ============================================================================
# ЭКРАН ПРИВЕТСТВИЯ
# ============================================================================
class WelcomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Основной layout с FloatLayout для позиционирования кнопки фона
        self.main_layout = FloatLayout()
        
        # Вертикальный layout для контента
        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        self.greeting_label = Label(
            text='', 
            font_size='24sp', 
            bold=True, 
            size_hint=(1, 0.2), 
            halign='center',
            color=(0, 0, 0, 1)  # Чёрный текст
        )
        
        self.stats_label = Label(
            text='Загрузка статистики...', 
            font_size='16sp', 
            size_hint=(1, 0.15), 
            halign='center',
            color=(0, 0, 0, 1)  # Чёрный текст
        )
        
        # Layout для кнопок (уменьшен в 3 раза)
        btn_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.2), spacing=8)
        
        # Кнопка New Words (уменьшена в 3 раза)
        self.new_words_btn = self.create_rounded_button(
            text='[b]New Words[/b]\nновые слова',
            bg_color=(0.3, 0.8, 0.3, 1)
        )
        self.new_words_btn.bind(on_press=lambda x: self.manager.current('topic_select'))
        
        # Кнопка Repetition (уменьшена в 3 раза)
        self.repetition_btn = self.create_rounded_button(
            text='[b]Repetition[/b]\nповторение',
            bg_color=(0.8, 0.6, 0.2, 1)
        )
        self.repetition_btn.bind(on_press=self.start_repetition)
        
        # Кнопка Progress (уменьшена в 3 раза)
        self.progress_btn = self.create_rounded_button(
            text='[b]My Progress[/b]\nмой прогресс',
            bg_color=(0.5, 0.5, 0.8, 1)
        )
        self.progress_btn.bind(on_press=self.show_progress)
        
        btn_layout.add_widget(self.new_words_btn)
        btn_layout.add_widget(self.repetition_btn)
        btn_layout.add_widget(self.progress_btn)
        
        self.layout.add_widget(self.greeting_label)
        self.layout.add_widget(self.stats_label)
        self.layout.add_widget(btn_layout)
        
        # Кнопка выбора фона (🎨) в правом верхнем углу
        self.bg_color_btn = Button(
            text='🎨',
            size_hint=(None, None),
            size=(50, 50),
            pos_hint={'right': 1, 'top': 1},
            background_color=(1, 1, 1, 0.8),
            color=(0, 0, 0, 1)
        )
        self.bg_color_btn.bind(on_press=self.show_color_picker)
        
        self.main_layout.add_widget(self.layout)
        self.main_layout.add_widget(self.bg_color_btn)
        
        self.add_widget(self.main_layout)
    
    def create_rounded_button(self, text, bg_color):
        """Создаёт кнопку с закруглёнными углами (radius=15dp)"""
        btn = Button(
            text=text,
            markup=True,
            font_size='16sp',
            background_color=bg_color,
            color=(1, 1, 1, 1),
            size_hint=(1, None),
            height=45  # Уменьшенная высота (примерно в 3 раза)
        )
        
        # Добавляем закругление углов
        with btn.canvas.before:
            Color(0, 0, 0, 0.2)  # Цвет обводки
            RoundedRectangle(pos=btn.pos, size=btn.size, radius=[15, 15, 15, 15])
            Color(*bg_color)
            RoundedRectangle(pos=btn.pos, size=btn.size, radius=[15, 15, 15, 15])
        
        btn.bind(pos=self._update_rounded_rect, size=self._update_rounded_rect)
        return btn
    
    def _update_rounded_rect(self, instance, value):
        """Обновляет позицию и размер закруглённого прямоугольника"""
        if hasattr(instance, 'canvas') and len(instance.canvas.before) > 0:
            instance.canvas.before[0].pos = instance.pos
            instance.canvas.before[0].size = instance.size
            instance.canvas.before[2].pos = instance.pos
            instance.canvas.before[2].size = instance.size
    
    def show_color_picker(self, instance):
        """Показывает popup с выбором цвета фона"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text='Выберите цвет фона:', size_hint=(1, 0.3)))
        
        # Сетка с цветами
        colors_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.7), spacing=15, padding=10)
        
        color_names = ['light_blue', 'light_pink', 'light_green', 'light_yellow', 'white']
        color_display_names = ['🔵', '', '', '🟡', '⚪']
        
        for color_name, color_emoji in zip(color_names, color_display_names):
            color_value = COLOR_OPTIONS[color_name]
            
            # Создаём цветной квадратик
            color_btn = Button(
                text=color_emoji,
                size_hint=(1, 1),
                background_color=color_value,
                color=(0, 0, 0, 1) if color_name != 'white' else (0, 0, 0, 1)
            )
            
            # Добавляем закругление
            with color_btn.canvas.before:
                Color(0.7, 0.7, 0.7, 0.5)
                RoundedRectangle(pos=color_btn.pos, size=color_btn.size, radius=[10, 10, 10, 10])
                Color(*color_value)
                RoundedRectangle(pos=color_btn.pos, size=color_btn.size, radius=[10, 10, 10, 10])
            
            color_btn.bind(pos=lambda inst, val, btn=color_btn: self._update_color_btn(btn),
                          size=lambda inst, val, btn=color_btn: self._update_color_btn(btn))
            
            color_btn.bind(on_press=lambda x, name=color_name: self.set_background_color(name))
            colors_layout.add_widget(color_btn)
        
        content.add_widget(colors_layout)
        
        popup = Popup(
            title='Цвет фона',
            content=content,
            size_hint=(0.7, 0.3),
            auto_dismiss=True
        )
        popup.open()
    
    def _update_color_btn(self, instance):
        """Обновляет позицию закругления для цветных кнопок"""
        if hasattr(instance, 'canvas') and len(instance.canvas.before) > 0:
            instance.canvas.before[0].pos = instance.pos
            instance.canvas.before[0].size = instance.size
            instance.canvas.before[2].pos = instance.pos
            instance.canvas.before[2].size = instance.size
    
    def set_background_color(self, color_name):
        """Устанавливает цвет фона и сохраняет его"""
        color = COLOR_OPTIONS.get(color_name, DEFAULT_BG_COLOR)
        
        # Сохраняем выбор
        App.get_running_app().save_bg_color(color_name)
        
        # Применяем ко всем экранам
        App.get_running_app().apply_background_color(color)
    
    def on_enter(self):
        # Применяем сохранённый цвет фона
        App.get_running_app().apply_saved_background()
        self.update_greeting()
        self.update_stats()
    
    def update_greeting(self):
        hour = datetime.now().hour
        if 4 <= hour < 12:
            greeting = "Good morning!"
        elif 12 <= hour < 18:
            greeting = "Good day!"
        elif 18 <= hour < 22:
            greeting = "Good evening!"
        else:
            greeting = "Good night!"
        self.greeting_label.text = greeting
    
    def update_stats(self):
        try:
            db_path = App.get_running_app().db_path
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute("SELECT COUNT(DISTINCT word_id) FROM user_progress WHERE result='correct' AND user_id='local_user'")
            count = cur.fetchone()[0]
            self.stats_label.text = f"✅ Correctly answered: {count} words"
            conn.close()
        except Exception as e:
            self.stats_label.text = "Database not ready"
    
    def start_repetition(self):
        self.manager.mode = 'repetition'
        self.manager.current = 'training'
    
    def show_progress(self):
        content = Label(
            text='📊 Detailed statistics will appear here.\nTotal sessions: 0\nAccuracy: 0%\nLast activity: -',
            color=(0, 0, 0, 1)
        )
        popup = Popup(title='My Progress', content=content, size_hint=(0.8, 0.4))
        popup.open()


# ============================================================================
# ЭКРАН ВЫБОРА ТЕМЫ
# ============================================================================
class TopicSelectScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        layout.add_widget(Label(
            text='Enter topic keywords:', 
            font_size='18sp', 
            size_hint=(1, 0.1),
            color=(0, 0, 0, 1)
        ))
        
        self.topic_input = TextInput(
            hint_text='e.g., food, travel, business', 
            multiline=False,
            size_hint=(1, 0.15), 
            font_size='16sp'
        )
        layout.add_widget(self.topic_input)
        
        level_layout = BoxLayout(size_hint=(1, 0.1), spacing=5)
        self.selected_level = 'A1'
        self.level_buttons = {}
        
        for lvl in ['A1', 'A2', 'B1', 'B2']:
            btn = Button(
                text=lvl, 
                background_color=(0.2, 0.6, 1, 1) if lvl=='A1' else (0.7, 0.7, 0.7, 1)
            )
            btn.lvl = lvl
            btn.bind(on_press=self.select_level)
            level_layout.add_widget(btn)
            self.level_buttons[lvl] = btn
        
        layout.add_widget(level_layout)
        
        start_btn = Button(
            text='Start Session', 
            size_hint=(1, 0.15), 
            background_color=(0.3, 0.8, 0.3, 1),
            font_size='18sp', 
            color=(1,1,1,1)
        )
        start_btn.bind(on_press=self.start_session)
        layout.add_widget(start_btn)
        
        back_btn = Button(
            text='Back', 
            size_hint=(1, 0.1), 
            background_color=(0.6, 0.6, 0.6, 1)
        )
        back_btn.bind(on_press=lambda x: self.manager.current('welcome'))
        layout.add_widget(back_btn)
        
        self.add_widget(layout)
    
    def select_level(self, instance):
        self.selected_level = instance.lvl
        for lvl, btn in self.level_buttons.items():
            btn.background_color = (0.2, 0.6, 1, 1) if lvl == self.selected_level else (0.7, 0.7, 0.7, 1)
    
    def start_session(self, instance):
        keywords = [kw.strip() for kw in self.topic_input.text.split(',') if kw.strip()]
        if not keywords:
            keywords = ['general']
        self.manager.keywords = keywords
        self.manager.level = self.selected_level
        self.manager.mode = 'new_words'
        self.manager.current = 'training'
    
    def on_enter(self):
        # Применяем сохранённый цвет фона
        App.get_running_app().apply_saved_background()


# ============================================================================
# ЭКРАН ТРЕНИРОВКИ
# ============================================================================
class TrainingScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 8
        self.current_word = None
        self.timer_event = None
        self.elapsed_time = 0
        self.words_queue = []
        self.answered_count = 0
        self.total_words = 0
        
        header = BoxLayout(size_hint=(1, 0.12), spacing=10)
        self.topic_label = Label(
            text='Тема: -', 
            font_size='14sp', 
            halign='left', 
            size_hint=(0.6, 1),
            color=(0, 0, 0, 1)
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
        
        self.word_display = Label(
            text='', 
            font_size='24sp', 
            bold=True, 
            size_hint=(1, 0.25), 
            halign='center', 
            valign='middle',
            color=(0, 0, 0, 1)
        )
        self.add_widget(self.word_display)
        
        self.answer_input = TextInput(
            hint_text='Введите перевод...', 
            multiline=False, 
            size_hint=(1, 0.12), 
            font_size='18sp'
        )
        self.answer_input.bind(on_text_validate=lambda x: self.check_answer(None))
        self.add_widget(self.answer_input)
        
        check_btn = Button(
            text='Проверить', 
            size_hint=(1, 0.1), 
            background_color=(0.2, 0.6, 1, 1), 
            color=(1,1,1,1)
        )
        check_btn.bind(on_press=self.check_answer)
        self.add_widget(check_btn)
        
        self.example_box = BoxLayout(
            orientation='vertical', 
            size_hint=(1, 0.15), 
            opacity=0, 
            disabled=True
        )
        self.example_label = Label(
            text='', 
            font_size='14sp', 
            color=(0.3, 0.3, 0.3, 1), 
            halign='center', 
            valign='middle'
        )
        self.example_box.add_widget(self.example_label)
        self.add_widget(self.example_box)
        
        self.result_label = Label(
            text='', 
            font_size='16sp', 
            size_hint=(1, 0.08), 
            halign='center',
            color=(0, 0, 0, 1)
        )
        self.add_widget(self.result_label)
        
        self.progress_label = Label(
            text='Слово 0/0', 
            font_size='13sp', 
            color=(0.5, 0.5, 0.5, 1), 
            size_hint=(1, 0.08)
        )
        self.add_widget(self.progress_label)
    
    def on_enter(self):
        # Применяем сохранённый цвет фона
        App.get_running_app().apply_saved_background()
        
        self.db_path = App.get_running_app().db_path
        self.answered_count = 0
        mode = getattr(self.manager, 'mode', 'new_words')
        level = getattr(self.manager, 'level', 'A1')
        keywords = getattr(self.manager, 'keywords', ['general'])
        
        self.topic_label.text = f'📚 {", ".join(keywords)} | {level} | {mode}'
        self.load_words(keywords, level, mode)
    
    def on_leave(self):
        if self.timer_event:
            self.timer_event.cancel()
            self.timer_event = None
    
    def load_words(self, keywords, level, mode):
        from smart_search import SimpleWordSearch
        search = SimpleWordSearch(self.db_path)
        search.set_username("local_user")
        
        if mode == 'new_words':
            self.words_queue = search.find_unanswered_words(keywords=keywords, level=level, limit=20)
        else:
            self.words_queue = search.find_words_for_repetition(username="local_user", level=level, limit=20)
        
        self.total_words = len(self.words_queue)
        
        if not self.words_queue:
            self.word_display.text = '[b]Нет слов для этой темы/уровня[/b]'
            self.result_label.text = 'Пополните базу данных или измените параметры поиска'
            return
        
        self.show_next_word()
    
    def show_next_word(self):
        if not self.words_queue:
            self.word_display.text = '[b]🎉 Сессия завершена![/b]'
            self.result_label.text = f'Пройдено слов: {self.answered_count}'
            return
        
        self.current_word = self.words_queue.pop(0)
        # word = (id, word_en, translation, level, topic, frequency, examples_json)
        self.word_display.text = f'[b]{self.current_word[1]}[/b]'
        self.answer_input.text = ''
        self.answer_input.focus = True
        self.example_box.opacity = 0
        self.example_box.disabled = True
        self.example_label.text = ''
        self.result_label.text = ''
        
        if self.timer_event:
            self.timer_event.cancel()
        self.session_start = datetime.now()
        self.timer_event = Clock.schedule_interval(self.update_timer, 0.01)
        self.progress_label.text = f'Слово {self.answered_count + 1}/{self.total_words}'
    
    def update_timer(self, dt):
        if hasattr(self, 'session_start') and self.session_start:
            elapsed = (datetime.now() - self.session_start).total_seconds()
            self.timer_label.text = f'⏱ {elapsed:.2f}с'
            if elapsed >= 10.0 and not self.result_label.text:
                self.handle_timeout()
    
    def check_answer(self, instance):
        if not self.current_word or self.result_label.text:
            return
        
        if self.timer_event:
            self.timer_event.cancel()
        
        user_answer = self.answer_input.text.strip().lower()
        correct_answers = [self.current_word[2].lower()]
        is_correct = user_answer in correct_answers
        
        response_time = (datetime.now() - self.session_start).total_seconds()
        self.save_result(is_correct, response_time)
        
        if is_correct:
            self.result_label.text = '✅ Правильно!'
            self.result_label.color = (0, 0.7, 0, 1)
        else:
            self.result_label.text = f'❌ Правильно: {self.current_word[2]}'
            self.result_label.color = (0.9, 0.2, 0.2, 1)
        
        self.answered_count += 1
        
        if self.current_word[6]:
            import json
            try:
                examples = json.loads(self.current_word[6])
                if examples:
                    self.example_label.text = f"Пример: {examples[0]}"
                    self.example_box.opacity = 1
                    self.example_box.disabled = False
            except:
                pass
        
        Clock.schedule_once(lambda dt: self.show_next_word(), 1.5)
    
    def handle_timeout(self):
        if self.timer_event:
            self.timer_event.cancel()
        self.result_label.text = '⏳ Время вышло!'
        self.result_label.color = (0.8, 0.6, 0, 1)
        self.save_result(False, 10.0)
        self.answered_count += 1
        Clock.schedule_once(lambda dt: self.show_next_word(), 1.5)
    
    def save_result(self, result, response_time):
        if not self.current_word:
            return
        
        now = datetime.now()
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO user_progress
                (user_id, word_id, session_date, session_time, result, response_time, attempt_number)
                VALUES (?, ?, ?, ?, ?, ?, ?)''',
                ("local_user", self.current_word[0], now.strftime('%d.%m.%Y'),
                 now.strftime('%H:%M:%S'), 'correct' if result else 'incorrect',
                 round(response_time, 2), 1))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Ошибка сохранения: {e}")


# ============================================================================
# ГЛАВНЫЙ КЛАСС ПРИЛОЖЕНИЯ
# ============================================================================
class EnglishLearningApp(App):
    def build(self):
        self.db_path = self.get_db_path()
        print(f"[DEBUG] Путь к БД: {self.db_path}")
        
        # Проверка наличия слов в базе
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM words")
            count = cursor.fetchone()[0]
            print(f"[DEBUG] В базе {count} слов")
            conn.close()
        except Exception as e:
            print(f"[ERROR] Не удалось прочитать базу: {e}")
        
        self.title = 'English Learning'
        
        sm = ScreenManager(transition=FadeTransition(duration=0.3))
        sm.add_widget(WelcomeScreen(name='welcome'))
        sm.add_widget(TopicSelectScreen(name='topic_select'))
        sm.add_widget(TrainingScreen(name='training'))
        
        # Применяем сохранённый цвет фона при запуске
        Clock.schedule_once(lambda dt: self.apply_saved_background(), 0.1)
        
        return sm
    
    def get_db_path(self):
        user_dir = self.user_data_dir
        db_path = os.path.join(user_dir, 'words.db')
        
        if not os.path.exists(db_path):
            try:
                possible_sources = [
                    os.path.join(os.getcwd(), 'database', 'words.db'),
                    os.path.join(os.path.dirname(__file__), 'database', 'words.db'),
                ]
                source_db = next((p for p in possible_sources if p and os.path.exists(p)), None)
                
                if source_db:
                    os.makedirs(user_dir, exist_ok=True)
                    shutil.copy2(source_db, db_path)
                    print(f"[INFO] ✅ База скопирована: {db_path}")
                else:
                    print(f"[WARNING] ⚠️ Исходная база не найдена, создаём пустую")
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute('''CREATE TABLE IF NOT EXISTS words (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, word_en TEXT NOT NULL,
                        translation TEXT, level TEXT, topic TEXT, frequency INTEGER DEFAULT 0,
                        examples_json TEXT)''')
                    cursor.execute('''CREATE TABLE IF NOT EXISTS user_progress (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, word_id INTEGER,
                        session_date TEXT, session_time TEXT, result TEXT,
                        response_time REAL, attempt_number INTEGER)''')
                    conn.commit()
                    conn.close()
            except Exception as e:
                print(f"[ERROR] ❌ Ошибка инициализации БД: {e}")
        
        return db_path
    
    def save_bg_color(self, color_name):
        """Сохраняет выбранный цвет фона"""
        config_path = os.path.join(self.user_data_dir, 'settings.json')
        try:
            settings = {}
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    settings = json.load(f)
            
            settings['bg_color'] = color_name
            
            with open(config_path, 'w') as f:
                json.dump(settings, f)
        except Exception as e:
            print(f"[ERROR] Не удалось сохранить цвет фона: {e}")
    
    def load_bg_color(self):
        """Загружает сохранённый цвет фона"""
        config_path = os.path.join(self.user_data_dir, 'settings.json')
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    settings = json.load(f)
                    return settings.get('bg_color', 'light_blue')
        except Exception as e:
            print(f"[ERROR] Не удалось загрузить цвет фона: {e}")
        
        return 'light_blue'  # Цвет по умолчанию
    
    def apply_background_color(self, color):
        """Применяет цвет фона ко всем экранам"""
        Window.clearcolor = color
    
    def apply_saved_background(self):
        """Применяет сохранённый цвет фона"""
        color_name = self.load_bg_color()
        color = COLOR_OPTIONS.get(color_name, DEFAULT_BG_COLOR)
        Window.clearcolor = color
    
    def on_pause(self):
        return True
    
    def on_resume(self):
        pass


if __name__ == '__main__':
    EnglishLearningApp().run()
