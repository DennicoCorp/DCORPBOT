import logging
from openai import OpenAI  # Импортируем OpenAI клиент

# Импортируем настройки из config.py
try:
    from config import NEURO_API_BASE_URL, NEURO_MODEL_NAME, NEURO_API_KEY
except ImportError:
    print("Переменные NEURO_API_BASE_URL, NEURO_MODEL_NAME, NEURO_API_KEY не найдены в config.py!")
    NEURO_API_BASE_URL = None
    NEURO_MODEL_NAME = None
    NEURO_API_KEY = "NA"  # Ставим значение по умолчанию, если ключ не нужен

# Настройка логирования для этого модуля
logger = logging.getLogger(__name__)

# Инициализируем OpenAI клиент
# Он будет использоваться для всех запросов к вашему локальному серверу
if NEURO_API_BASE_URL and NEURO_MODEL_NAME:
    try:
        # Если ваш сервер не требует API ключа, можно передать фиктивный ключ,
        # например, "NA", "None", или любой другой непустой, если библиотека этого требует.
        # Некоторые серверы (как Ollama по умолчанию) игнорируют ключ.
        # OpenAI v1.x клиент требует чтобы api_key был не None, если передается.
        # Если ключ реально нужен, он должен быть правильным.
        client = OpenAI(
            base_url=NEURO_API_BASE_URL,
            api_key=NEURO_API_KEY if NEURO_API_KEY and NEURO_API_KEY.strip() and NEURO_API_KEY.lower() != "na" else "sk-dummy-key-for-local"
        )
        logger.info(f"OpenAI клиент успешно сконфигурирован для URL: {NEURO_API_BASE_URL} и модели: {NEURO_MODEL_NAME}")
    except Exception as e:
        logger.error(f"Ошибка при конфигурации OpenAI клиента: {e}")
        client = None  # Устанавливаем в None, чтобы функция ниже корректно обработала ошибку
else:
    logger.warning("NEURO_API_BASE_URL или NEURO_MODEL_NAME не предоставлены. Функционал нейросети будет недоступен.")
    client = None


def get_custom_ai_response(user_prompt: str, temperature: float = 0.7, max_tokens: int = 1024) -> str | None:
    """
    Отправляет запрос к вашему локальному/self-hosted OpenAI-совместимому API
    и возвращает текстовый ответ.
    Возвращает None или сообщение об ошибке в случае неудачи.
    """
    if not client:
        error_message = "Клиент для работы с нейросетью не инициализирован. Проверьте конфигурацию."
        logger.error(error_message)
        return error_message

    try:
        logger.info(f"Отправка запроса к модели {NEURO_MODEL_NAME} с промптом: '{user_prompt[:70]}...'")

        completion = client.chat.completions.create(
            model=NEURO_MODEL_NAME,
            messages=[
                {"role": "user", "content": user_prompt}
                # Можно добавить системный промпт:
                # {"role": "system", "content": "Ты полезный ассистент."}
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            # stream=False # Для простоты пока без стриминга
        )

        response_text = completion.choices[0].message.content

        if response_text:
            logger.info(f"Получен ответ от модели {NEURO_MODEL_NAME}.")
            return response_text.strip()
        else:
            logger.warning(f"Модель {NEURO_MODEL_NAME} вернула пустой ответ на промпт '{user_prompt[:70]}...'.")
            return "Нейросеть вернула пустой ответ. Попробуйте переформулировать запрос."

    except Exception as e:  # Ловим более общие ошибки openai.APIError или requests.exceptions.ConnectionError
        logger.error(
            f"Произошла ошибка при взаимодействии с API нейросети ({NEURO_MODEL_NAME}): {type(e).__name__} - {e}",
            exc_info=True)
        if "Connection refused" in str(e) or "Failed to resolve" in str(e):
            return "Не удалось подключиться к серверу нейросети. Убедитесь, что он запущен и URL указан верно."
        return "Произошла ошибка при обращении к нейросети. Пожалуйста, попробуйте позже."


# --- Тестовый запуск функции (можно раскомментировать для проверки) ---
if __name__ == '__main__':
    if not NEURO_API_BASE_URL or not NEURO_MODEL_NAME:
        print("Для тестового запуска установите NEURO_API_BASE_URL и NEURO_MODEL_NAME в config.py")
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        test_prompt_1 = "Привет! Кто ты и что умеешь?"
        print(f"\nОтправляем тестовый промпт 1: {test_prompt_1}")
        response_1 = get_custom_ai_response(test_prompt_1)
        print(f"Ответ:\n{response_1}")

        print("-" * 30)

        test_prompt_2 = "Напиши короткий Python скрипт для вывода чисел от 1 до 5."
        print(f"Отправляем тестовый промпт 2: {test_prompt_2}")
        response_2 = get_custom_ai_response(test_prompt_2)
        print(f"Ответ:\n{response_2}")