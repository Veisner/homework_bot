import os
import time
import logging
#import telegram
import requests
from logging import StreamHandler
from dotenv import load_dotenv

from telegram import Bot

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    level=logging.DEBUG,
    filename='program.log',
    format='%(asctime)s, %(levelname)s, %(message)s'
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = StreamHandler()
logger.addHandler(handler)

formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
)

handler.setFormatter(formatter)

def send_message(bot, message):
    """Отправка сообщения об изменившемся статусе """
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
        )
        logger.info('Сообщение отправлено')
    except Exception:
        logger.error('Сообщение не отправлено')

def get_api_answer(current_timestamp):
    """Делает запрос к API, ответ приводит к типам данных Python."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=params
        )
        logger.info('Запрос на сервер отправлен')
    except Exception:
        logger.error('Запрос на сервер не отправлен')
    if response.status_code != 200:
        raise logger.error('Не удалось получить ответ API'
                           f'error-status: {response.status_code}')
    try:
        return response.json()
    except Exception:
        raise logger.error('Ответ от сервера в неверном формате')

def check_response(response):
    """Проверяет ответ API на корректность."""
    if type(response) != dict:
        raise TypeError('Ошибка в типе ответа API')
    if 'homeworks' not in response:
        raise KeyError('Ключ "homework" отсутствует в словаре')
    homeworks = response['homeworks']
    if type(homeworks) != list:
        raise TypeError('Homeworks не является списком')
    return homeworks[0]

def parse_status(homework):
    """Извлекается информацию о статусе работы."""
    if len(homework) == 0:
        logger.debug('Отсутствует проверенная работа')
        return False
    if 'homework_name' not in homework:
        raise KeyError('В ответе API отсутсвует ключ homework_name')
    if 'status' not in homework:
        raise KeyError('В ответе API отсутсвует ключ status')
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_name or homework_status is None:
        raise ValueError('Не найдено значение')
    if homework_status not in HOMEWORK_STATUSES:
        logger.error(f'Неизвестный статус {homework_status} домашней работы')
        raise Exception(f'Неизвестный статус работы - {homework_status}')
    verdict = HOMEWORK_STATUSES[homework_status]
    message = f'Изменился статус проверки работы "{homework_name}". {verdict}'
    return message

def check_tokens():
    if not all(PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID):
        logger.critical('Отсутствие обязательных переменных')
        return False
    return True

def main():
    """Основная логика работы бота."""
#    homework_statuses = requests.get(url=ENDPOINT, headers=HEADERS, params=get_api_answer(current_timestamp))

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    message = ''
    if not check_tokens():
        raise Exception('Отсутствие обязательных переменных')
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            homework = homeworks[0]
            new_status = parse_status(homework)
            if message != new_status:
                message = new_status
                send_message(bot, message)
            else:
                logger.debug('Статус не поменялся')
            current_timestamp = int(time.time())
           
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            send_message(bot, message)

        time.sleep(RETRY_TIME)

if __name__ == '__main__':
    main()
