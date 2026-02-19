import asyncio
import logging
import os
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from deep_translator import GoogleTranslator
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

# _________________________Настройка логирования_________________________
logging.basicConfig(level=logging.INFO)

# _________________________Глобальные переменные_________________________
TELEGRAM_BOT_TOKEN = None
bot = None
dp = None

# _________________________Класс состояний для FSM_________________________
class TranslationState(StatesGroup):
    waiting_for_direction = State()
    waiting_for_text = State()

# ========================== ТЕЛЕГРАМ БОТ ==========================

def initialize_bot(token: str):
    """Инициализирует бота с указанным токеном"""
    global bot, dp, TELEGRAM_BOT_TOKEN
    
    TELEGRAM_BOT_TOKEN = token
    bot = Bot(
        token=TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher(storage=MemoryStorage())
    setup_bot_handlers()
    
    return bot

def setup_bot_handlers():
    """Настраивает обработчики для бота"""
    
    def get_main_keyboard():
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text='🇷🇺 → 🇺🇸 Русский-Английский', 
                    callback_data='ru_en'
                )
            ],
            [
                types.InlineKeyboardButton(
                    text='🇺🇸 → 🇷🇺 Английский-Русский', 
                    callback_data='en_ru'
                )
            ],
            [
                types.InlineKeyboardButton(
                    text='ℹ️ Информация о боте', 
                    callback_data='bot_info'
                )
            ]
        ])
        return keyboard

    def get_back_keyboard():
        return types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text='◀️ Назад в меню', callback_data='back_to_menu')]
        ])

    @dp.message(Command("start"))
    async def start_command(message: types.Message, state: FSMContext):
        """Главное меню"""
        await state.clear()
        
        await message.answer(
            "👋 Добро пожаловать в Переводчик!\n\n"
            "Выберите направление перевода:",
            reply_markup=get_main_keyboard()
        )

    @dp.message(Command("help"))
    async def help_command(message: types.Message):
        """Помощь по использованию бота"""
        await message.answer(
            "🤖 <b>Помощь по использованию переводчика</b>\n\n"
            "📝 <b>Как использовать:</b>\n"
            "1. Выберите направление перевода\n"
            "2. Отправьте текст для перевода\n"
            "3. Получите результат\n\n"
            "🔄 <b>Доступные переводы:</b>\n"
            "• Русский → Английский\n"
            "• Английский → Русский\n\n"
            "⚡ <b>Команды:</b>\n"
            "/start - Главное меню\n"
            "/help - Эта справка\n"
            "/info - Информация о боте",
            reply_markup=get_main_keyboard()
        )

    @dp.message(Command("info"))
    async def info_command(message: types.Message):
        """Информация о боте"""
        try:
            bot_info = await bot.get_me()
            await message.answer(
                f"🤖 <b>Информация о переводчике:</b>\n\n"
                f"👤 <b>Имя:</b> {bot_info.first_name}\n"
                f"📝 <b>Username:</b> @{bot_info.username}\n"
                f"🆔 <b>ID:</b> {bot_info.id}\n\n"
                f"🌐 <b>Доступные языки:</b>\n"
                f"• Русский → Английский\n"
                f"• Английский → Русский\n\n"
                f"⚡ <b>Технологии:</b>\n"
                f"• Aiogram 3.x\n"
                f"• Google Translate API\n"
                f"• Python 3.11+",
                reply_markup=get_main_keyboard()
            )
        except:
            await message.answer(
                "❌ Не удалось получить информацию о боте",
                reply_markup=get_main_keyboard()
            )

    @dp.callback_query()
    async def process_callback(call: types.CallbackQuery, state: FSMContext):
        """Обрабатывает все callback-запросы"""
        await call.answer()
        
        # Информация о боте
        if call.data == 'bot_info':
            try:
                bot_info = await bot.get_me()
                await call.message.edit_text(
                    f"🤖 <b>Информация о боте:</b>\n\n"
                    f"👤 <b>Имя:</b> {bot_info.first_name}\n"
                    f"📝 <b>Username:</b> @{bot_info.username}\n"
                    f"🆔 <b>ID:</b> {bot_info.id}\n\n"
                    f"🌐 <b>Язык:</b> {bot_info.language_code or 'Не указан'}\n"
                    f"✅ <b>Может читать групповые сообщения:</b> {'Да' if bot_info.can_read_all_group_messages else 'Нет'}\n"
                    f"💬 <b>Поддерживает инлайн-режим:</b> {'Да' if bot_info.supports_inline_queries else 'Нет'}",
                    reply_markup=get_main_keyboard()
                )
            except:
                await call.message.edit_text(
                    "❌ <b>Не удалось получить информацию о боте</b>",
                    reply_markup=get_main_keyboard()
                )
            return
        
        # Выбор направления перевода
        elif call.data in ['ru_en', 'en_ru']:
            # Сохраняем выбранное направление
            if call.data == 'ru_en':
                await state.update_data({
                    'direction': 'ru_en',
                    'source': 'ru',
                    'target': 'en',
                    'direction_text': 'Русский → Английский'
                })
            else:
                await state.update_data({
                    'direction': 'en_ru',
                    'source': 'en',
                    'target': 'ru',
                    'direction_text': 'Английский → Русский'
                })
            
            data = await state.get_data()
            direction_text = data.get('direction_text', '')
            
            await call.message.edit_text(
                f"✅ Выбрано: <b>{direction_text}</b>\n\n"
                "Отправьте текст для перевода:",
                reply_markup=get_back_keyboard()
            )
            await state.set_state(TranslationState.waiting_for_text)
            return
        
        # Назад в меню
        elif call.data == 'back_to_menu':
            await state.clear()
            await call.message.edit_text(
                "👋 Переводчик Русский ↔ Английский\n\n"
                "Выберите направление перевода:",
                reply_markup=get_main_keyboard()
            )
            return

    async def translate_text(text: str, source_lang: str, target_lang: str) -> str:
        """Переводит текст через Google Translate"""
        try:
            translator = GoogleTranslator(source=source_lang, target=target_lang)
            result = translator.translate(text)
            return result
        except Exception as e:
            logging.error(f"Translation error: {e}")
            return f"Ошибка перевода: {str(e)}"

    @dp.message()
    async def handle_text_message(message: types.Message, state: FSMContext):
        """Обрабатывает текст для перевода"""
        current_state = await state.get_state()
        
        # Если ждем текст для перевода
        if current_state == TranslationState.waiting_for_text.state:
            data = await state.get_data()
            
            if not data.get('direction'):
                await message.answer(
                    "Сначала выберите направление перевода:",
                    reply_markup=get_main_keyboard()
                )
                return
            
            # Получаем настройки перевода
            source_lang = data.get('source', 'ru')
            target_lang = data.get('target', 'en')
            direction_text = data.get('direction_text', '')
            
            # Показываем статус перевода
            status_msg = await message.answer("🔄 Перевожу...")
            
            # Выполняем перевод
            translated = await translate_text(message.text, source_lang, target_lang)
            
            # Удаляем сообщение со статусом
            try:
                await bot.delete_message(message.chat.id, status_msg.message_id)
            except:
                pass
            
            # Отправляем результат
            await message.answer(
                f"📝 <b>Оригинал:</b>\n{message.text}\n\n"
                f"✅ <b>Перевод ({direction_text}):</b>\n{translated}\n\n"
                f"<i>Для нового перевода выберите направление:</i>",
                reply_markup=get_main_keyboard()
            )
            await state.clear()
        else:
            # Если направление не выбрано, показываем меню
            await start_command(message, state)

