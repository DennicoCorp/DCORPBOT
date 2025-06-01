import sqlite3
import logging

# Настройка логирования для этого модуля
logger = logging.getLogger(__name__)

DB_NAME = 'bot_database.db' # Имя файла вашей базы данных

def initialize_database():
    """
    Инициализирует базу данных SQLite и создает таблицы, если они еще не существуют.
    """
    try:
        # Подключаемся к БД (если файла нет, он будет создан)
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # Создаем таблицу 'users'
        # przechowuje informacje o użytkownikach Telegramu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,    -- Уникальный ID пользователя Telegram
                username TEXT,                      -- Username пользователя (может быть None)
                first_name TEXT,                    -- Имя пользователя
                last_name TEXT,                     -- Фамилия пользователя (может быть None)
                registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Дата и время регистрации в боте
            )
        ''')
        logger.info("Таблица 'users' проверена/создана.")

        # Создаем таблицу 'subscriptions'
        # przechowuje informacje o subskrypcjach użytkowników
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                subscription_id INTEGER PRIMARY KEY AUTOINCREMENT, -- Уникальный ID подписки
                telegram_id INTEGER NOT NULL,                 -- ID пользователя, которому принадлежит подписка
                start_date TIMESTAMP,                         -- Дата начала подписки
                end_date TIMESTAMP,                           -- Дата окончания подписки
                is_active BOOLEAN DEFAULT 0,                  -- Активна ли подписка (0 - нет, 1 - да)
                plan_name TEXT,                               -- Название тарифного плана (например, 'месячный', 'годовой')
                payment_id TEXT,                              -- ID платежа из платежной системы (опционально)
                FOREIGN KEY (telegram_id) REFERENCES users (telegram_id) -- Связь с таблицей users
            )
        ''')
        logger.info("Таблица 'subscriptions' проверена/создана.")

        # Сохраняем изменения
        conn.commit()

    except sqlite3.Error as e:
        logger.error(f"Ошибка SQLite при инициализации базы данных: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Неожиданная ошибка при инициализации базы данных: {e}", exc_info=True)
    finally:
        if 'conn' in locals() and conn:
            conn.close() # Всегда закрываем соединение
            logger.debug(f"Соединение с БД '{DB_NAME}' закрыто после инициализации.")

# Этот блок выполнится, если запустить database.py напрямую (python database.py)
# Используется для первоначального создания БД или для тестов.
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.info("Запуск инициализации базы данных из database.py...")
    initialize_database()
    logger.info("Инициализация базы данных завершена.")