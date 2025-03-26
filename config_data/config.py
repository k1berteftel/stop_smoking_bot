from dataclasses import dataclass

from environs import Env

'''
    При необходимости конфиг базы данных или других сторонних сервисов
'''


@dataclass
class tg_bot:
    token: str
    admin_ids: list[int]


@dataclass
class OpenAi:
    token: str


@dataclass
class DB:
    dns: str


@dataclass
class Config:
    bot: tg_bot
    db: DB
    ai: OpenAi


def load_config(path: str | None = None) -> Config:
    env: Env = Env()
    env.read_env(path)

    return Config(
        bot=tg_bot(
            token=env('token'),
            admin_ids=list(map(int, env.list('admins')))
            ),
        db=DB(
            dns=env('dns')
        ),
        ai=OpenAi(
            token=env('ai-token')
        )
    )
