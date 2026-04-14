#!/usr/bin/env python3
"""English Learning App - Main Entry Point
Оффлайн-приложение для изучения английских слов"""

import os
import sys
import sqlite3
import shutil
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

# Глобальная переменная для пути к БД
DB_PATH = None

# Функция инициализации БД (вызывается ВНУТРИ App.build())
def get_correct_db_path():
    """
    Получает правильный путь к базе данных.
    На Android копирует БД из ресурсов в личную папку приложения.
    """
    app = App.get_running_app()
    
    # 1. Путь к личной папке приложения (разрешена для записи на Android)
    user_dir = app.user_data_dir
    
    # 2. Имя файла базы
    db_name = 'words.db' 
    target_db_path = os.path.join(user_dir, db_name)
    
    # 3. Если базы в личной папке нет — копируем её из ресурсов
    if not os.path.exists(target_db_path):
        try:
            # Путь к исходной базе внутри APK (в папке database)
            # source_dir указывает на корень вашего проекта внутри APK
            source_db_path = os.path.join(app.source_dir, 'database', db_name)
            
            if os.path.exists(source_db_path):
                os.makedirs(user_dir, exist_ok=True)
                shutil.copy2(source_db_path, target_db_path)
                print(f"✅ База данных скопирована в: {target_db_path}")
            else:
                print(f"❌ ОШИБКА: Исходная база не найдена в {source_db_path}")
        except Exception as e:
            print(f"❌ Ошибка копирования базы: {e}")
            
    return target_db_path

# Инициализируем правильный путь
DB_PATH = get_correct_db_path()

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
        title = Label(text='[b]English Learning[/b][v0.1]',
                      markup=True, font_size='28sp', size_hint=(1, 0.15),
                      halign='center', valign='middle')
        self.add_widget(title)
        
        # Поле ввода имени
        self.username_input = TextInput(hint_text='Введите ваше имя',
                                        multiline=False, write_tab=False,
                                        size_hint=(1, 0.1), font_size='18sp')
        self.add_widget(self.username_input)
        
        # Кнопка входа
        login_btn = Button(text='НАЧАТЬ', size_hint=(1, 0.12),
                           font_size='20sp', background_color=(0.2, 0.6, 1, 1),
                           color=(1, 1, 1, 1))
        login_btn.bind(on_press=self.on_login)
        self.add_widget(login_btn)
        
        # Информационная подпись
        info = Label(text='Данные хранятся локально на устройстве',
                     font_size='12sp', color=(0.5, 0.5, 0.5, 1),
                     size_hint=(1, 0.08))
        self.add_widget(info)

    def on_login(self, instance):
        username = self.username_input.text.strip()
        if username:
            self.manager.username = username
            self.manager.current = 'main'
        else:
            self.username_input.hint_text = 'Введите имя!'
            self.username_input.foreground_color = (1, 0, 0, 1)


