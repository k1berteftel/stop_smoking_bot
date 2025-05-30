import json


json_prompt = """
Пользуйся Unix временем, не смей допускать ошибку в нынешних датах и времени когда говоришь за время или у тебя за него спрашивают
Присваивай пользователю следующие статусы в зависимости от достигнутого прогресса:
- Новый(1) — пользователь только начал общение, статус по умолчанию 
- Готов(2) — определена дата отказа, план действий согласован. У тебя готова для пользователя индивидуальная программа. 
- Бросил(3) — пользователь отказался от курения и находится в стадии поддержки. Не выкуривает ни одной сигареты или их аналогов. 
- Срыв(4) — если после статуса БРОСИЛ произошел возврат к курению, требуется корректировка плана и проработка причин.
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


def get_abstract_prompt() -> str:
    with open('prompts/Конспект.txt', 'r+', encoding='utf-8') as f:
        prompt = f.read().strip()
    return prompt


def get_current_prompt(user_status: int):
    if user_status == 1:
        with open('prompts/Новый.txt', 'r+', encoding='utf-8') as f:
            prompt = f.read().strip()
    else:
        with open('prompts/Другое.txt', 'r+', encoding='utf-8') as f:
            prompt = f.read().strip()
    return prompt + '\n\n' + json_prompt