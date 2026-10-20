import os
import json
# Берём весь код агента из соседнего файла (консольный диалог там не запустится: он под if __name__)
from agent import *

# Ссылки на вакансии: тестовые значения
VACANCY_URL_RU = "https://hh.ru/vacancy/138624337"
VACANCY_URL_EN = "https://hh.ru/vacancy/138624337"
BAD_URL = "https://hh.ru/vacancy/000000000000"

# Тестовые кейсы: язык, сообщения пользователя по порядку, какой action ждем в конце и что проверить глазами.
# Уточняющие вопросы GigaChat может задавать по-разному, поэтому в сообщениях сразу даны подробные ответы.
TEST_CASES = [
    # ---------- Русский ----------
    {
        "name": "RU-1. Полный профиль одним сообщением, потом ссылка",
        "language": "ru",
        "messages": [
            "Меня зовут Анна Смирнова, телефон +7 900 123-45-67, anna@mail.ru, Москва. "
            "Учусь на 3 курсе ВШЭ, факультет компьютерных наук, программа ПМИ, окончание в 2028. "
            "Летом 2025 стажировалась тестировщиком в Яндексе (июнь - август): писала автотесты на Python, нашла 30 багов. "
            "Знаю Python, SQL, Git, английский B2. Призёр олимпиады по информатике 2023, курс Karpov.Courses по SQL. "
            "Хочу стажировку аналитика данных.",
            VACANCY_URL_RU,
            "Всё указано, добавить нечего.",
        ],
        "expected": "resume_ready",
        "check": "Все разделы на месте, 30 багов и олимпиада перенесены без преувеличений",
    },
    {
        "name": "RU-2. Неполный профиль, агент задаёт вопросы",
        "language": "ru",
        "messages": [
            "Привет, я Надя, закончила бизнес-аналитику, хочу быть стажёром аналитиком",
            "Telegram @nadiafed, Москва. Стажёр в X5, январь - ноябрь 2025, собирала отчёты и следила за качеством данных. "
            "Навыки: Python, SQL, BPMN. Достижений нет.",
            "Федорова Надежда, НИТУ МИСИС, бакалавриат, 2026. В X5 сделала отчёты по рекламной аналитике для 40 конкурентов.",
            VACANCY_URL_RU,
        ],
        "expected": "resume_ready",
        "check": "После 1-го сообщения вопросы про контакты, опыт, навыки, достижения; раздела 'Достижения' в резюме нет",
    },
    {
        "name": "RU-3. Нет опыта работы",
        "language": "ru",
        "messages": [
            "Иван Петров, ivan@gmail.com, Казань. Учусь в КФУ на 2 курсе, прикладная информатика, окончание 2029. "
            "Опыта работы нет. Знаю Python и Excel. Достижений нет. Ищу первую стажировку в аналитике.",
            "Учебный проект: бот для расписания на Python, 2025.",
            VACANCY_URL_RU,
        ],
        "expected": "resume_ready",
        "check": "Нет слов 'Нет опыта' и 'Отсутствует'; учебный проект может быть в опыте или достижениях",
    },
    {
        "name": "RU-4. Сначала ссылка, потом рассказ о себе",
        "language": "ru",
        "messages": [
            VACANCY_URL_RU,
            "Мария Козлова, @mkozlova, Санкт-Петербург. СПбГУ, экономика, 4 курс, окончание 2027. "
            "Стажёр-аналитик в Сбере, сентябрь 2025 - январь 2026: дашборды в Power BI, автоматизация отчётов на Python. "
            "Навыки: SQL, Python, Power BI, английский C1. Сертификат Яндекс Практикума по анализу данных. Хочу в аналитику.",
            "Всё указано.",
        ],
        "expected": "resume_ready",
        "check": "После ссылки бот пишет 'Вакансия сохранена' и задаёт вопросы про профиль; vacancy_id сохраняется",
    },
    {
        "name": "RU-5. Ссылка и текст в одном сообщении",
        "language": "ru",
        "messages": [
            "Вот вакансия " + VACANCY_URL_RU + " . Я Олег Иванов, @olegiv, Москва, МФТИ, 3 курс, ПМФ, окончание 2028. "
            "Опыта нет. Знаю C++, Python, SQL. Финалист Всеросса по информатике. Хочу стажировку аналитиком.",
            "Всё указано.",
        ],
        "expected": "resume_ready",
        "check": "Ссылка не попала в профиль, вакансия сохранена с первого сообщения",
    },
    {
        "name": "RU-6. Нерабочая ссылка",
        "language": "ru",
        "messages": [
            "Павел Сидоров, @psid, Москва. МГУ, ВМК, 4 курс, 2027. Опыта нет. Python, SQL. Достижений нет. Хочу в аналитику.",
            "Всё указано.",
            BAD_URL,
        ],
        "expected": "need_link",
        "check": "Бот пишет 'Не получилось прочитать вакансию' и снова просит ссылку, программа не падает",
    },
    # ---------- English ----------
    {
        "name": "EN-1. Full profile in English",
        "language": "en",
        "messages": [
            "My name is John Smith, john.smith@gmail.com, London. I study Computer Science at UCL, 3rd year, graduating in 2027. "
            "Data analyst intern at Revolut, June - September 2025: built SQL reports and a churn dashboard in Tableau, cut reporting time by 20%. "
            "Skills: Python, SQL, Tableau, Git. Languages: English native, Spanish B1. Kaggle bronze medal 2024. "
            "I am looking for a data analyst internship.",
            VACANCY_URL_EN,
            "Nothing to add.",
        ],
        "expected": "resume_ready",
        "check": "Questions and resume in English, section names in English, 20% kept",
    },
    {
        "name": "EN-2. Incomplete profile, agent asks follow-ups",
        "language": "en",
        "messages": [
            "Hi, I'm Emma, I studied economics and want an analyst internship.",
            "Telegram @emma_b, Berlin. Marketing intern at Zalando, 2025, did some reports. Skills: Excel, SQL. No achievements.",
            "Emma Brown, Humboldt University of Berlin, BSc Economics, 2026. At Zalando (March - August 2025) I analysed campaign data for 15 markets.",
            VACANCY_URL_EN,
        ],
        "expected": "resume_ready",
        "check": "Follow-up questions in English; no 'Achievements' section",
    },
    {
        "name": "EN-3. Russian-language profile, English resume",
        "language": "en",
        "messages": [
            "Меня зовут Дмитрий Орлов, @dorlov, Новосибирск. НГУ, математика, 4 курс, окончание 2027. "
            "Аналитик-стажёр в 2ГИС, июль - декабрь 2025: A/B-тесты, SQL-запросы. Python, SQL, английский B2. "
            "Победитель хакатона ЦФТ 2024. Хочу стажировку аналитиком.",
            "Всё указано.",
            VACANCY_URL_EN,
        ],
        "expected": "resume_ready",
        "check": "Resume fully in English, name in Latin letters (Dmitry Orlov), companies not translated",
    },
]

