import asyncio
import logging
import json
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums.chat_member_status import ChatMemberStatus
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_USERNAMES = ["Scaifoll", "D0DJERyyy", "mizasol"]

BANNED_FILE = "banned_nicks.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def load_banned_nicks():
    if os.path.isfile(BANNED_FILE):
        with open(BANNED_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Если в файле одна строка с переносами, разделим её по строкам
            if len(data) == 1 and '\n' in data[0]:
                return [nick.strip().lower() for nick in data[0].split('\n') if nick.strip()]
            # Если уже корректный список - норм
            return [nick.lower() for nick in data]
    else:
        with open(BANNED_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
        return []


BANNED_NICKS = load_banned_nicks()

def is_admin(message: types.Message) -> bool:
    username = (message.from_user.username or "").lower()
    return username in [u.lower() for u in ADMIN_USERNAMES]

@dp.chat_member()
async def check_new_member(event: types.ChatMemberUpdated):
    user = event.new_chat_member.user
    if (event.new_chat_member.status == ChatMemberStatus.MEMBER and 
        event.old_chat_member.status in {ChatMemberStatus.LEFT, ChatMemberStatus.KICKED}):
        logging.info(f"Новый участник: {user.id} @{user.username} {user.full_name} в чате {event.chat.id}")
        await validate_user(event.chat.id, user)

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    logging.info(f"Команда /help от @{message.from_user.username} ({message.from_user.first_name}) [{message.from_user.id})")
    if not is_admin(message):
        logging.warning(f"Доступ запрещён @{message.from_user.username} ({message.from_user.first_name}) [{message.from_user.id}) на /help")
        await message.reply("Доступ запрещён.")
        return

    help_text = (
        "Доступные команды:\n"
        "/add <ник> — добавить ник в список запрещённых\n"
        "/del <ник> — удалить ник из списка\n"
        "/change <старый_ник> <новый_ник> — изменить ник в списке\n"
        "/list — показать список запрещённых ников\n"
        "/help — показать эту справку"
    )
    await message.reply(help_text)

async def validate_user(chat_id, user: types.User):
    display_name = f"{user.first_name or ''} {user.last_name or ''}".strip().lower()
    username = (user.username or "").lower()

    if any(banned in display_name for banned in BANNED_NICKS) or any(banned in username for banned in BANNED_NICKS):
        try:
            await bot.ban_chat_member(chat_id, user.id)
            await bot.unban_chat_member(chat_id, user.id)
            logging.info(f"Кик пользователя {user.id} @{username} ({display_name}) из чата {chat_id}")
        except Exception as e:
            logging.error(f"Ошибка при кике пользователя {user.id} @{username}: {e}")

@dp.message(Command("add"))
async def cmd_add(message: types.Message):
    logging.info(f"Команда /add от @{message.from_user.username} ({message.from_user.first_name}) [{message.from_user.id})")
    if not is_admin(message):
        logging.warning(f"Доступ запрещён @{message.from_user.username} на /add")
        await message.reply("Доступ запрещён.")
        return

    args = message.text[len("/add"):].strip().lower()
    if not args:
        await message.reply("Использование:\n/add ник")
        return

    if args in BANNED_NICKS:
        await message.reply(f"Ник '{args}' уже в списке.")
        return

    BANNED_NICKS.append(args)
    save_banned_nicks(BANNED_NICKS)
    await message.reply(f"Ник '{args}' добавлен.")

@dp.message(Command("del"))
async def cmd_del(message: types.Message):
    logging.info(f"Команда /del от @{message.from_user.username} ({message.from_user.first_name}) [{message.from_user.id}")
    if not is_admin(message):
        logging.warning(f"Доступ запрещён @{message.from_user.username} на /del")
        await message.reply("Доступ запрещён.")
        return

    args = message.text[len("/del"):].strip().lower()
    if not args:
        await message.reply("Использование:\n/del ник")
        return

    if args not in BANNED_NICKS:
        await message.reply(f"Ник '{args}' не найден.")
        return

    BANNED_NICKS.remove(args)
    save_banned_nicks(BANNED_NICKS)
    await message.reply(f"Ник '{args}' удалён.")

@dp.message(Command("change"))
async def cmd_change(message: types.Message):
    logging.info(f"Команда /change от @{message.from_user.username} ({message.from_user.first_name}) [{message.from_user.id})")
    if not is_admin(message):
        logging.warning(f"Доступ запрещён @{message.from_user.username} на /change")
        await message.reply("Доступ запрещён.")
        return

    args = message.text[len("/change"):].strip().lower().split(maxsplit=1)
    if len(args) != 2:
        await message.reply("Использование:\n/change старый_ник новый_ник")
        return

    old_nick, new_nick = args
    if old_nick not in BANNED_NICKS:
        await message.reply(f"Ник '{old_nick}' не найден.")
        return

    if new_nick in BANNED_NICKS:
        await message.reply(f"Ник '{new_nick}' уже есть.")
        return

    idx = BANNED_NICKS.index(old_nick)
    BANNED_NICKS[idx] = new_nick
    save_banned_nicks(BANNED_NICKS)
    await message.reply(f"Ник '{old_nick}' изменён на '{new_nick}'.")

@dp.message(Command("list"))
async def cmd_list(message: types.Message):
    logging.info(f"Команда /list от @{message.from_user.username} ({message.from_user.first_name}) [{message.from_user.id})")
    if not is_admin(message):
        logging.warning(f"Доступ запрещён @{message.from_user.username} на /list")
        await message.reply("Доступ запрещён.")
        return

    if not BANNED_NICKS:
        await message.reply("Список пуст.")
        return

    await message.reply("Список запрещённых ников:\n" + "\n".join(BANNED_NICKS))

@dp.message()
async def check_message(message: types.Message):
    if message.text and message.text.startswith("/"):
        return
    logging.info(f"Сообщение от @{message.from_user.username} ({message.from_user.first_name}) [{message.from_user.id}) в чате {message.chat.id}: {message.text}")
    await validate_user(message.chat.id, message.from_user)

async def main():
    logging.info("Запуск бота")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
