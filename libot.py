import cv2
import logging
import telegram
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from datetime import datetime, timedelta


# Вставьте свой токен
TOKEN = "TELEGRAM TOKEN"
TARGET_CHAT_ID = "GROUP ID"

# Настройка логгирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Обработка команды /start
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('*Привет!*\nОтправь мне *QR-код*, и я его просканирую.', parse_mode=telegram.ParseMode.MARKDOWN)

# Обработка входящих сообщений с изображением
def handle_image(update: Update, context: CallbackContext) -> None:
    # Получаем объект файла из сообщения
    file_id = update.message.photo[-1].file_id
    file = context.bot.get_file(file_id)
    file.download('qr_code.jpg')

    # Пытаемся просканировать QR-код
    qr_image = cv2.imread('qr_code.jpg')
    qr_detector = cv2.QRCodeDetector()
    data, bbox, straight_qrcode  = qr_detector.detectAndDecode(qr_image)
    if data != "":
        if "x512" in data:
            data = data.replace("x512", "")
            update.message.reply_text(f'✅ Книга *"{data}"* успешно возвращена.', parse_mode=telegram.ParseMode.MARKDOWN)
            send_to_target_group(data, update.message.from_user.username, update.message.date, True)
        else:
            update.message.reply_text(f'✅ Книга *"{data}"* успешно отсканирована.', parse_mode=telegram.ParseMode.MARKDOWN)
            send_to_target_group(data, update.message.from_user.username, update.message.date, False)
    else:
        update.message.reply_text('❌ *Не удалось просканировать QR-код.* Попробуйте еще раз.', parse_mode=telegram.ParseMode.MARKDOWN) #🛑⛔❗

# Обработка отправки статуса книги в админ телеграмм группу
def send_to_target_group(data: str, username: str, message_date: datetime, istrue: bool) -> None:
    message_date += timedelta(hours=6)
    formatted_date = message_date.strftime("%Y-%m-%d %H:%M:%S")
    bot = telegram.Bot(token=TOKEN)
    if istrue:
        bot.send_message(chat_id=TARGET_CHAT_ID, text=f'📙 Книга: *{data}*\n\n👤 Пользователь: *{username}*\n✏️ Статус: *Возвращена*\n⌚ Время: *{formatted_date}*', parse_mode=telegram.ParseMode.MARKDOWN)
    else:
        bot.send_message(chat_id=TARGET_CHAT_ID, text=f'📙 Книга: *{data}*\n\n👤 Пользователь: *{username}*\n✏️ Статус: *Взята*\n⌚ Время: *{formatted_date}*', parse_mode=telegram.ParseMode.MARKDOWN)


# Обработка команды /createqr
def create_qr(update: Update, context: CallbackContext) -> None:
    # Получаем текст после команды /createqr
    text = " ".join(context.args)

    # Создаем QR-код
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    
    qr2 = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )

    qr.add_data(text)
    qr.make(fit=True)

    qr2.add_data(text+"x512")
    qr2.make(fit=True)

    img = qr.make_image(image_factory=StyledPilImage, module_drawer=RoundedModuleDrawer())
    img.save('created_qr.png')

    # Отправляем созданный QR-код пользователю
    update.message.reply_text('QR-код для взятия')
    context.bot.send_photo(update.message.chat_id, photo=open('created_qr.png', 'rb'))

    img = qr2.make_image(image_factory=StyledPilImage, module_drawer=RoundedModuleDrawer())
    img.save('created_qr.png')
    update.message.reply_text('QR-код для возвращения')
    context.bot.send_photo(update.message.chat_id, photo=open('created_qr.png', 'rb'))


# Обработка неизвестных команд
def unknown(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('🤖 Извините, я не понимаю эту команду.')

def main() -> None:
    # Создаем объект Updater и передаем ему токен бота
    updater = Updater(TOKEN)

    # Получаем объект диспетчера от updater
    dp = updater.dispatcher

    # Регистрируем обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("createqr", create_qr, pass_args=True))

    # Регистрируем обработчик изображений
    dp.add_handler(MessageHandler(Filters.photo & ~Filters.command, handle_image))

    # Регистрируем обработчик неизвестных команд
    dp.add_handler(MessageHandler(Filters.command, unknown))

    # Запускаем бота
    updater.start_polling()

    # Останавливаем бота, если получен сигнал остановки
    updater.idle()

if __name__ == '__main__':
    main()
