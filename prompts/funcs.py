import json


abstract_prompt = """На основе твоего каждого вопроса теста или анкеты и ответа пользователя, тебе надо составить одно короткое предложение отображающее суть.
Пример 1:
Вопрос: Бросали ли вы курить ранее?
Ответ: да, я не курил месяц. 
Результат, который ты хранишь в конспекте и больше его не исправляешь: «Пользователь бросал курить на месяц.»
Пример 2:
Вопрос: сколько сигарет в день ты выкуриваешь?
Ответ: 15
Результат: пользователь выкуривает 15 сигарет в день. 
Эта часть конспекта в дальнейшем не меняется и может только корректироваться в зависимости от ответов пользователя. 
</instruction>

Сократи диалог до основных тезисов и выводов,сохранив всю важную информацию. Убедись, что в конспекте отражены ключевые моменты, решения, договоренности, результаты тестов и опросов.  Используй нейтральный тон и структурированный формат.
Идентифицируй ключевые моменты диалога исходя из твоей миссии помочь пользователю бросить курить. 
Исключи повторы и детали, которые не влияют на твои решения относительно помощи пользователю с борьбой с зависимостью.
Раздели конспект на логические блоки.
Убедись что все важные моменты сохранены в конспекте диалога.  
            """


json_prompt = """
ТЫ должен пользоваться нынешним системным календарем
Присваивай пользователю следующие статусы в зависимости от достигнутого прогресса:
- Новый(1) — пользователь только начал общение, статус по умолчанию 
- Готов(2) — определена дата отказа, план действий согласован. У тебя готова для пользователя индивидуальная программа. 
- Бросил(3) — пользователь отказался от курения и находится в стадии поддержки. Не выкуривает ни одной сигареты или их аналогов. 
- Срыв(4) — произошел возврат к курению, требуется корректировка плана и проработка причин.
Действующий статус пользователя ты определяешь и отправляешь после каждого запроса.
При изменении статуса пользователя отмечай это для себя и адаптируй подход соответственно. 
ВАЖНО! Возвращай все ответы в формате JSON по четко заданной структуре, вот пример:
{
    "answer": "Твой ответ пользователю",
    "user_status": 1,  # Тут действующий статус пользователя из предложенных
    "jobs": [           # это задачи которые надо будет тебе выполнить через некоторое время
        {
            "type": "interval",  # тип задачи, один из типов задач python apscheduler
            "time": "YYYY-MM-DD HH:MM:SS",  # время в которое | через которое должна будет выполниться данная задача
            "description": "Описание задачи"
        },
        ...
    ]
}
"""


def get_current_prompt(user_status: int):
    if user_status == 1:
        with open('prompts/Новый.txt', 'r+', encoding='utf-8') as f:
            prompt = f.read().strip()
    else:
        with open('prompts/Другое.txt', 'r+', encoding='utf-8') as f:
            prompt = f.read().strip()
    return prompt + '\n\n' + json_prompt