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
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.config import Config
from kivy.core.window import Window
from kivy.core.text import LabelBase

# Регистрация шрифта с поддержкой эмодзи
try:
    assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'fonts')
    emoji_font_path = os.path.join(assets_dir, 'NotoColorEmoji.ttf')
    if os.path.exists(emoji_font_path):
        LabelBase.register(name='EmojiFont', fn_normal=emoji_font_path)
        print(f"[INFO] Emoji font registered: {emoji_font_path}")
    else:
        print(f"[WARNING] Emoji font not found at {emoji_font_path}")
except Exception as e:
    print(f"[ERROR] Failed to register emoji font: {e}")

Config.set('graphics', 'multisamples', '0')
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
Window.clearcolor = (0.95, 0.95, 0.95, 1)

# Установить шрифт с поддержкой эмодзи по умолчанию для всех Label и Button
from kivy.uix.label import Label as KivyLabel
from kivy.uix.button import Button as KivyButton
KivyLabel.font_name = 'EmojiFont'
KivyButton.font_name = 'EmojiFont'

# Цвета фона для выбора
BG_COLORS = {
    'white': (0.95, 0.95, 0.95, 1),
    'light_green': (0.8, 0.95, 0.8, 1),
    'light_pink': (0.95, 0.8, 0.85, 1),
    'light_blue': (0.8, 0.9, 0.95, 1),
    'light_yellow': (0.95, 0.95, 0.7, 1),
}

COLOR_NAMES = ['white', 'light_green', 'light_pink', 'light_blue', 'light_yellow']