def run_case(case, user_id):
    """Прогоняет один диалог и печатает ответы бота."""
    print("=" * 70)
    print(case["name"])
    state = {"user_id": user_id, "language": case["language"], "vacancy_id": ""}
    result = {"action": ""}
    for message in case["messages"]:
        print("\nПользователь:", message)
        state["message"] = message
        try:
            result = nadya_agent(state)
            state["vacancy_id"] = result["vacancy_id"]
            print(f"[action: {result['action']}]")
            print("Бот:", result["response"])
        except Exception as e:
            print("Ошибка:", e)
            result = {"action": "error"}
    passed = result["action"] == case["expected"]
    print(f"\nОжидали: {case['expected']}, получили: {result['action']} -> {'OK' if passed else 'ПРОВЕРИТЬ'}")
    print("Проверить глазами:", case["check"])
    return passed

if __name__ == "__main__":
    # тесты начинаются с чистых JSON
    for file_name in [USERS_FILE, VACANCIES_FILE, RESUMES_FILE]:
        if os.path.exists(file_name):
            os.remove(file_name)
    results = []
    for i, case in enumerate(TEST_CASES):
        # у каждого кейса свой пользователь, чтобы профили не смешивались
        results.append((case["name"], run_case(case, user_id=1000 + i)))
    print("=" * 70)
    print("Итог:")
    for name, passed in results:
        print("OK       " if passed else "ПРОВЕРИТЬ", name)