# _________________________Функция проверки токена_________________________
async def check_token_async(token: str):
    """Асинхронно проверяет валидность токена"""
    try:
        temp_bot = Bot(token=token)
        bot_info = await temp_bot.get_me()
        await temp_bot.session.close()
        return True, f"✅ Токен валидный!\n🤖 Бот: @{bot_info.username}\n👤 Имя: {bot_info.first_name}"
    except Exception as e:
        return False, f"❌ Неверный токен: {str(e)}"

# _________________________Основная функция запуска бота_________________________
async def start_bot():
    """Запускает бота"""
    if not TELEGRAM_BOT_TOKEN:
        print("❌ Токен не установлен. Используйте приложение для настройки.")
        return
    
    print('='*50)
    print('🤖 Запуск бота-переводчика...')
    print('='*50)
    
    # Проверяем токен
    is_valid, message = await check_token_async(TELEGRAM_BOT_TOKEN)
    if not is_valid:
        print(f"\n{message}")
        return
    
    print('\n✅ Бот успешно запущен!')
    print('📱 Откройте Telegram и найдите вашего бота')
    print('🚀 Используйте /start для начала работы')
    print('='*50)
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        print(f"\n❌ Ошибка при запуске бота: {e}")
        print("\nВозможные причины:")
        print("1. Неверный токен")
        print("2. Проблемы с интернет-соединением")
        print("3. Бот заблокирован")