# ============================================================================
# МЕНЕДЖЕР ЭКРАНОВ С ПОДДЕРЖКОЙ ЦВЕТА ФОНА
# ============================================================================
class ScreenManagerWithBg(ScreenManager):
    """ScreenManager с возможностью установки общего цвета фона"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_bg_color = (0.95, 0.95, 0.95, 1)  # белый по умолчанию

    def set_background(self, color):
        """Установить цвет фона для всех экранов"""
        self.current_bg_color = color
        Window.clearcolor = color

# ============================================================================
# ЭКРАН ПРИВЕТСТВИЯ
# ============================================================================
class WelcomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=15)

        # Верхняя панель с кнопкой выбора цвета
        top_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.1), spacing=10)

        self.greeting_label = Label(text='', font_size='24sp', bold=True, size_hint=(0.9, 1), halign='center')
        top_layout.add_widget(self.greeting_label)

        # Кнопка выбора цвета фона
        self.color_btn = Button(text='🎨', size_hint=(0.1, 1), font_size='20sp')
        self.color_btn.bind(on_press=self.open_color_picker)
        top_layout.add_widget(self.color_btn)

        self.stats_label = Label(text='Загрузка статистики...', font_size='16sp', size_hint=(1, 0.15), halign='center')

        btn_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.6), spacing=10)

        self.new_words_btn = Button(text='[b]New Words[/b]\nновые слова', markup=True, font_size='16sp',
                                    background_color=(0.3, 0.8, 0.3, 1), color=(1,1,1,1))
        self.new_words_btn.bind(on_press=lambda x: self.manager.current('topic_select'))

        self.repetition_btn = Button(text='[b]Repetition[/b]\nповторение', markup=True, font_size='16sp',
                                     background_color=(0.8, 0.6, 0.2, 1), color=(1,1,1,1))
        self.repetition_btn.bind(on_press=self.start_repetition)

        self.progress_btn = Button(text='[b]My Progress[/b]\nмой прогресс', markup=True, font_size='16sp',
                                   background_color=(0.5, 0.5, 0.8, 1), color=(1,1,1,1))
        self.progress_btn.bind(on_press=self.show_progress)

        btn_layout.add_widget(self.new_words_btn)
        btn_layout.add_widget(self.repetition_btn)
        btn_layout.add_widget(self.progress_btn)

        self.layout.add_widget(top_layout)
        self.layout.add_widget(self.stats_label)
        self.layout.add_widget(btn_layout)
        self.add_widget(self.layout)

    def open_color_picker(self, instance):
        """Открыть popup с выбором цвета фона"""
        content = GridLayout(cols=4, spacing=5, size_hint=(1, 1), padding=10)

        for color_name in COLOR_NAMES:
            color = BG_COLORS[color_name]
            btn = Button(background_color=color[:3], background_normal='')
            btn.bind(on_press=lambda x, c=color_name: self.set_background_color(c))
            content.add_widget(btn)

        popup = Popup(title='Выберите цвет фона', content=content, size_hint=(0.6, 0.4), auto_dismiss=True)
        popup.open()

    def set_background_color(self, color_name):
        """Установить цвет фона и сохранить в конфиг"""
        color = BG_COLORS.get(color_name, BG_COLORS['white'])
        App.get_running_app().set_bg_color(color_name, color)
        self.parent.set_background(color)

    def on_enter(self):
        self.update_greeting()
        self.update_stats()
        # Применить сохранённый цвет фона
        app = App.get_running_app()
        saved_color_name = app.get_saved_bg_color()
        if saved_color_name:
            color = BG_COLORS.get(saved_color_name, BG_COLORS['white'])
            self.parent.set_background(color)

    def update_greeting(self):
        hour = datetime.now().hour
        if 4 <= hour < 12: greeting = "Good morning!"
        elif 12 <= hour < 18: greeting = "Good day!"
        elif 18 <= hour < 22: greeting = "Good evening!"
        else: greeting = "Good night!"
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
        content = Label(text='📊 Detailed statistics will appear here.\nTotal sessions: 0\nAccuracy: 0%\nLast activity: -')
        popup = Popup(title='My Progress', content=content, size_hint=(0.8, 0.4))
        popup.open()

# ============================================================================
# ЭКРАН ВЫБОРА ТЕМЫ
# ============================================================================
class TopicSelectScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        layout.add_widget(Label(text='Enter topic keywords:', font_size='18sp', size_hint=(1, 0.1)))

        self.topic_input = TextInput(hint_text='e.g., food, travel, business', multiline=False,
                                     size_hint=(1, 0.15), font_size='16sp')
        layout.add_widget(self.topic_input)

        level_layout = BoxLayout(size_hint=(1, 0.1), spacing=5)
        self.selected_level = 'A1'
        self.level_buttons = {}
        for lvl in ['A1', 'A2', 'B1', 'B2']:
            btn = Button(text=lvl, background_color=(0.2, 0.6, 1, 1) if lvl=='A1' else (0.7, 0.7, 0.7, 1))
            btn.lvl = lvl
            btn.bind(on_press=self.select_level)
            level_layout.add_widget(btn)
            self.level_buttons[lvl] = btn
        layout.add_widget(level_layout)

        start_btn = Button(text='Start Session', size_hint=(1, 0.15), background_color=(0.3, 0.8, 0.3, 1),
                           font_size='18sp', color=(1,1,1,1))
        start_btn.bind(on_press=self.start_session)
        layout.add_widget(start_btn)

        back_btn = Button(text='Back', size_hint=(1, 0.1), background_color=(0.6, 0.6, 0.6, 1))
        back_btn.bind(on_press=lambda x: self.manager.current('welcome'))
        layout.add_widget(back_btn)
        self.add_widget(layout)

    def select_level(self, instance):
        self.selected_level = instance.lvl
        for lvl, btn in self.level_buttons.items():
            btn.background_color = (0.2, 0.6, 1, 1) if lvl == self.selected_level else (0.7, 0.7, 0.7, 1)

    def start_session(self, instance):
        keywords = [kw.strip() for kw in self.topic_input.text.split(',') if kw.strip()]
        if not keywords: keywords = ['general']
        self.manager.keywords = keywords
        self.manager.level = self.selected_level
        self.manager.mode = 'new_words'
        self.manager.current = 'training'

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
        self.topic_label = Label(text='Тема: -', font_size='14sp', halign='left', size_hint=(0.6, 1))
        header.add_widget(self.topic_label)
        self.timer_label = Label(text='⏱ 0.00с', font_size='16sp', color=(0.2, 0.6, 1, 1), halign='right', size_hint=(0.4, 1))
        header.add_widget(self.timer_label)
        self.add_widget(header)

        self.word_display = Label(text='', font_size='24sp', bold=True, size_hint=(1, 0.25), halign='center', valign='middle')
        self.add_widget(self.word_display)

        self.answer_input = TextInput(hint_text='Введите перевод...', multiline=False, size_hint=(1, 0.12), font_size='18sp')
        self.answer_input.bind(on_text_validate=lambda x: self.check_answer(None))
        self.add_widget(self.answer_input)

        check_btn = Button(text='Проверить', size_hint=(1, 0.1), background_color=(0.2, 0.6, 1, 1), color=(1,1,1,1))
        check_btn.bind(on_press=self.check_answer)
        self.add_widget(check_btn)

        self.example_box = BoxLayout(orientation='vertical', size_hint=(1, 0.15), opacity=0, disabled=True)
        self.example_label = Label(text='', font_size='14sp', color=(0.3, 0.3, 0.3, 1), halign='center', valign='middle')
        self.example_box.add_widget(self.example_label)
        self.add_widget(self.example_box)

        self.result_label = Label(text='', font_size='16sp', size_hint=(1, 0.08), halign='center')
        self.add_widget(self.result_label)

        self.progress_label = Label(text='Слово 0/0', font_size='13sp', color=(0.5, 0.5, 0.5, 1), size_hint=(1, 0.08))
        self.add_widget(self.progress_label)

    def on_enter(self):
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

        if self.timer_event: self.timer_event.cancel()
        self.timer_event = Clock.schedule_interval(self.update_timer, 0.01)
        self.progress_label.text = f'Слово {self.answered_count + 1}/{self.total_words}'

    def update_timer(self, dt):
        if hasattr(self, 'session_start') and self.session_start:
            elapsed = (datetime.now() - self.session_start).total_seconds()
            self.timer_label.text = f'⏱ {elapsed:.2f}с'
            if elapsed >= 10.0 and not self.result_label.text:
                self.handle_timeout()

    def check_answer(self, instance):
        if not self.current_word or self.result_label.text: return
        if self.timer_event: self.timer_event.cancel()

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
            except: pass

        Clock.schedule_once(lambda dt: self.show_next_word(), 1.5)

    def handle_timeout(self):
        if self.timer_event: self.timer_event.cancel()
        self.result_label.text = '⏳ Время вышло!'
        self.result_label.color = (0.8, 0.6, 0, 1)
        self.save_result(False, 10.0)
        self.answered_count += 1
        Clock.schedule_once(lambda dt: self.show_next_word(), 1.5)

    def save_result(self, result, response_time):
        if not self.current_word: return
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

        # Загрузка сохранённого цвета фона
        self.saved_bg_color_name = self.get_saved_bg_color()
        if not self.saved_bg_color_name:
            self.saved_bg_color_name = 'white'

        self.title = 'English Learning'
        sm = ScreenManagerWithBg(transition=FadeTransition(duration=0.3))
        sm.add_widget(WelcomeScreen(name='welcome'))
        sm.add_widget(TopicSelectScreen(name='topic_select'))
        sm.add_widget(TrainingScreen(name='training'))
        # Применить начальный цвет фона
        sm.set_background(BG_COLORS[self.saved_bg_color_name])
        return sm

    def set_bg_color(self, color_name, color):
        """Сохранить выбранный цвет фона и применить его"""
        self.saved_bg_color_name = color_name
        self.save_config()

    def get_saved_bg_color(self):
        """Получить сохранённый цвет фона из конфига"""
        config_file = os.path.join(self.user_data_dir, 'config.json')
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    return config.get('bg_color', 'white')
            except:
                pass
        return 'white'

    def save_config(self):
        """Сохранить конфигурацию приложения"""
        config_file = os.path.join(self.user_data_dir, 'config.json')
        try:
            os.makedirs(self.user_data_dir, exist_ok=True)
            config = {'bg_color': self.saved_bg_color_name}
            with open(config_file, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            print(f"Ошибка сохранения конфига: {e}")

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
                    conn.commit()
                    conn.close()
            except Exception as e:
                print(f"[ERROR] ❌ Ошибка инициализации БД: {e}")
        return db_path

    def on_pause(self): return True
    def on_resume(self): pass

if __name__ == '__main__':
    EnglishLearningApp().run()
