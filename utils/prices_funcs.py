import re
import asyncio
from aiohttp import ClientSession
from bs4 import BeautifulSoup
import lxml


async def get_usdt_rub() -> float:
    async with ClientSession() as session:
        async with session.get('https://www.rbc.ru/crypto/currency/usdtrub') as res:
            resp = await res.text()
            soup = BeautifulSoup(resp, 'lxml')
            price = soup.find('div', class_='chart__subtitle').text.strip()
            value = re.search(r'\d+,\d+', price)
            return float(price[value.start():value.end():].replace(',', '.'))