# ========================== ГРАФИЧЕСКОЕ ПРИЛОЖЕНИЕ ==========================

class TranslatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Telegram Переводчик - Настройка")
        self.root.geometry("650x550")
        
        # Центрирование окна
        self.center_window(650, 550)
        
        # Стили
        self.setup_styles()
        
        # Создание интерфейса
        self.create_widgets()
        
        # Проверка существующего токена
        self.load_existing_token()

    def center_window(self, width, height):
        """Центрирует окно на экране"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def setup_styles(self):
        """Настраивает стили для интерфейса"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Цвета
        self.bg_color = "#f0f0f0"
        self.button_color = "#4CAF50"
        self.text_bg = "#ffffff"
        
        self.root.configure(bg=self.bg_color)

    def create_widgets(self):
        """Создает виджеты интерфейса"""
        # Главный контейнер
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Заголовок
        title_label = ttk.Label(
            main_frame,
            text="🤖 Telegram Переводчик",
            font=("Arial", 18, "bold"),
            foreground="#2c3e50"
        )
        title_label.pack(pady=(0, 15))
        
        # Описание
        desc_label = ttk.Label(
            main_frame,
            text="Настройте токен бота для запуска переводчика в Telegram",
            font=("Arial", 10),
            foreground="#7f8c8d"
        )
        desc_label.pack(pady=(0, 20))
        
        # Фрейм для ввода токена
        token_frame = ttk.LabelFrame(main_frame, text="Токен бота", padding="15")
        token_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Инструкция с кнопкой
        instruction_frame = ttk.Frame(token_frame)
        instruction_frame.pack(fill=tk.X, pady=(0, 10))
        
        instruction_label = ttk.Label(
            instruction_frame,
            text="Как получить токен:",
            font=("Arial", 9, "bold")
        )
        instruction_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Инструкции
        instructions = [
            "1. Откройте @BotFather в Telegram",
            "2. Используйте команду /newbot",
            "3. Следуйте инструкциям",
            "4. Скопируйте полученный токен"
        ]
        
        for instruction in instructions:
            instr_label = ttk.Label(
                instruction_frame,
                text=instruction,
                justify=tk.LEFT
            )
            instr_label.pack(anchor=tk.W)
        
        # Поле для ввода токена с кнопками
        input_frame = ttk.Frame(token_frame)
        input_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Метка
        ttk.Label(input_frame, text="Токен:").pack(anchor=tk.W, pady=(0, 5))
        
        # Фрейм для поля ввода и кнопок
        entry_frame = ttk.Frame(input_frame)
        entry_frame.pack(fill=tk.X)
        
        # Поле для ввода токена
        self.token_var = tk.StringVar()
        self.token_entry = tk.Text(
            entry_frame,
            height=3,
            font=("Courier", 10),
            wrap=tk.WORD,
            bg=self.text_bg
        )
        self.token_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Фрейм для кнопок управления полем ввода
        button_frame = ttk.Frame(entry_frame)
        button_frame.pack(side=tk.RIGHT)
        
        # Кнопки для работы с текстом
        clear_btn = ttk.Button(
            button_frame,
            text="🗑️",
            width=3,
            command=self.clear_token,
            style="Small.TButton"
        )
        clear_btn.pack(pady=(0, 5))
        
        paste_btn = ttk.Button(
            button_frame,
            text="📋",
            width=3,
            command=self.paste_token,
            style="Small.TButton"
        )
        paste_btn.pack(pady=(0, 5))
        
        copy_btn = ttk.Button(
            button_frame,
            text="📄",
            width=3,
            command=self.copy_token,
            style="Small.TButton"
        )
        copy_btn.pack(pady=(0, 5))
        
        # Кнопка показать/скрыть токен
        self.show_token = tk.BooleanVar(value=False)
        show_token_btn = ttk.Checkbutton(
            input_frame,
            text="Показать токен",
            variable=self.show_token,
            command=self.toggle_token_visibility
        )
        show_token_btn.pack(anchor=tk.W, pady=(10, 0))
        
        # Кнопки управления
        action_frame = ttk.Frame(token_frame)
        action_frame.pack(fill=tk.X, pady=(15, 0))
        
        # Стили для кнопок
        style = ttk.Style()
        style.configure("Accent.TButton", 
                       background=self.button_color,
                       foreground="white",
                       font=("Arial", 10, "bold"))
        
        style.configure("Small.TButton",
                       font=("Arial", 8))
        
        check_btn = ttk.Button(
            action_frame,
            text="🔍 Проверить токен",
            command=self.check_token,
            style="Accent.TButton"
        )
        check_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        save_btn = ttk.Button(
            action_frame,
            text="🚀 Сохранить и запустить",
            command=self.save_and_run
        )
        save_btn.pack(side=tk.LEFT)
        
        # Быстрые действия
        quick_frame = ttk.Frame(token_frame)
        quick_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(quick_frame, text="Быстрые действия:").pack(anchor=tk.W, pady=(0, 5))
        
        quick_btn_frame = ttk.Frame(quick_frame)
        quick_btn_frame.pack(fill=tk.X)
        
        load_btn = ttk.Button(
            quick_btn_frame,
            text="📂 Загрузить из файла",
            command=self.load_from_file,
            width=20
        )
        load_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        open_botfather_btn = ttk.Button(
            quick_btn_frame,
            text="🤖 Открыть BotFather",
            command=self.open_botfather,
            width=20
        )
        open_botfather_btn.pack(side=tk.LEFT)
        
        # Зона вывода информации
        info_frame = ttk.LabelFrame(main_frame, text="Информация", padding="10")
        info_frame.pack(fill=tk.BOTH, expand=True, pady=(15, 0))
        
        self.info_text = scrolledtext.ScrolledText(
            info_frame,
            height=10,
            font=("Consolas", 9),
            bg=self.text_bg,
            wrap=tk.WORD
        )
        self.info_text.pack(fill=tk.BOTH, expand=True)
        
        # Добавляем контекстное меню для текстового поля
        self.add_context_menu()
        
        # Бинды на клавиши
        self.token_entry.bind('<Control-v>', lambda e: self.paste_token())
        self.token_entry.bind('<Control-V>', lambda e: self.paste_token())
        self.token_entry.bind('<Control-c>', lambda e: self.copy_token())
        self.token_entry.bind('<Control-C>', lambda e: self.copy_token())
        self.token_entry.bind('<Control-a>', lambda e: self.select_all())
        self.token_entry.bind('<Control-A>', lambda e: self.select_all())
        self.token_entry.bind('<Return>', lambda e: self.check_token())

    def add_context_menu(self):
        """Добавляет контекстное меню для текстового поля"""
        # Создаем меню
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Вставить", command=self.paste_token)
        self.context_menu.add_command(label="Копировать", command=self.copy_token)
        self.context_menu.add_command(label="Вырезать", command=self.cut_token)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Выделить все", command=self.select_all)
        self.context_menu.add_command(label="Очистить", command=self.clear_token)
        
        # Привязываем меню к правой кнопке мыши
        self.token_entry.bind("<Button-3>", self.show_context_menu)
        self.info_text.bind("<Button-3>", self.show_info_context_menu)

    def show_context_menu(self, event):
        """Показывает контекстное меню для поля ввода"""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def show_info_context_menu(self, event):
        """Показывает контекстное меню для информационного поля"""
        info_menu = tk.Menu(self.root, tearoff=0)
        info_menu.add_command(label="Копировать", 
                            command=lambda: self.root.clipboard_clear() or 
                                          self.root.clipboard_append(self.info_text.selection_get()))
        info_menu.add_command(label="Очистить", command=self.clear_info)
        info_menu.add_command(label="Выделить все", 
                            command=lambda: self.info_text.tag_add(tk.SEL, "1.0", tk.END))
        
        try:
            info_menu.tk_popup(event.x_root, event.y_root)
        finally:
            info_menu.grab_release()

    def clear_info(self):
        """Очищает информационное поле"""
        self.info_text.delete(1.0, tk.END)

    def paste_token(self):
        """Вставляет токен из буфера обмена"""
        try:
            # Получаем текст из буфера обмена
            clipboard_text = self.root.clipboard_get()
            # Очищаем поле и вставляем текст
            self.token_entry.delete(1.0, tk.END)
            self.token_entry.insert(1.0, clipboard_text)
            self.log_message("✅ Токен вставлен из буфера обмена")
        except Exception as e:
            self.log_message(f"⚠️ Не удалось вставить из буфера: {str(e)}")

    def copy_token(self):
        """Копирует токен в буфер обмена"""
        try:
            token = self.token_entry.get(1.0, tk.END).strip()
            if token:
                self.root.clipboard_clear()
                self.root.clipboard_append(token)
                self.log_message("✅ Токен скопирован в буфер обмена")
            else:
                self.log_message("⚠️ Нет токена для копирования")
        except Exception as e:
            self.log_message(f"⚠️ Не удалось скопировать токен: {str(e)}")

    def cut_token(self):
        """Вырезает токен в буфер обмена"""
        try:
            # Копируем выделенный текст
            if self.token_entry.tag_ranges(tk.SEL):
                selected_text = self.token_entry.get(tk.SEL_FIRST, tk.SEL_LAST)
                self.root.clipboard_clear()
                self.root.clipboard_append(selected_text)
                # Удаляем выделенный текст
                self.token_entry.delete(tk.SEL_FIRST, tk.SEL_LAST)
                self.log_message("✅ Текст вырезан в буфер обмена")
            else:
                # Если ничего не выделено, копируем весь текст
                self.copy_token()
                self.clear_token()
        except Exception as e:
            self.log_message(f"⚠️ Не удалось вырезать текст: {str(e)}")

    def clear_token(self):
        """Очищает поле ввода токена"""
        self.token_entry.delete(1.0, tk.END)
        self.log_message("🧹 Поле ввода очищено")

    def select_all(self):
        """Выделяет весь текст в поле ввода"""
        self.token_entry.tag_add(tk.SEL, "1.0", tk.END)
        self.token_entry.mark_set(tk.INSERT, "1.0")
        self.token_entry.see(tk.INSERT)
        return "break"  # Предотвращаем стандартное поведение

    def toggle_token_visibility(self):
        """Переключает видимость токена"""
        if self.show_token.get():
            self.token_entry.config(show="", fg="black")
        else:
            # Для Text widget нельзя использовать show, поэтому меняем цвет
            # Вместо этого мы просто оставляем как есть для Text widget
            pass

    def load_existing_token(self):
        """Загружает существующий токен из файла"""
        token_file = "bot_token.txt"
        if os.path.exists(token_file):
            try:
                with open(token_file, 'r', encoding='utf-8') as f:
                    token = f.read().strip()
                    if token:
                        self.token_entry.delete(1.0, tk.END)
                        self.token_entry.insert(1.0, token)
                        self.log_message("✅ Загружен сохраненный токен")
            except Exception as e:
                self.log_message(f"⚠️ Ошибка загрузки токена: {str(e)}")

    def load_from_file(self):
        """Загружает токен из файла"""
        from tkinter import filedialog
        
        try:
            file_path = filedialog.askopenfilename(
                title="Выберите файл с токеном",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            
            if file_path:
                with open(file_path, 'r', encoding='utf-8') as f:
                    token = f.read().strip()
                    if token:
                        self.token_entry.delete(1.0, tk.END)
                        self.token_entry.insert(1.0, token)
                        self.log_message(f"✅ Токен загружен из файла: {os.path.basename(file_path)}")
                    else:
                        self.log_message("⚠️ Файл пустой")
        except Exception as e:
            self.log_message(f"❌ Ошибка загрузки файла: {str(e)}")

    def open_botfather(self):
        """Открывает инструкцию по получению токена"""
        import webbrowser
        
        botfather_info = """
🤖 <b>Как получить токен бота:</b>

1. Откройте Telegram
2. Найдите @BotFather
3. Отправьте команду /newbot
4. Придумайте имя для бота (например: MyTranslatorBot)
5. Придумайте username для бота (должен заканчиваться на 'bot', например: my_translator_bot)
6. Скопируйте полученный токен

<b>Пример токена:</b>
<code>1234567890:ABCdefGHIjklMNOpqrsTUVwxyz</code>

<b>Важно:</b>
• Токен должен храниться в секрете
• Никому не передавайте ваш токен
• Если токен скомпрометирован, создайте новый через @BotFather
"""
        
        messagebox.showinfo("Инструкция по получению токена", botfather_info)
        
        # Спрашиваем, открыть ли BotFather в браузере
        open_web = messagebox.askyesno("Открыть BotFather", 
                                      "Хотите открыть Telegram Web для быстрого доступа к @BotFather?")
        
        if open_web:
            try:
                webbrowser.open("https://web.telegram.org/")
                self.log_message("🌐 Открываю Telegram Web...")
            except:
                self.log_message("⚠️ Не удалось открыть браузер")

    def log_message(self, message):
        """Добавляет сообщение в информационное окно"""
        self.info_text.insert(tk.END, message + "\n")
        self.info_text.see(tk.END)
        self.root.update()

    def check_token(self):
        """Проверяет валидность токена"""
        token = self.token_entry.get(1.0, tk.END).strip()
        
        if not token:
            messagebox.showwarning("Внимание", "Введите токен бота")
            return
        
        self.log_message("🔍 Проверка токена...")
        
        # Запускаем асинхронную проверку
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            is_valid, message = loop.run_until_complete(check_token_async(token))
            loop.close()
            
            self.log_message(message)
            
        except Exception as e:
            self.log_message(f"❌ Ошибка проверки: {str(e)}")

    def save_and_run(self):
        """Сохраняет токен и запускает бота"""
        token = self.token_entry.get(1.0, tk.END).strip()
        
        if not token:
            messagebox.showwarning("Внимание", "Введите токен бота")
            return
        
        # Сохраняем токен в файл
        try:
            with open("bot_token.txt", 'w', encoding='utf-8') as f:
                f.write(token)
            self.log_message("💾 Токен сохранен в файл bot_token.txt")
        except Exception as e:
            self.log_message(f"⚠️ Не удалось сохранить токен: {e}")
            return
        
        # Подтверждение запуска
        confirm = messagebox.askyesno(
            "Подтверждение", 
            "Запустить бота-переводчика?\n\n"
            "После запуска:\n"
            "1. Приложение закроется\n"
            "2. Бот запустится в фоновом режиме\n"
            "3. Откройте Telegram и найдите вашего бота\n\n"
            "Продолжить?"
        )
        
        if not confirm:
            return
        
        # Инициализируем бота
        try:
            initialize_bot(token)
            self.log_message("✅ Бот инициализирован")
            self.log_message("🚀 Запуск бота...")
            
            # Небольшая задержка для отображения сообщения
            self.root.after(1000, self.launch_bot)
            
        except Exception as e:
            self.log_message(f"❌ Ошибка инициализации бота: {e}")

    def launch_bot(self):
        """Запускает бота после закрытия окна"""
        self.root.destroy()
        
        # Запускаем бота в асинхронном режиме
        try:
            asyncio.run(start_bot())
        except KeyboardInterrupt:
            print("\n👋 Бот остановлен пользователем")
        except Exception as e:
            print(f"\n❌ Ошибка при запуске бота: {e}")

    def run(self):
        """Запускает приложение"""
        self.root.mainloop()

# ========================== ОСНОВНАЯ ФУНКЦИЯ ==========================

def main():
    """Основная функция запуска приложения"""
    root = tk.Tk()
    app = TranslatorApp(root)
    app.run()

if __name__ == "__main__":
    main()