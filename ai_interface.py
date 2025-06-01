import logging
import google.generativeai as genai

try:
    from config import GEMINI_API_KEY
except ImportError:
    print("Ключ GEMINI_API_KEY не найден в config.py!")
    GEMINI_API_KEY = None

logger = logging.getLogger(__name__)

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        logger.info("Google Generative AI SDK успешно сконфигурирован.")
    except Exception as e:
        logger.error(f"Ошибка при конфигурации Google Generative AI SDK: {e}")
        exit()
else:
    logger.warning("GEMINI_API_KEY не предоставлен. Функционал Gemini будет недоступен.")

def get_gemini_response(user_prompt: str) -> str | None:
    if not GEMINI_API_KEY:
        error_message = "API ключ для Gemini не настроен. Обратитесь к администратору."
        logger.error(error_message)
        return error_message

    try:
        model = genai.GenerativeModel('gemini-pro')

        response = model.generate_content(user_prompt)

        if response.parts:
            full_response_text = "".join(part.text for part in response.parts if hasattr(part, 'text'))
            if full_response_text:
                logger.info(f"Получен ответ от Gemini для промпта: '{user_prompt[:50]}...'")
                return full_response_text.strip()
            else:
                logger.warning(
                    f"Ответ Gemini на промпт '{user_prompt[:50]}...' не содержит текстовых частей (возможно, заблокирован по безопасности или пустой). Full response: {response}")
                finish_reason_message = ""
                if hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
                    finish_reason_message = f" Причина: {response.prompt_feedback.block_reason_message or response.prompt_feedback.block_reason}."
                elif hasattr(response, 'candidates') and response.candidates and response.candidates[0].finish_reason:
                    finish_reason_message = f" Причина завершения: {response.candidates[0].finish_reason.name}."

                return f"Не удалось получить содержательный ответ от нейросети.{finish_reason_message} Попробуйте переформулировать запрос."

        else:
            logger.warning(
                f"Ответ Gemini на промпт '{user_prompt[:50]}...' не содержит атрибута 'parts' или он пуст. Full response: {response}")
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
                block_reason_message = response.prompt_feedback.block_reason_message or response.prompt_feedback.block_reason
                logger.warning(f"Промпт заблокирован по причине: {block_reason_message}")
                return f"Ваш запрос был заблокирован по соображениям безопасности: {block_reason_message}. Пожалуйста, измените запрос."
            return "Нейросеть вернула пустой ответ. Попробуйте переформулировать запрос."

    except Exception as e:
        logger.error(f"Произошла ошибка при взаимодействии с Gemini API: {e}", exc_info=True)
        return "Произошла ошибка при обращении к нейросети. Пожалуйста, попробуйте позже."

if __name__ == '__main__':
    if not GEMINI_API_KEY:
        print("Для тестового запуска установите GEMINI_API_KEY в config.py")
    else:
        logging.basicConfig(level=logging.INFO)
        test_prompt = "Привет, Gemini! Как твои дела?"
        print(f"Отправляем тестовый промпт: {test_prompt}")
        response = get_gemini_response(test_prompt)
        print(f"\nОтвет от Gemini:\n{response}")

        print("-" * 20)
        test_prompt_2 = "Расскажи короткую смешную историю про кота и пылесос."
        print(f"Отправляем тестовый промпт: {test_prompt_2}")
        response_2 = get_gemini_response(test_prompt_2)
        print(f"\nОтвет от Gemini:\n{response_2}")