import asyncio
from typing import Literal
from openai import AsyncOpenAI
from config_data.config import Config, load_config
from openai._exceptions import NotFoundError
from pathlib import Path
from dataclasses import dataclass
import json
import httpx

from prompts.funcs import get_current_prompt, get_abstract_prompt


config: Config = load_config()


@dataclass
class SystemMessage:
    role: Literal['user', 'assistant']
    content: str


client = AsyncOpenAI(
    api_key=config.ai.token,
    http_client=httpx.AsyncClient(proxy='http://eAzEJHXk:6WL4egih@109.205.62.47:64856')
)


async def get_answer_by_prompt(prompt: str):
    completion = await client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )
    return completion.choices[0].message.content


async def get_assistant_and_thread(role: str, temperature: float, model: str = 'gpt-4o-mini'):
    """
    :param role: Роль которую будет отыгрывать ИИ.
    :param model: модель чата гпт
    :return: Две str переменной по факту являющиеся уникальными для каждого юзера, чтобы обрабатывать их
        диалог отдельно от других юзеров
    """
    print(role)
    assistant = await client.beta.assistants.create(
        model='gpt-4.1-mini',
        instructions=role if role else None,
        temperature=temperature,
        name="Доктор ИИ.Бросай"
    )

    thread = await client.beta.threads.create()
    return assistant.id, thread.id


async def get_text_answer(text: str, assistant_id: str, thread_id: str) -> str | dict | None:
    """
        Обработка ИИшкой сообщения юзера, возвращает ответ ИИ
    """
    print(assistant_id, thread_id)
    message = await client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=text
    )
    print(message.__dict__)
    run = await client.beta.threads.runs.create_and_poll(
        thread_id=thread_id,
        assistant_id=assistant_id
    )
    info = (f'Стоимость запроса: {run.usage.completion_tokens}\nСтоимость промпта: {run.usage.prompt_tokens}'
            f'\nОбщая стоимость: {run.usage.total_tokens}')
    print(info)
    if run.status == "completed":
        messages = await client.beta.threads.messages.list(thread_id=thread_id)
        #print(messages)

        async for message in messages:
            print(message.content[0].text.value)
            try:
                return json.loads(message.content[0].text.value)
            except Exception as err:
                assistanst = await client.beta.assistants.list()
                await client.beta.threads.messages.create(
                    thread_id=thread_id,
                    role='assistant',
                    content="""Напоминаю, ты ДОЛЖЕН возвращать ответы в строго заданном формате:
{
    "answer": "Твой ответ пользователю",
    "user_status": 1,  # Тут действующий статус пользователя из предложенных
    "jobs": [
        {
            "type": "interval",  # тип задачи, один из типов задач python apscheduler
            "time": "YYYY-MM-DD HH:MM:SS",  # время в которое | через которое должна будет выполниться данная задача
            "description": "Описание задачи"
        },
        ...
    ]
}"""
                )
                print('json error: ', err)
                return message.content[0].text.value
    else:
        return None


async def transfer_context(old_assistant_id: str, thread_id: str, instructions: str, temperature: float) -> str:
    """
    Переносит контекст из одного ассистента в другой.

    :param old_assistant_id: ID старого ассистента.
    :param thread_id: ID потока для переноса контекста.
    """
    thread_messages = client.beta.threads.messages.list(thread_id)
    messages = []

    """
    try:
        async for msg in thread_messages:
            try:
                messages.append(msg.model_dump())
            except Exception as err:
                print(err)
                continue
    except NotFoundError:
        ...
    """

    await client.beta.assistants.delete(assistant_id=old_assistant_id)

    #message = await get_messages_abstract(messages)

    print(instructions)
    new_assistant = await client.beta.assistants.create(
        model="gpt-4.1-mini",
        temperature=temperature,
        instructions=instructions
    )
    #await clear_chat_history(thread_id)

    print('Смена статуса')
    #for message in messages:
        #await client.beta.threads.messages.create(
            #thread_id=thread_id,
            #role=message['role'],
            #content=message["content"][0]['text']['value']
        #)
    return new_assistant.id


async def assistant_messages_abstract(thread_id: str, save_abstract: bool = True):
    thread_messages = client.beta.threads.messages.list(thread_id)

    print(thread_messages)
    messages = []
    try:
        async for msg in thread_messages:
            try:
                messages.append(msg.model_dump())
                await client.beta.threads.messages.delete(
                    message_id=msg.id,
                    thread_id=thread_id
                )
            except Exception as err:
                print(err)
                continue
    except NotFoundError:
        ...
    if save_abstract:
        abstract = messages[-1]
        messages = messages[0:-1:]

    message = await get_messages_abstract(messages)


    await clear_chat_history(thread_id)

    if not save_abstract:
        await client.beta.threads.messages.create(
            thread_id=thread_id,
            role=message.role,
            content=message.content
        )
    else:
        await client.beta.threads.messages.create(
            thread_id=thread_id,
            role=message.role,
            content=abstract["content"][0]['text']['value'] + '\n\n' + message.content
        )
    return message


async def clear_chat_history(thread_id: str):
    thread_messages = client.beta.threads.messages.list(thread_id)

    try:
        async for msg in thread_messages:
            try:
                await client.beta.threads.messages.delete(
                    message_id=msg.id,
                    thread_id=thread_id
                )
            except Exception as err:
                print(err)
                continue
    except NotFoundError:
        ...


async def set_chat_history(thread_id: str):
    await clear_chat_history(thread_id)
    with open('prompts/КонспектГотов.txt', 'r+', encoding='utf-8') as f:
        content = f.read().strip()
    messages = []
    messages.append(
        SystemMessage(
            role='user',
            content=content
        )
    )
    for message in messages:
        await client.beta.threads.messages.create(
            thread_id=thread_id,
            role=message.role,
            content=message.content
        )


async def get_messages_abstract(datas: list[dict]) -> SystemMessage:
    dialog_messages = []
    for data in datas:
        try:
            dialog_messages.append(
                    {
                        "role": "user",
                        "content": json.loads(data["content"][0]['text']['value'])['answer'],
                    },
                )
            print(json.loads(data["content"][0]['text']['value'])['answer'])
        except Exception:
            dialog_messages.append(
                        {
                            "role": "user",
                            "content": data["content"][0]['text']['value'],
                        },
                    )
            print(data["content"][0]['text']['value'])

    print(get_abstract_prompt())
    dialog_messages.append(
        {
            "role": "user",
            "content": get_abstract_prompt(),
        },
    )
    completion = await client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=dialog_messages
    )
    dialog_abstract = completion.choices[0].message.content

    return SystemMessage(
            role='user',
            content=dialog_abstract
        )


async def delete_assistant_and_thread(assistant_id: str, thread_id: str):
    """
        Удаление ассистента и потока (после окончательного завершения диалога с юзером)
    """
    await client.beta.assistants.delete(assistant_id)
    await client.beta.threads.delete(thread_id)


async def _get_chat_history(thread_id):
    thread_messages = client.beta.threads.messages.list(thread_id)
    messages = []
    try:
        async for msg in thread_messages:
            try:
                messages.append(msg.model_dump())
            except Exception as err:
                print(err)
                continue
    except NotFoundError:
        ...

    for message in messages:
        print(message['role'])
        print(message['content'][0]['text']['value'])

