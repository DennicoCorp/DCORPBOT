import sqlite3
import logging
import datetime

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


def add_or_update_user(telegram_id: int, username: str | None, first_name: str | None, last_name: str | None):
    """
    Добавляет нового пользователя в таблицу 'users' или обновляет его данные,
    если пользователь с таким telegram_id уже существует.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # Используем INSERT OR REPLACE или INSERT ON CONFLICT для атомарной операции
        # INSERT OR REPLACE: если запись существует, она удаляется и вставляется новая.
        # INSERT ... ON CONFLICT(telegram_id) DO UPDATE SET ...: если конфликт по telegram_id, обновляем поля.
        # Второй вариант предпочтительнее, т.к. не удаляет старую запись и может сохранить registration_date.

        # Мы будем использовать INSERT ... ON CONFLICT
        # registration_date будет установлен только при первой вставке благодаря DEFAULT CURRENT_TIMESTAMP
        # При обновлении registration_date не будет меняться.
        cursor.execute('''
                       INSERT INTO users (telegram_id, username, first_name, last_name)
                       VALUES (?, ?, ?, ?) ON CONFLICT(telegram_id) DO
                       UPDATE SET
                           username = excluded.username,
                           first_name = excluded.first_name,
                           last_name = excluded.last_name
                       -- registration_date не обновляем, он остается от первой вставки
                       ''', (telegram_id, username, first_name, last_name))

        conn.commit()
        logger.info(f"Пользователь ID: {telegram_id}, Username: {username} был добавлен/обновлен в БД.")

    except sqlite3.Error as e:
        logger.error(f"Ошибка SQLite при добавлении/обновлении пользователя ID {telegram_id}: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Неожиданная ошибка при добавлении/обновлении пользователя ID {telegram_id}: {e}", exc_info=True)
    finally:
        if 'conn' in locals() and conn:
            conn.close()


def add_user_subscription(telegram_id: int, duration_days: int, plan_name: str = "Тестовый доступ"):
    """
    Добавляет или обновляет подписку для пользователя.
    Если у пользователя уже есть активная подписка, можно решить, как поступать:
    продлевать существующую, заменять на новую, или не делать ничего.
    Пока что для простоты будем добавлять новую или заменять существующую активную, если она от того же плана.
    Либо, если есть активная, можно просто продлить end_date.
    Для начала, сделаем так: если есть активная, просто продлим ее. Если нет - создадим новую.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        now = datetime.datetime.now()

        # Проверяем, есть ли уже активная подписка у этого пользователя
        cursor.execute('''
                       SELECT subscription_id, end_date
                       FROM subscriptions
                       WHERE telegram_id = ?
                         AND is_active = 1
                         AND end_date > ?
                       ORDER BY end_date DESC LIMIT 1
                       ''', (telegram_id, now))
        active_subscription = cursor.fetchone()

        if active_subscription:
            # Если есть активная подписка, продлеваем ее
            sub_id, current_end_date_str = active_subscription
            current_end_date = datetime.datetime.fromisoformat(current_end_date_str)  # Преобразуем строку в datetime
            new_end_date = current_end_date + datetime.timedelta(days=duration_days)
            cursor.execute('''
                           UPDATE subscriptions
                           SET end_date  = ?,
                               plan_name = ?
                           WHERE subscription_id = ?
                           ''', (new_end_date, plan_name + " (продлено)", sub_id))
            logger.info(f"Подписка ID {sub_id} для пользователя {telegram_id} продлена до {new_end_date}.")
        else:
            # Если активной подписки нет, создаем новую
            start_date = now
            end_date = start_date + datetime.timedelta(days=duration_days)
            cursor.execute('''
                           INSERT INTO subscriptions (telegram_id, start_date, end_date, is_active, plan_name)
                           VALUES (?, ?, ?, 1, ?)
                           ''', (telegram_id, start_date, end_date, plan_name))
            logger.info(
                f"Новая подписка '{plan_name}' на {duration_days} дней добавлена для пользователя {telegram_id} до {end_date}.")

        conn.commit()
        return True  # Возвращаем True в случае успеха

    except sqlite3.Error as e:
        logger.error(f"Ошибка SQLite при добавлении/продлении подписки для пользователя ID {telegram_id}: {e}",
                     exc_info=True)
        return False  # Возвращаем False в случае ошибки
    except Exception as e:
        logger.error(f"Неожиданная ошибка при добавлении/продлении подписки для ID {telegram_id}: {e}", exc_info=True)
        return False
    finally:
        if 'conn' in locals() and conn:
            conn.close()


def check_user_subscription(telegram_id: int) -> bool:
    """
    Проверяет, есть ли у пользователя активная и не истекшая подписка.
    Возвращает True, если активная подписка есть, иначе False.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        now = datetime.datetime.now()  # Текущее время

        # Выбираем активные подписки, у которых дата окончания еще не наступила
        cursor.execute('''
                       SELECT 1
                       FROM subscriptions
                       WHERE telegram_id = ?
                         AND is_active = 1
                         AND end_date > ? LIMIT 1
                       ''', (telegram_id, now))

        result = cursor.fetchone()  # fetchone() вернет (1,) если найдена запись, или None

        if result:
            logger.debug(f"У пользователя ID {telegram_id} найдена активная подписка.")
            return True
        else:
            logger.debug(f"Активная подписка для пользователя ID {telegram_id} не найдена или истекла.")
            return False

    except sqlite3.Error as e:
        logger.error(f"Ошибка SQLite при проверке подписки для пользователя ID {telegram_id}: {e}", exc_info=True)
        return False  # В случае ошибки считаем, что подписки нет
    except Exception as e:
        logger.error(f"Неожиданная ошибка при проверке подписки для ID {telegram_id}: {e}", exc_info=True)
        return False
    finally:
        if 'conn' in locals() and conn:
            conn.close()


# Этот блок выполнится, если запустить database.py напрямую (python database.py)
# Используется для первоначального создания БД или для тестов.
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.info("Запуск инициализации базы данных из database.py...")
    initialize_database()
    logger.info("Инициализация базы данных завершена.")