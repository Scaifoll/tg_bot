import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums.chat_member_status import ChatMemberStatus
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_USERNAME = "Scaifoll"  # поменяйте на ваш ник без @
BANNED_NICKS = ["miza", "usik", "d0djer"]

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def is_admin(message: types.Message) -> bool:
    return message.from_user.username == ADMIN_USERNAME

@dp.chat_member()
async def check_new_member(event: types.ChatMemberUpdated):
    user = event.new_chat_member.user
    logging.info(f"Событие: {event.old_chat_member.status} -> {event.new_chat_member.status}, пользователь: {user.first_name} {user.last_name}, username: @{user.username}")

    if (event.new_chat_member.status == ChatMemberStatus.MEMBER and 
        event.old_chat_member.status in {ChatMemberStatus.LEFT, ChatMemberStatus.KICKED}):
        
        display_name = f"{user.first_name or ''} {user.last_name or ''}".strip().lower()
        username = (user.username or "").lower()

        if any(banned in display_name for banned in BANNED_NICKS) or \
           any(banned in username for banned in BANNED_NICKS):
            try:
                await bot.ban_chat_member(event.chat.id, user.id)
                await bot.unban_chat_member(event.chat.id, user.id)
                logging.info(f"Пользователь {display_name} (@{username}) кикнут из чата {event.chat.id}")
            except Exception as e:
                logging.error(f"Ошибка при кике пользователя {display_name}: {e}")

@dp.message(Command("add"))
async def cmd_add(message: types.Message):
    if not is_admin(message):
        await message.reply("Доступ запрещён.")
        return

    args = message.text[len("/add"):].strip().lower()
    if not args:
        await message.reply("Использование:\n/add ник\nДобавляет ник в список запрещённых.")
        return

    if args in BANNED_NICKS:
        await message.reply(f"Ник '{args}' уже есть в списке.")
        return

    BANNED_NICKS.append(args)
    await message.reply(f"Ник '{args}' добавлен в список запрещённых.")

@dp.message(Command("del"))
async def cmd_del(message: types.Message):
    if not is_admin(message):
        await message.reply("Доступ запрещён.")
        return

    args = message.text[len("/del"):].strip().lower()
    if not args:
        await message.reply("Использование:\n/del ник\nУдаляет ник из списка запрещённых.")
        return

    if args not in BANNED_NICKS:
        await message.reply(f"Ника '{args}' нет в списке.")
        return

    BANNED_NICKS.remove(args)
    await message.reply(f"Ник '{args}' удалён из списка запрещённых.")

@dp.message(Command("change"))
async def cmd_change(message: types.Message):
    if not is_admin(message):
        await message.reply("Доступ запрещён.")
        return

    args = message.text[len("/change"):].strip().lower().split(maxsplit=1)
    if len(args) != 2:
        await message.reply("Использование:\n/change старый_ник новый_ник\nИзменяет ник в списке.")
        return

    old_nick, new_nick = args
    if old_nick not in BANNED_NICKS:
        await message.reply(f"Старого ника '{old_nick}' нет в списке.")
        return

    if new_nick in BANNED_NICKS:
        await message.reply(f"Ник '{new_nick}' уже есть в списке.")
        return

    idx = BANNED_NICKS.index(old_nick)
    BANNED_NICKS[idx] = new_nick
    await message.reply(f"Ник '{old_nick}' изменён на '{new_nick}' в списке.")

@dp.message(Command("list"))
async def cmd_list(message: types.Message):
    if not is_admin(message):
        await message.reply("Доступ запрещён.")
        return

    if not BANNED_NICKS:
        await message.reply("Список запрещённых пуст.")
        return

    await message.reply("Список запрещённых ников:\n" + "\n".join(BANNED_NICKS))

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
