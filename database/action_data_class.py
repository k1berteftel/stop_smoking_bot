from typing import Literal
import datetime
from sqlalchemy import select, insert, update, column, text, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.model import (UsersTable, DeeplinksTable, AdminsTable, OneTimeLinksIdsTable,
                            VouchersTable, UserVouchersTable, BalanceTable, PricesTable, UserAI,
                            TextsTable, ApplicationsTable)
from dateutil.relativedelta import relativedelta


async def configurate_tables(sessions: async_sessionmaker):
    async with sessions() as session:
        await session.execute(insert(PricesTable))
        await session.execute(insert(TextsTable))
        await session.commit()


class DataInteraction():
    def __init__(self, session: async_sessionmaker):
        self._sessions = session

    async def check_user(self, user_id: int) -> bool:
        async with self._sessions() as session:
            result = await session.scalar(select(UsersTable).where(UsersTable.user_id == user_id))
        return True if result else False

    async def check_voucher(self, user_id: int, voucher: str) -> bool:
        async with self._sessions() as session:
            result = await session.scalar(select(VouchersTable).where(VouchersTable.code == voucher))
            print('result 1:', result)
            if not result:
                return False
            result = await session.scalar(select(UserVouchersTable).where(
                and_(
                    UserVouchersTable.user_id == user_id,
                    UserVouchersTable.code == voucher
                )
            ))
            print('result 2:', result)
            if result:
                return False
            await session.execute(insert(UserVouchersTable).values(
                user_id=user_id,
                code=voucher
            ))
            await session.execute(update(VouchersTable).where(VouchersTable.code == voucher).values(
                inputs=VouchersTable.inputs + 1
            ))
            await session.commit()
            return True

    async def add_application(self, user_id: int, amount: int) -> bool:
        if await self.get_application(user_id):
            return False
        async with self._sessions() as session:
            await session.execute(insert(ApplicationsTable).values(
                user_id=user_id,
                amount=amount
            ))
            await session.commit()
        return True

    async def add_refs(self, user_id: int):
        async with self._sessions() as session:
            await session.execute(update(UsersTable).where(UsersTable.user_id == user_id).values(
                refs=UsersTable.refs + 1,
            ))
            await session.commit()

    async def add_sub_refs(self, user_id: int):
        async with self._sessions() as session:
            await session.execute(update(UsersTable).where(UsersTable.user_id == user_id).values(
                refs=UsersTable.sub_refs + 1,
            ))
            await session.commit()

    async def add_user(self, user_id: int, username: str, name: str,
                       referral: int | None, sub_referral: int | None, join: str | None):
        if await self.check_user(user_id):
            return
        async with self._sessions() as session:
            await session.execute(insert(UsersTable).values(
                user_id=user_id,
                username=username,
                name=name,
                referral=referral,
                sub_referral=sub_referral,
                join=join
            ))
            model = BalanceTable(
                user_id=user_id,
            )
            session.add(model)
            await session.commit()

    async def add_user_ai(self, user_id: int):
        async with self._sessions() as session:
            user = await self.get_user(user_id)
            user_ai = UserAI(
                user_id=user_id
            )
            user.AI = user_ai
            session.add(user_ai)
            await session.commit()

    async def add_deeplink(self, name: str, link: str):
        async with self._sessions() as session:
            await session.execute(insert(DeeplinksTable).values(
                name=name,
                link=link
            ))
            await session.commit()

    async def add_entry(self, link: str):
        async with self._sessions() as session:
            await session.execute(update(DeeplinksTable).where(DeeplinksTable.link == link).values(
                entry=DeeplinksTable.entry+1
            ))
            await session.commit()

    async def add_admin(self, user_id: int, name: str):
        async with self._sessions() as session:
            await session.execute(insert(AdminsTable).values(
                user_id=user_id,
                name=name
            ))
            await session.commit()

    async def add_link(self, link: str):
        async with self._sessions() as session:
            await session.execute(insert(OneTimeLinksIdsTable).values(
                link=link
            ))
            await session.commit()

    async def add_voucher(self, code: str, amount: int):
        async with self._sessions() as session:
            await session.execute(insert(VouchersTable).values(
                code=code,
                amount=amount
            ))
            await session.commit()

    async def get_application(self, user_id: int):
        async with self._sessions() as session:
            result = await session.scalar(select(ApplicationsTable).where(ApplicationsTable.user_id == user_id))
        return result

    async def get_user_ai(self, user_id: int):
        async with self._sessions() as session:
            result = await session.scalar(select(UserAI).where(UserAI.user_id == user_id))
        if not result:
            await self.add_user_ai(user_id)
            async with self._sessions() as session:
                result = await session.scalar(select(UserAI).where(UserAI.user_id == user_id))
        return result

    async def get_voucher_amount(self, code: str):
        async with self._sessions() as session:
            result = await session.scalar(select(VouchersTable.amount).where(VouchersTable.code == code))
        return result

    async def get_vouchers(self):
        async with self._sessions() as session:
            result = await session.scalars(select(VouchersTable))
        return result

    async def get_deeplinks(self):
        async with self._sessions() as session:
            result = await session.scalars(select(DeeplinksTable))
        return result.fetchall()

    async def get_user(self, user_id: int):
        async with self._sessions() as session:
            result = await session.scalar(select(UsersTable).where(UsersTable.user_id == user_id))
        return result

    async def get_user_by_username(self, username: str):
        async with self._sessions() as session:
            result = await session.scalar(select(UsersTable).where(UsersTable.username == username))
        return result

    async def get_users_by_join_link(self, deeplink: str):
        async with self._sessions() as session:
            result = await session.scalars(select(UsersTable).where(UsersTable.join == deeplink))
        return result.fetchall()

    async def get_users(self):
        async with self._sessions() as session:
            result = await session.scalars(select(UsersTable))
        return result.fetchall()

    async def get_user_refs(self, user_id: int):
        async with self._sessions() as session:
            result = await session.scalars(select(UsersTable).where(UsersTable.referral == user_id))
        return result.fetchall()

    async def get_links(self):
        async with self._sessions() as session:
            result = await session.scalars(select(OneTimeLinksIdsTable))
        return result.fetchall()

    async def get_admins(self):
        async with self._sessions() as session:
            result = await session.scalars(select(AdminsTable))
        return result.fetchall()

    async def get_prices(self):
        async with self._sessions() as session:
            result = await session.scalar(select(PricesTable).where(PricesTable.id == 1))
        return result

    async def get_text(self, column: str):
        async with self._sessions() as session:
            result = await session.scalar(select(text(column)).where(TextsTable.id == 1))
        return result

    async def get_texts(self):
        async with self._sessions() as session:
            result = await session.scalar(select(TextsTable).where(TextsTable.id == 1))
        return result

    async def update_user_sub(self, user_id: int):
        async with self._sessions() as session:
            await session.execute(update(UsersTable).where(UsersTable.user_id == user_id).values(
                sub=True
            ))
            await session.commit()

    async def update_user_balance(self, user_id: int, amount: int, type: Literal['rub', 'usdt', 'ton']):
        async with self._sessions() as session:
            if type == 'rub':
                await session.execute(update(BalanceTable).where(BalanceTable.user_id == user_id).values(
                    rub=BalanceTable.rub + amount
                ))
            if type == 'usdt':
                await session.execute(update(BalanceTable).where(BalanceTable.user_id == user_id).values(
                    rub=BalanceTable.usdt + amount
                ))
            if type == 'ton':
                await session.execute(update(BalanceTable).where(BalanceTable.user_id == user_id).values(
                    rub=BalanceTable.ton + amount
                ))
            await session.commit()

    async def set_sub_end(self, user_id: int, months: int | None):
        user = await self.get_user(user_id)
        async with self._sessions() as session:
            if months is None:
                await session.execute(update(UsersTable).where(UsersTable.user_id == user_id).values(
                    sub_end=None,
                    sub=False
                ))
                await session.commit()
                return
            if user.sub_end:
                await session.execute(update(UsersTable).where(UsersTable.user_id == user_id).values(
                    sub_end=UsersTable.sub_end + relativedelta(months=months)
                ))
            else:
                await session.execute(update(UsersTable).where(UsersTable.user_id == user_id).values(
                    sub_end=datetime.datetime.today() + relativedelta(months=months),
                    sub=True
                ))
            await session.commit()

    async def set_locale(self, user_id: int, locale: str):
        async with self._sessions() as session:
            await session.execute(update(UsersTable).where(UsersTable.user_id == user_id).values(
                locale=locale
            ))
            await session.commit()

    async def set_user_ai_data(self, user_id: int, **kwargs):
        async with self._sessions() as session:
            await session.execute(update(UserAI).where(UserAI.user_id == user_id).values(
                kwargs
            ))
            await session.commit()

    async def set_active(self, user_id: int, active: int):
        async with self._sessions() as session:
            await session.execute(update(UsersTable).where(UsersTable.user_id == user_id).values(
                active=active
            ))
            await session.commit()

    async def set_activity(self, user_id: int):
        async with self._sessions() as session:
            await session.execute(update(UsersTable).where(UsersTable.user_id == user_id).values(
                activity=datetime.datetime.today()
            ))
            await session.commit()

    async def set_prices(self, **kwargs):
        async with self._sessions() as session:
            await session.execute(update(PricesTable).values(
                kwargs
            ))
            await session.commit()

    async def set_texts(self, **kwargs):
        async with self._sessions() as session:
            await session.execute(update(TextsTable).values(
                kwargs
            ))
            await session.commit()

    async def set_paid_referral(self, user_id: int):
        async with self._sessions() as session:
            await session.execute(update(UsersTable).where(UsersTable.user_id == user_id).values(
                paid_referral=True
            ))
            await session.commit()

    async def del_deeplink(self, link: str):
        async with self._sessions() as session:
            await session.execute(delete(DeeplinksTable).where(DeeplinksTable.link == link))
            await session.commit()

    async def del_link(self, link_id: str):
        async with self._sessions() as session:
            await session.execute(delete(OneTimeLinksIdsTable).where(OneTimeLinksIdsTable.link == link_id))
            await session.commit()

    async def del_admin(self, user_id: int):
        async with self._sessions() as session:
            await session.execute(delete(AdminsTable).where(AdminsTable.user_id == user_id))
            await session.commit()

    async def del_voucher(self, id: int):
        async with self._sessions() as session:
            await session.execute(delete(VouchersTable).where(VouchersTable.id == id))
            await session.commit()

    async def del_user(self, user_id: int):
        async with self._sessions() as session:
            await session.execute(delete(UsersTable).where(UsersTable.user_id == user_id))
            await session.commit()

    async def del_application(self, user_id: int):
        async with self._sessions() as session:
            await session.execute(delete(ApplicationsTable).where(ApplicationsTable.user_id == user_id))
            await session.commit()