class MainScreen(Screen):
    """Главный экран: выбор темы и режима"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 10
        
        # Верхняя панель с темой
        header = BoxLayout(size_hint=(1, 0.15), spacing=10)
        self.topic_input = TextInput(hint_text='Введите тему (например: travel)',
                                     multiline=False, size_hint=(0.7, 1),
                                     font_size='16sp')
        header.add_widget(self.topic_input)
        
        # Выбор уровня
        level_layout = BoxLayout(orientation='horizontal', size_hint=(0.3, 1))
        self.selected_level = None
        
        for lvl in ['A1', 'A2', 'B1']:
            btn = Button(text=lvl, size_hint=(1/3, 1))
            btn.lvl = lvl
            btn.bind(on_press=self.select_level)
            setattr(self, f'btn_{lvl}', btn)
            level_layout.add_widget(btn)
            
        header.add_widget(level_layout)
        self.add_widget(header)
        
        # Статус
        self.status_label = Label(text='Выберите уровень и введите тему',
                                  font_size='14sp', color=(0.4, 0.4, 0.4, 1),
                                  size_hint=(1, 0.1))
        self.add_widget(self.status_label)
        
        # Режимы обучения
        modes_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.6), spacing=10)
        
        self.new_words_btn = Button(text='[b]New Words[/b]\nновые слова',
                                    markup=True, font_size='16sp',
                                    background_color=(0.3, 0.8, 0.3, 1),
                                    color=(1, 1, 1, 1))
        self.new_words_btn.bind(on_press=self.start_new_words)
        modes_layout.add_widget(self.new_words_btn)
        
        self.repetition_btn = Button(text='[b]Repetition[/b]\nповторение',
                                     markup=True, font_size='16sp',
                                     background_color=(0.8, 0.6, 0.2, 1),
                                     color=(1, 1, 1, 1), disabled=True)
        self.repetition_btn.bind(on_press=self.start_repetition)
        modes_layout.add_widget(self.repetition_btn)
        
        self.add_widget(modes_layout)
        
        # Кнопка смены темы
        change_btn = Button(text='🔄 Change topic', size_hint=(1, 0.08),
                            background_color=(0.6, 0.6, 0.6, 1))
        change_btn.bind(on_press=self.change_topic)
        self.add_widget(change_btn)

    def select_level(self, instance):
        self.selected_level = instance.lvl
        for lvl in ['A1', 'A2', 'B1']:
            btn = getattr(self, f'btn_{lvl}')
            btn.background_color = (0.8, 0.8, 0.8, 1) if btn.lvl != self.selected_level else (0.2, 0.6, 1, 1)
        
        topic = self.topic_input.text.strip()
        if topic and self.selected_level:
            self.status_label.text = f'Готово: {topic} ({self.selected_level})'
            self.status_label.color = (0, 0.7, 0, 1)
            self.new_words_btn.disabled = False
            self.repetition_btn.disabled = False
        else:
            self.status_label.text = 'Введите тему и выберите уровень'
            self.status_label.color = (0.4, 0.4, 0.4, 1)
            self.new_words_btn.disabled = True
            self.repetition_btn.disabled = True

    def start_new_words(self, instance):
        topic = self.topic_input.text.strip() or 'общая'
        if not self.selected_level:
            self.status_label.text = 'Выберите уровень!'
            self.status_label.color = (1, 0, 0, 1)
            return
        self.current_topic = topic
        self.manager.topic = topic
        self.manager.level = self.selected_level
        self.manager.mode = 'new_words'
        self.manager.current = 'training'

    def start_repetition(self, instance):
        self.manager.mode = 'repetition'
        self.manager.current = 'training'

    def change_topic(self, instance):
        self.topic_input.text = ''
        self.selected_level = None
        self.current_topic = None
        for lvl in ['A1', 'A2', 'B1']:
            getattr(self, f'btn_{lvl}').background_color = (0.8, 0.8, 0.8, 1)
        self.status_label.text = 'Введите тему и выберите уровень'
        self.status_label.color = (0.4, 0.4, 0.4, 1)
        self.new_words_btn.disabled = True
        self.repetition_btn.disabled = True


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
        self.topic_label = Label(text='Тема: -', font_size='14sp',
                                 halign='left', size_hint=(0.6, 1))
        header.add_widget(self.topic_label)
        
        self.timer_label = Label(text='⏱ 0.00с', font_size='16sp',
                                 color=(0.2, 0.6, 1, 1), halign='right',
                                 size_hint=(0.4, 1))
        header.add_widget(self.timer_label)
        self.add_widget(header)
        
        # === Слово ===
        self.word_display = Label(text='', font_size='24sp', bold=True,
                                  size_hint=(1, 0.25), halign='center',
                                  valign='middle')
        self.add_widget(self.word_display)
        
        # === Поле ответа ===
        self.answer_input = TextInput(hint_text='Введите перевод...',
                                      multiline=False, size_hint=(1, 0.12),
                                      font_size='18sp')
        self.answer_input.bind(on_text_validate=self.on_answer_enter)
        self.add_widget(self.answer_input)
        
        # === Кнопка проверки ===
        check_btn = Button(text='Проверить', size_hint=(1, 0.1),
                           background_color=(0.2, 0.6, 1, 1), color=(1, 1, 1, 1))
        check_btn.bind(on_press=self.check_answer)
        self.add_widget(check_btn)
        
        # === Пример использования ===
        self.example_box = BoxLayout(orientation='vertical', size_hint=(1, 0.15),
                                     opacity=0, disabled=True)
        self.example_label = Label(text='', font_size='14sp', color=(0.3, 0.3, 0.3, 1),
                                   halign='center', valign='middle')
        self.example_box.add_widget(self.example_label)
        self.add_widget(self.example_box)
        
        # === Результат ответа ===
        self.result_label = Label(text='', font_size='16sp', size_hint=(1, 0.08),
                                  halign='center')
        self.add_widget(self.result_label)
        
        # === Прогресс ===
        self.progress_label = Label(text='Слово 0/0', font_size='13sp',
                                    color=(0.5, 0.5, 0.5, 1), size_hint=(1, 0.08))
        self.add_widget(self.progress_label)

    def on_enter(self):
        """Вызывается при переходе на экран"""
        topic = getattr(self.manager, 'topic', 'общая')
        level = getattr(self.manager, 'level', 'A1')
        mode = getattr(self.manager, 'mode', 'new_words')
        self.topic_label.text = f'📚 {topic} | {level} | {mode}'
        self.load_words(topic, level, mode)

    def on_leave(self):
        """Вызывается при уходе с экрана"""
        if self.timer_event:
            self.timer_event.cancel()
            self.timer_event = None

    def load_words(self, topic, level, mode):
        """Загрузка слов для сессии"""
        from smart_search import SimpleWordSearch
        search = SimpleWordSearch(DB_PATH)
        
        if mode == 'new_words':
            self.words_queue = search.find_unanswered_words(keywords=[topic], level=level, limit=20)
        else:
            self.words_queue = search.find_weak_words(keywords=[topic], level=level, limit=20)
            
        self.total_words = len(self.words_queue)
        self.answered_count = 0
        
        if not self.words_queue:
            self.word_display.text = '[b]Нет слов для этой темы/уровня[/b]'
            self.result_label.text = 'Попробуйте другую тему или режим "Новые слова"'
            return
            
        self.show_next_word()

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
            self.timer_event = None
            
        user_answer = self.answer_input.text.strip().lower()
        correct_answers = [self.current_word[2].lower()]
        # Можно добавить альтернативные варианты из examples_json если нужно
        
        is_correct = user_answer in correct_answers
        
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
        
        # Показать пример использования (если есть)
        if self.current_word[6]: # examples_json
            import json
            try:
                examples = json.loads(self.current_word[6])
                if examples:
                    self.example_label.text = f"Пример: {examples[0]}"
                    self.example_box.opacity = 1
                    self.example_box.disabled = False
            except:
                pass
                
        # Показать следующее слово через 1.5 секунды
        Clock.schedule_once(lambda dt: self.show_next_word(), 1.5)

    def handle_timeout(self):
        """Обработка таймаута (10 секунд)"""
        if self.timer_event:
            self.timer_event.cancel()
            self.timer_event = None
        self.result_label.text = '⏳ Время вышло!'
        self.result_label.color = (0.8, 0.6, 0, 1)
        # Считаем как неправильный ответ
        self.save_result(False, 10.0)
        self.answered_count = getattr(self, 'answered_count', 0) + 1
        Clock.schedule_once(lambda dt: self.show_next_word(), 1.5)

    def save_result(self, result, response_time):
        """Сохранение результата в базу данных"""
        if not self.current_word or not self.manager.username:
            return
            
        now = datetime.now()
        attempt_num = 1 # Упрощено для примера
        
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO user_progress
                              (user_id, word_id, session_date, session_time, result, response_time, attempt_number)
                              VALUES (?, ?, ?, ?, ?, ?, ?)''',
                          (self.manager.username,
                           self.current_word[0],
                           now.strftime('%d.%m.%Y'),
                           now.strftime('%H:%M:%S'),
                           result,
                           round(response_time, 2),
                           attempt_num))
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
        # 1. Сначала настраиваем БД
        if not setup_database():
            return Label(text="Ошибка инициализации БД", halign='center', valign='middle')

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
        return True

    def on_resume(self):
        """Обработка разворачивания приложения"""
        pass


# ============================================================================
# ТОЧКА ВХОДА
# ============================================================================

if __name__ == '__main__':
    EnglishLearningApp().run()
