#!/usr/bin/env python3
"""English Learning App - Main Entry Point
Оффлайн-приложение для изучения английских слов"""
import os
import sys
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
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
from kivy.config import Config
from kivy.core.window import Window
from kivy.storage.jsonstore import JsonStore

# Настройки для Android
Config.set('graphics', 'multisamples', '0')
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

# Доступные цвета фона
AVAILABLE_COLORS = {
    'default': (0.95, 0.95, 0.95, 1),      # Светло-серый (по умолчанию)
    'pink': (1.0, 0.92, 0.95, 1),          # Светло-розовый
    'green': (0.92, 1.0, 0.92, 1),         # Светло-зелёный
    'blue': (0.92, 0.95, 1.0, 1),          # Светло-голубой
    'yellow': (1.0, 0.98, 0.92, 1),        # Светло-жёлтый
}

COLOR_NAMES = {
    'default': 'Серый',
    'pink': 'Розовый',
    'green': 'Зелёный',
    'blue': 'Голубой',
    'yellow': 'Жёлтый',
}

# ============================================================================
# КЛАССЫ ЭКРАНОВ
# ============================================================================
class WelcomeScreen(Screen):
    """Экран приветствия"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 15
        
        # Заголовок с приветствием
        self.greeting_label = Label(
            text='',
            font_size='28sp',
            bold=True,
            size_hint=(1, 0.2),
            halign='center',
            valign='middle'
        )
        self.add_widget(self.greeting_label)
        
        # Статистика
        self.stats_label = Label(
            text='Загрузка статистики...',
            font_size='16sp',
            size_hint=(1, 0.1),
            halign='center'
        )
        self.add_widget(self.stats_label)
        
        # Кнопки режимов
        modes_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.5), spacing=10)
        
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
            disabled=True
        )
        self.repetition_btn.bind(on_press=self.start_repetition)
        modes_layout.add_widget(self.repetition_btn)
        
        self.progress_btn = Button(
            text='[b]My Progress[/b]\nмой прогресс',
            markup=True,
            font_size='16sp',
            background_color=(0.5, 0.5, 0.8, 1),
            color=(1, 1, 1, 1)
        )
        self.progress_btn.bind(on_press=self.show_progress)
        modes_layout.add_widget(self.progress_btn)
        
        self.add_widget(modes_layout)
        
        # Нижняя панель с кнопкой выбора цвета
        bottom_layout = BoxLayout(size_hint=(1, 0.1), spacing=10)
        
        # Кнопка выбора цвета (палитра)
        self.color_btn = Button(
            text='🎨 Цвет фона',
            font_size='14sp',
            background_color=(0.7, 0.7, 0.9, 1),
            color=(0, 0, 0, 1)
        )
        self.color_btn.bind(on_press=self.show_color_picker)
        bottom_layout.add_widget(self.color_btn)
        
        # Кнопка смены темы (для совместимости)
        change_btn = Button(
            text='🔄 Сменить тему',
            font_size='14sp',
            background_color=(0.6, 0.6, 0.6, 1),
            color=(1, 1, 1, 1)
        )
        change_btn.bind(on_press=self.change_topic)
        bottom_layout.add_widget(change_btn)
        
        self.add_widget(bottom_layout)
    
    def on_enter(self):
        """Вызывается при переходе на экран"""
        self.update_greeting()
        self.update_stats()
        self.apply_saved_color()
    
    def update_greeting(self):
        """Обновить приветствие в зависимости от времени суток"""
        hour = datetime.now().hour
        if 4 <= hour < 12:
            greeting = "Good morning!"
        elif 12 <= hour < 18:
            greeting = "Good day!"
        elif 18 <= hour < 22:
            greeting = "Good evening!"
        else:
            greeting = "Good night!"
        self.greeting_label.text = f"[b]{greeting}[/b]"
    
    def update_stats(self):
        """Обновить статистику пользователя"""
        try:
            db_path = App.get_running_app().db_path
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(DISTINCT word_id) 
                FROM user_progress 
                WHERE result='correct' AND user_id='local_user'
            """)
            count = cursor.fetchone()[0]
            conn.close()
            self.stats_label.text = f"✅ Правильно отвечено слов: {count}"
        except Exception as e:
            self.stats_label.text = "База данных не готова"
    
    def apply_saved_color(self):
        """Применить сохранённый цвет фона"""
        app = App.get_running_app()
        color_name = app.get_saved_color()
        color = AVAILABLE_COLORS.get(color_name, AVAILABLE_COLORS['default'])
        self.clearcolor = color
    
    def show_color_picker(self, instance):
        """Показать выбор цвета фона"""
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        content.add_widget(Label(text='Выберите цвет фона:', font_size='18sp', halign='center'))
        
        # Сетка с кнопками цветов
        colors_grid = GridLayout(cols=2, spacing=10, size_hint=(1, 0.8))
        
        for color_key, color_value in AVAILABLE_COLORS.items():
            btn = Button(
                text=COLOR_NAMES[color_key],
                background_color=color_value[:3],  # Без alpha
                color=(0, 0, 0, 1) if color_key != 'yellow' else (0.3, 0.3, 0.3, 1),
                size_hint=(1, 1),
                font_size='14sp'
            )
            btn.color_key = color_key
            btn.bind(on_press=self.select_color)
            colors_grid.add_widget(btn)
        
        content.add_widget(colors_grid)
        
        # Кнопка закрытия
        close_btn = Button(text='Закрыть', size_hint=(1, 0.15))
        close_btn.bind(on_press=lambda x: popup.dismiss())
        content.add_widget(close_btn)
        
        popup = Popup(
            title='🎨 Выбор цвета фона',
            content=content,
            size_hint=(0.8, 0.6),
            auto_dismiss=False
        )
        popup.open()
    
    def select_color(self, instance):
        """Сохранить выбранный цвет и применить его"""
        color_key = instance.color_key
        app = App.get_running_app()
        app.save_color(color_key)
        
        # Применить цвет ко всем экранам
        color = AVAILABLE_COLORS[color_key]
        app.set_app_color(color)
        
        # Закрыть popup (находим его через родителя кнопки)
        popup = instance.parent.parent.parent
        popup.dismiss()
    
    def start_new_words(self, instance):
        """Начать изучение новых слов"""
        self.manager.mode = 'new_words'
        self.manager.current = 'topic_select'
    
    def start_repetition(self, instance):
        """Начать повторение"""
        self.manager.mode = 'repetition'
        self.manager.current = 'training'
    
    def show_progress(self, instance):
        """Показать прогресс"""
        content = Label(
            text='📊 Ваш прогресс:\n\n'
                 'Общее количество сессий: 0\n'
                 'Правильных ответов: 0\n'
                 'Процент успеха: 0%\n'
                 'Последняя активность: -',
            font_size='16sp',
            halign='center',
            valign='middle'
        )
        popup = Popup(title='Мой прогресс', content=content, size_hint=(0.8, 0.5))
        popup.open()
    
    def change_topic(self, instance):
        """Сменить тему (заглушка)"""
        self.manager.current = 'topic_select'


