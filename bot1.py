import asyncio
import logging
from deep_translator import GoogleTranslator
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

# _________________________Настройка логирования_________________________
logging.basicConfig(level=logging.INFO)

# _________________________Инициализация бота с токеном_________________________
bot = Bot(
    token='токен',
    default=DefaultBotProperties(parse_mode=ParseMode.HTML) # режим форматирования текста
)
# хранилище состояний в памяти 
storage = MemoryStorage()
# распределяет входящие сообщения по нужным обработчикам 
dp = Dispatcher(storage=storage)

# _________________________Создаем клавиатуру с кнопками выбора направления перевода, в сообщении_________________________
def get_main_keyboard():
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(
                text='🇷🇺 → 🇺🇸 Русский-Английский', 
                callback_data='ru_en' # данные отправляющиеся при нажатии на кнопку 
            )
        ],
        [
            types.InlineKeyboardButton(
                text='🇺🇸 → 🇷🇺 Английский-Русский', 
                callback_data='en_ru'
            )
        ]
    ])
    return keyboard

# _________________________Обработчик команды /start_________________________
@dp.message(Command("start"))
async def start_command(message: types.Message):
    """Отправляем приветственное сообщение с кнопками"""
    await message.answer(
        "👋 Переводчик Русский ↔ Английский\n\n"
        "Выберите направление перевода:",
        reply_markup=get_main_keyboard()  # Прикрепляем клавиатуру
    )

# _________________________Обработчик нажатий на кнопки_________________________
@dp.callback_query(lambda c: c.data in ['ru_en', 'en_ru'])
# нажатие на кнопку..........текущее состояние
async def process_callback(call: types.CallbackQuery, state: FSMContext):
    """Обрабатываем выбор направления перевода"""
    await call.answer()  # Подтверждаем получение callback
    
    # Сохраняем выбранное направление в состоянии
    if call.data == 'ru_en':
        await state.set_data({'direction': 'ru_en', 'source': 'ru', 'target': 'en'})
        direction_text = "Русский → Английский"
    else:
        await state.set_data({'direction': 'en_ru', 'source': 'en', 'target': 'ru'})
        direction_text = "Английский → Русский"
    
    # _________________________Просим пользователя отправить текст_________________________
    await call.message.edit_text(
        f"✅ Выбрано: {direction_text}\n\n"
        "Отправьте текст для перевода:",
        # Клавиатура с одной кнопкой "Назад"
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text='◀️ Назад', callback_data='back')]
        ])
    )

# _________________________Функция для перевода текста_________________________
async def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    """Переводит текст через Google Translate"""
    try: 
        # Создаем объект переводчика с указанием языков
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        # Выполняем перевод
        result = translator.translate(text)
        return result
    except Exception as e:
        # Если произошла ошибка, логируем ее и возвращаем сообщение пользователю
        logging.error(f"Translation error: {e}")
        return f"Ошибка перевода: {str(e)}"

#_________________________ Обработчик текстовых сообщений (пользователь отправляет текст для перевода)_________________________
@dp.message()
async def handle_text_message(message: types.Message, state: FSMContext):
    """Обрабатывает текст для перевода"""
    # Получаем данные о выбранном направлении
    data = await state.get_data()
    
    # Если направление не выбрано, показываем меню
    if not data.get('direction'):
        # Показываем главное меню
        await start_command(message)
        return
    
    # Получаем настройки перевода
    source_lang = data.get('source', 'ru')
    target_lang = data.get('target', 'en')
    
    # Показываем статус перевода
    status_msg = await message.reply("🔄 Перевожу...")
    
    # Выполняем перевод
    translated = await translate_text(message.text, source_lang, target_lang)
    
    # Удаляем сообщение со статусом
    await bot.delete_message(message.chat.id, status_msg.message_id)
    
    # Отправляем результат
    await message.reply(
        f"✅ <b>Перевод:</b>\n\n"
        f"{translated}\n\n"
        f"<i>Для нового перевода выберите направление:</i>",
        reply_markup=get_main_keyboard()
    )

# _________________________Обработчик кнопки "Назад"_________________________
@dp.callback_query(lambda c: c.data == 'back')
async def back_to_menu(call: types.CallbackQuery, state: FSMContext):
    """Возвращаемся в главное меню"""
    await state.clear() # очищаем состояние
    await call.message.edit_text(
        "👋 Переводчик Русский ↔ Английский\n\n"
        "Выберите направление перевода:",
        reply_markup=get_main_keyboard()
    )
    await call.answer()

# _________________________Основная функция запуска бота_________________________
async def main():
    print('Бот запущен!')
    await dp.start_polling(bot)

# _________________________Запуск бота_________________________
if __name__ == '__main__':
#выполняет асинхронный код   
    asyncio.run(main())