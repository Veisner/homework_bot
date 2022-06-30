import os
import time
import logging
import telegram
import requests
from logging import StreamHandler
from dotenv import load_dotenv


load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600    # частота отправки запросов в секундах
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = StreamHandler()
logger.addHandler(handler)

formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
)

handler.setFormatter(formatter)


def send_message(bot, message):
    """Отправка сообщения об изменившемся статусе."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
        )
        logger.info('Сообщение отправлено')
    except Exception as error:
        logger.error(f'Сообщение не отправлено, ошибка - {error}')


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
    if not isinstance(response, dict):
        raise TypeError('Ошибка в типе ответа API')
    if 'homeworks' not in response:
        raise KeyError('Ключ "homework" отсутствует в словаре')
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        raise TypeError('Homeworks не является списком')
    # print(homeworks)
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
    if (homework_name or homework_status) is None:
        raise ValueError('Не найдено значение')
    if homework_status not in HOMEWORK_VERDICTS:
        logger.error(f'Неизвестный статус {homework_status} домашней работы')
        raise Exception(f'Неизвестный статус работы - {homework_status}')
    verdict = HOMEWORK_VERDICTS[homework_status]
    message = f'Изменился статус проверки работы "{homework_name}". {verdict}'
    return message


def check_tokens():
    """Проверка наличия обязательных токенов."""
    if all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]):
        return True
    return False


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    homework_time = 1650000000
    current_timestamp = homework_time
    STATUS = ''
    if not check_tokens():
        logger.critical('Отсутствие обязательных переменных')
        raise Exception('Отсутствие обязательных переменных')
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            new_status = parse_status(homework)
            if new_status != STATUS:
                send_message(bot, new_status)
                if STATUS != '':
                    current_timestamp = int(time.time())
                STATUS = new_status
            else:
                logger.debug('Статус не поменялся')

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            send_message(bot, message)

        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        filename='program.log',
        format='%(asctime)s, %(levelname)s, %(message)s'
    )
    main()