class TopicSelectScreen(Screen):
    """Экран выбора темы"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 15
        
        # Заголовок
        self.add_widget(Label(
            text='Выбор темы',
            font_size='24sp',
            bold=True,
            size_hint=(1, 0.1),
            halign='center'
        ))
        
        # Поле ввода темы
        self.topic_input = TextInput(
            hint_text='Введите тему (например: travel, food, business)',
            multiline=False,
            size_hint=(1, 0.1),
            font_size='16sp'
        )
        self.add_widget(self.topic_input)
        
        # Выбор уровня
        level_label = Label(text='Выберите уровень:', font_size='16sp', size_hint=(1, 0.08))
        self.add_widget(level_label)
        
        self.selected_level = 'A1'
        level_layout = BoxLayout(size_hint=(1, 0.12), spacing=10)
        
        for lvl in ['A1', 'A2', 'B1', 'B2']:
            btn = Button(
                text=lvl,
                background_color=(0.2, 0.6, 1, 1) if lvl == 'A1' else (0.7, 0.7, 0.7, 1),
                color=(1, 1, 1, 1)
            )
            btn.lvl = lvl
            btn.bind(on_press=self.select_level)
            setattr(self, f'btn_{lvl}', btn)
            level_layout.add_widget(btn)
        
        self.add_widget(level_layout)
        
        # Кнопка начала
        start_btn = Button(
            text='НАЧАТЬ ОБУЧЕНИЕ',
            size_hint=(1, 0.12),
            font_size='18sp',
            background_color=(0.3, 0.8, 0.3, 1),
            color=(1, 1, 1, 1)
        )
        start_btn.bind(on_press=self.start_session)
        self.add_widget(start_btn)
        
        # Кнопка назад
        back_btn = Button(
            text='← Назад',
            size_hint=(1, 0.1),
            background_color=(0.6, 0.6, 0.6, 1),
            color=(1, 1, 1, 1)
        )
        back_btn.bind(on_press=lambda x: self.manager.current('welcome'))
        self.add_widget(back_btn)
    
    def select_level(self, instance):
        """Выбрать уровень"""
        self.selected_level = instance.lvl
        for lvl in ['A1', 'A2', 'B1', 'B2']:
            btn = getattr(self, f'btn_{lvl}')
            btn.background_color = (0.2, 0.6, 1, 1) if lvl == self.selected_level else (0.7, 0.7, 0.7, 1)
    
    def start_session(self, instance):
        """Начать сессию"""
        topic = self.topic_input.text.strip() or 'general'
        self.manager.topic = topic
        self.manager.level = self.selected_level
        self.manager.current = 'training'


class TrainingScreen(Screen):
    """Экран тренировки"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 8
        
        # Переменные сессии
        self.current_word = None
        self.session_start = None
        self.timer_event = None
        self.words_queue = []
        self.answered_count = 0
        self.total_words = 0
        
        # Верхняя панель
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
        
        # Слово
        self.word_display = Label(
            text='',
            font_size='24sp',
            bold=True,
            size_hint=(1, 0.25),
            halign='center',
            valign='middle'
        )
        self.add_widget(self.word_display)
        
        # Поле ответа
        self.answer_input = TextInput(
            hint_text='Введите перевод...',
            multiline=False,
            size_hint=(1, 0.12),
            font_size='18sp'
        )
        self.answer_input.bind(on_text_validate=lambda x: self.check_answer(None))
        self.add_widget(self.answer_input)
        
        # Кнопка проверки
        check_btn = Button(
            text='Проверить',
            size_hint=(1, 0.1),
            background_color=(0.2, 0.6, 1, 1),
            color=(1, 1, 1, 1)
        )
        check_btn.bind(on_press=self.check_answer)
        self.add_widget(check_btn)
        
        # Пример
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
        
        # Результат
        self.result_label = Label(
            text='',
            font_size='16sp',
            size_hint=(1, 0.08),
            halign='center'
        )
        self.add_widget(self.result_label)
        
        # Прогресс
        self.progress_label = Label(
            text='Слово 0/0',
            font_size='13sp',
            color=(0.5, 0.5, 0.5, 1),
            size_hint=(1, 0.08)
        )
        self.add_widget(self.progress_label)
    
    def on_enter(self):
        """При входе на экран"""
        topic = getattr(self.manager, 'topic', 'general')
        level = getattr(self.manager, 'level', 'A1')
        mode = getattr(self.manager, 'mode', 'new_words')
        self.topic_label.text = f'📚 {topic} | {level} | {mode}'
        self.load_words(topic, level, mode)
        self.apply_saved_color()
    
    def on_leave(self):
        """При уходе с экрана"""
        if self.timer_event:
            self.timer_event.cancel()
            self.timer_event = None
    
    def apply_saved_color(self):
        """Применить сохранённый цвет"""
        app = App.get_running_app()
        color_name = app.get_saved_color()
        color = AVAILABLE_COLORS.get(color_name, AVAILABLE_COLORS['default'])
        self.clearcolor = color
    
    def load_words(self, topic, level, mode):
        """Загрузить слова"""
        try:
            from smart_search import SimpleWordSearch
            db_path = App.get_running_app().db_path
            search = SimpleWordSearch(db_path)
            
            if mode == 'new_words':
                self.words_queue = search.find_unanswered_words(
                    keywords=[topic],
                    level=level,
                    limit=20
                )
            else:
                self.words_queue = search.find_words_for_repetition(
                    username='local_user',
                    level=level,
                    limit=20
                )
            
            self.total_words = len(self.words_queue)
            self.answered_count = 0
            
            if not self.words_queue:
                self.word_display.text = '[b]Нет слов для этой темы/уровня[/b]'
                self.result_label.text = 'Попробуйте другую тему'
                return
            
            self.show_next_word()
        except Exception as e:
            self.word_display.text = '[b]Ошибка загрузки[/b]'
            self.result_label.text = str(e)
    
    def show_next_word(self):
        """Показать следующее слово"""
        if not self.words_queue:
            self.word_display.text = '[b]🎉 Сессия завершена![/b]'
            self.result_label.text = f'Пройдено слов: {self.answered_count}'
            return
        
        self.current_word = self.words_queue.pop(0)
        self.word_display.text = f'[b]{self.current_word[1]}[/b]'
        self.answer_input.text = ''
        self.answer_input.focus = True
        self.example_box.opacity = 0
        self.example_box.disabled = True
        self.example_label.text = ''
        self.result_label.text = ''
        
        self.session_start = datetime.now()
        self.timer_event = Clock.schedule_interval(self.update_timer, 0.01)
        self.progress_label.text = f'Слово {self.answered_count + 1}/{self.total_words}'
    
    def update_timer(self, dt):
        """Обновить таймер"""
        if self.session_start:
            elapsed = (datetime.now() - self.session_start).total_seconds()
            self.timer_label.text = f'⏱ {elapsed:.2f}с'
            if elapsed >= 10.0 and not self.result_label.text:
                self.handle_timeout()
    
    def check_answer(self, instance):
        """Проверить ответ"""
        if not self.current_word or self.result_label.text:
            return
        
        if self.timer_event:
            self.timer_event.cancel()
            self.timer_event = None
        
        user_answer = self.answer_input.text.strip().lower()
        correct_answer = self.current_word[2].lower()
        is_correct = user_answer == correct_answer
        
        response_time = (datetime.now() - self.session_start).total_seconds()
        self.save_result(is_correct, response_time)
        
        if is_correct:
            self.result_label.text = '✅ Правильно!'
            self.result_label.color = (0, 0.7, 0, 1)
        else:
            self.result_label.text = f'❌ Правильно: {self.current_word[2]}'
            self.result_label.color = (0.9, 0.2, 0.2, 1)
        
        self.answered_count += 1
        
        # Показать пример
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
        """Обработка таймаута"""
        if self.timer_event:
            self.timer_event.cancel()
            self.timer_event = None
        
        self.result_label.text = '⏳ Время вышло!'
        self.result_label.color = (0.8, 0.6, 0, 1)
        self.save_result(False, 10.0)
        self.answered_count += 1
        Clock.schedule_once(lambda dt: self.show_next_word(), 1.5)
    
    def save_result(self, result, response_time):
        """Сохранить результат"""
        if not self.current_word:
            return
        
        try:
            db_path = App.get_running_app().db_path
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO user_progress
                (user_id, word_id, session_date, session_time, result, response_time, attempt_number)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                'local_user',
                self.current_word[0],
                datetime.now().strftime('%d.%m.%Y'),
                datetime.now().strftime('%H:%M:%S'),
                'correct' if result else 'incorrect',
                round(response_time, 2),
                1
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
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db_path = None
        self.current_color = 'default'
        self.store = None
    
    def get_db_path(self):
        """Получить путь к базе данных"""
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
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS words (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            word_en TEXT NOT NULL,
                            translation TEXT,
                            level TEXT,
                            topic TEXT,
                            frequency INTEGER DEFAULT 0,
                            examples_json TEXT
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS user_progress (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id TEXT,
                            word_id INTEGER,
                            session_date TEXT,
                            session_time TEXT,
                            result TEXT,
                            response_time REAL,
                            attempt_number INTEGER DEFAULT 1
                        )
                    ''')
                    conn.commit()
                    conn.close()
            except Exception as e:
                print(f"[ERROR] ❌ Ошибка инициализации БД: {e}")
        
        return db_path
    
    def save_color(self, color_name):
        """Сохранить выбранный цвет"""
        if self.store:
            self.store.put('settings', background_color=color_name)
        self.current_color = color_name
    
    def get_saved_color(self):
        """Получить сохранённый цвет"""
        if self.store and self.store.exists('settings'):
            return self.store.get('settings').get('background_color', 'default')
        return 'default'
    
    def set_app_color(self, color):
        """Установить цвет для всех экранов"""
        # Цвет будет применён при переходе на каждый экран
        pass
    
    def build(self):
        """Построить интерфейс"""
        # Инициализация БД
        self.db_path = self.get_db_path()
        print(f"[DEBUG] Путь к БД: {self.db_path}")
        
        # Инициализация хранилища настроек
        try:
            self.store = JsonStore(
                os.path.join(self.user_data_dir, 'settings.json')
            )
        except Exception as e:
            print(f"[WARNING] Не удалось создать хранилище настроек: {e}")
            self.store = None
        
        # Получить сохранённый цвет
        self.current_color = self.get_saved_color()
        
        # Настройка начального цвета окна
        Window.clearcolor = AVAILABLE_COLORS.get(
            self.current_color,
            AVAILABLE_COLORS['default']
        )
        
        self.title = 'English Learning'
        
        # Менеджер экранов
        sm = ScreenManager(transition=FadeTransition(duration=0.3))
        sm.add_widget(WelcomeScreen(name='welcome'))
        sm.add_widget(TopicSelectScreen(name='topic_select'))
        sm.add_widget(TrainingScreen(name='training'))
        
        return sm
    
    def on_pause(self):
        """Обработка сворачивания"""
        return True
    
    def on_resume(self):
        """Обработка разворачивания"""
        pass


# ============================================================================
# ТОЧКА ВХОДА
# ============================================================================
if __name__ == '__main__':
    EnglishLearningApp().run()
