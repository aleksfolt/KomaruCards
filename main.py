import json
import random
import time
import os
import logging
from os import path
from datetime import datetime, timedelta
from telebot.async_telebot import AsyncTeleBot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import aiohttp
import asyncio
import telebot
from aiocryptopay import AioCryptoPay, Networks
import aiofiles
import emoji

crypto = AioCryptoPay(token='205872:AAN4Wj4SoVxVqtjBhfnXqQ1POMYCANkAuV8', network=Networks.MAIN_NET)
bot = AsyncTeleBot("7409912773:AAH6zKcL5S0hAyLfr5KcUQC0bRgYtmEsxg0")


async def config_func():
    with open('config.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data


if not path.exists("premium_users.json"):
    with open("premium_users.json", 'w') as f:
        json.dump({}, f)

if not path.exists("komaru_user_cards.json"):
    with open("komaru_user_cards.json", 'w') as f:
        json.dump({}, f)

user_button = {}


async def load_data_cards():
    try:
        with open("komaru_user_cards.json", 'r') as f:
            return json.load(f)
    except Exception as e:
        print(e)
        return {}


async def save_data(data):
    try:
        with open("komaru_user_cards.json", 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(e)

async def get_titul(card_count):
    if card_count > 500:
        return "Мастер карточек"
    elif card_count > 250:
        return "Коллекционер"
    elif card_count > 150:
        return 'Эксперт карточек'
    elif card_count > 100:
        return 'Продвинутый коллекционер'
    elif card_count > 50:
        return 'Любитель Комару'
    elif card_count > 20:
        return 'Начинающий коллекционер'
    else:
        return 'Новичок'

async def user_profile(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name or ""
    data = await load_data_cards()
    user_data = data.get(str(user_id), {'cats': [], 'last_usage': 0, 'points': 0, 'nickname': first_name, 'card_count': 0})
    card_count = user_data.get('card_count', 0)
    titul = await get_titul(card_count)

    collected_cards = len(user_data['cats'])
    total_cards = len(cats)

    premium_status, premium_expiration = await check_and_update_premium_status(user_id)
    premium_message = f"Премиум: активен до {premium_expiration}" if premium_status else "Премиум: не активен"

    try:
        user_profile_photos = await bot.get_user_profile_photos(user_id, limit=1)
        if user_profile_photos.photos:
            photo = user_profile_photos.photos[0][-1]
            file_id = photo.file_id

            current_datetime = message.date
            user_folder = os.path.join('path_to_save', f'user_{user_id}', str(current_datetime))
            os.makedirs(user_folder, exist_ok=True)

            downloaded_file_path = os.path.join(user_folder, f'{user_id}_profile_pic.jpg')
            file_info = await bot.get_file(file_id)
            with open(downloaded_file_path, 'wb') as new_file:
                new_file.write(await bot.download_file(file_info.file_path))
        else:
            downloaded_file_path = 'avatar.jpg'

        caption = (
            f"Привет {user_data['nickname']}!\n\n"
            f"🏡 Твой профиль:\n"
            f"🃏 Собрано {collected_cards} из {total_cards} карточек\n"
            f"💰 Очки: {user_data['points']}\n"
            f"🎖️ Титул: {titul}\n"
            f"🌟 {premium_message}"
        )
        unique_number = random.randint(1000, 1000000000000000000000)
        user_button[user_id] = unique_number
        keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
        button_1 = telebot.types.InlineKeyboardButton(text="Мои карточки", callback_data=f'show_cards_{unique_number}')
        button_2 = telebot.types.InlineKeyboardButton(text="Топ карточек", callback_data=f'top_komaru_{unique_number}')
        button_3 = telebot.types.InlineKeyboardButton(text="Премиум", callback_data=f'premium_callback_{unique_number}')
        keyboard.add(button_1, button_2, button_3)
        await bot.send_photo(message.chat.id, photo=open(downloaded_file_path, 'rb'), caption=caption, reply_markup=keyboard)
    except telebot.apihelper.ApiException as e:
        if "bot was blocked by the user" in str(e):
            await bot.send_message(message.chat.id, "Пожалуйста, разблокируйте бота для доступа к вашему профилю.")
        else:
            await bot.send_message(message.chat.id, "Произошла ошибка при доступе к вашему профилю. Попробуйте позже.")



async def komaru_cards_function(message):
    user_id = str(message.from_user.id)
    user_nickname = message.from_user.first_name
    await register_user_and_group_async(message)

    data = await load_data_cards()
    user_data = data.get(user_id, {'cats': [], 'last_usage': 0, 'points': 0, 'nickname': user_nickname, 'card_count': 0})
    
    if 'card_count' not in user_data:
        user_data['card_count'] = 0
        
    user_data['points'] = int(user_data['points'])
    time_since_last_usage = time.time() - user_data['last_usage']

    premium_status, _ = await check_and_update_premium_status(user_id)
    wait_time = 14400 if not premium_status else 10800

    if time_since_last_usage < wait_time:
        remaining_time = wait_time - time_since_last_usage
        remaining_hours = int(remaining_time // 3600)
        remaining_minutes = int((remaining_time % 3600) // 60)
        remaining_seconds = int(remaining_time % 60)
        await bot.reply_to(message,
                           f"Вы осмотрелись, но не увидели рядом ни одного Комару. Попробуйте еще раз через {remaining_hours} часов {remaining_minutes} минут {remaining_seconds} секунд.")
        return

    random_number = random.randint(1, 95)
    if premium_status:
        if 0 <= random_number <= 19:
            eligible_cats = [cat for cat in cats if cat["rarity"] == "Легендарная"]
        elif 20 <= random_number <= 34:
            eligible_cats = [cat for cat in cats if cat["rarity"] == "Мифическая"]
    else:
        if 0 <= random_number <= 14:
            eligible_cats = [cat for cat in cats if cat["rarity"] == "Легендарная"]
        elif 15 <= random_number <= 29:
            eligible_cats = [cat for cat in cats if cat["rarity"] == "Мифическая"]

    if 30 <= random_number <= 49:
        eligible_cats = [cat for cat in cats if cat["rarity"] == "Сверхредкая"]
    elif 50 <= random_number <= 95:
        eligible_cats = [cat for cat in cats if cat["rarity"] == "Редкая"]

    if eligible_cats:
        chosen_cat = random.choice(eligible_cats)
        photo_data = chosen_cat['photo']
        if chosen_cat['name'] in user_data['cats']:
            await bot.send_photo(message.chat.id, photo_data,
                                 caption=f"Вы осмотрелись вокруг и снова увидели {chosen_cat['name']}! Будут начислены только очки.\nРедкость: {chosen_cat['rarity']}\n+{chosen_cat['points']} очков.\n\nВсего поинтов: {user_data['points'] + int(chosen_cat['points'])}")
            user_data['points'] += int(chosen_cat['points'])
        else:
            await bot.send_photo(message.chat.id, photo_data,
                                 caption=f"Вы осмотрелись вокруг и увидели {chosen_cat['name']}!\nРедкость: {chosen_cat['rarity']}\nОчки: {chosen_cat['points']}\n\nВсего поинтов: {user_data['points'] + int(chosen_cat['points'])}")
            user_data['cats'].append(chosen_cat['name'])
            user_data['points'] += int(chosen_cat['points'])
            user_data['card_count'] += 1 
        user_data['last_usage'] = time.time()
        data[user_id] = user_data
        await save_data(data)


@bot.callback_query_handler(func=lambda call: call.data.startswith('show_cards'))
async def show_knock_cards(call):
    user_id = str(call.from_user.id)
    user_id_notstr = call.from_user.id
    user_nickname = call.from_user.first_name
    unique_number = int(call.data.split('_')[-1])
    if user_button.get(user_id_notstr) != unique_number:
        await bot.answer_callback_query(call.id, "Не ваша кнопка.", show_alert=True)
        return
    data = await load_data_cards()
    user_data = data.get(user_id, {'cats': [], 'last_usage': 0, 'points': 0, 'nickname': user_nickname, 'card_count': 0})
    collected_cards = len(user_data['cats'])
    total_cards = len(cats)
    if user_data['cats']:
        cats_owned_by_user = {cat['name'] for cat in cats if cat['name'] in user_data['cats']}
        rarities = {cat['rarity'] for cat in cats if cat['name'] in cats_owned_by_user}
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        for rarity in rarities:
            keyboard.add(types.InlineKeyboardButton(text=rarity, callback_data=f'show_{rarity}'))
        try:
            await bot.send_message(call.from_user.id,
                                   f"У вас собрано {collected_cards} из {total_cards} возможных\nВыберите редкость:",
                                   reply_markup=keyboard)
            chat_type = call.message.chat.type
            if chat_type in ['group', 'supergroup']:
                await bot.send_message(call.message.chat.id,
                                       f"{call.from_user.first_name}, карточки отправлены вам в личные сообщения!")
            else:
                pass
        except telebot.apihelper.ApiException as e:
            logging.error(f"Не удалось отправить сообщение: {str(e)}")
            await bot.send_message(call.message.chat.id,
                                   "Напишите боту что-то в личные сообщения, чтобы отправить вам карточки!")
    else:
        await bot.send_message(call.message.chat.id, "Вы пока что не наблюдали за птичками.")


@bot.callback_query_handler(func=lambda call: call.data.startswith('show_'))
async def show_cards(call):
    rarity = call.data[len('show_'):]
    user_id = str(call.from_user.id)
    user_nickname = call.from_user.first_name
    data = await load_data_cards()
    user_data = data.get(user_id, {'cats': [], 'last_usage': 0, 'points': 0, 'nickname': user_nickname, 'card_count': 0})
    rarity_cards = [cat for cat in cats if cat['name'] in user_data['cats'] and cat['rarity'] == rarity]

    if rarity_cards:
        for cat in rarity_cards:
            photo_data = cat['photo']
            caption = f"{cat['name']}\nРедкость: {cat['rarity']}"
            if 'points' in cat:
                caption += f"\nОчки: {cat['points']}"
            chat_type = call.message.chat.type
            await bot.send_photo(call.message.chat.id, photo_data, caption=caption)
    else:
        await bot.send_message(call.message.chat.id, f"У вас нет карточек редкости {rarity}")


@bot.callback_query_handler(func=lambda call: call.data.startswith('top_komaru'))
async def top_komaru(call):
    user_id = call.from_user.id
    unique_number = int(call.data.split('_')[-1])
    if user_button.get(user_id) != unique_number:
        await bot.answer_callback_query(call.id, "Не ваша кнопка.", show_alert=True)
        return
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
    button_1 = telebot.types.InlineKeyboardButton(text="Топ по карточкам", callback_data=f'top_cards_cards')
    button_2 = telebot.types.InlineKeyboardButton(text="Топ по очкам", callback_data=f'top_cards_point')
    keyboard.add(button_1, button_2)
    await bot.send_message(call.message.chat.id, "Топ 10 пользователей по карточкам. Выберите кнопку:",
                           reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data.startswith('top_cards_'))
async def cards_top_callback(call):
    choice = call.data.split('_')[2]
    data = await load_data_cards()
    user_id = str(call.from_user.id)
    message_text = ""

    if choice == "cards":
        sorted_data = sorted(data.items(), key=lambda x: len(x[1].get('cats', [])), reverse=True)
        top_10 = sorted_data[:10]

        message_text = "Топ-10 пользователей по количеству собранных карточек:\n\n"
        for i, (user_id, user_data) in enumerate(top_10, 1):
            nickname = user_data.get('nickname', 'Unknown')
            num_cards = len(user_data.get('cats', []))
            premium_status, _ = await check_and_update_premium_status(user_id)
            premium_icon = "💎" if premium_status else ""
            message_text += f"{i}. {premium_icon} {nickname}: {num_cards} карточек\n"

    elif choice == "point":
        sorted_data_points = sorted(data.items(), key=lambda x: x[1].get('points', 0), reverse=True)
        top_10 = sorted_data_points[:10]

        message_text = "Топ-10 пользователей по количеству набранных очков:\n\n"
        for j, (user_id, user_data) in enumerate(top_10, 1):
            nickname_2 = user_data.get('nickname', 'Unknown')
            points = user_data.get('points', 0)
            premium_status, _ = await check_and_update_premium_status(user_id)
            premium_icon = "💎" if premium_status else ""
            message_text += f"{j}. {premium_icon} {nickname_2}: {points} очков\n"

    if not message_text:
        message_text = "Не удалось получить данные. Попробуйте позже."

    await bot.delete_message(call.message.chat.id, call.message.message_id)
    await bot.send_message(call.message.chat.id, message_text)


def registr(s):
    for i in range(len(s)):
        if s[i].isupper():
            s = s[:i] + s[i].lower() + s[i + 1:]
    return s


async def start(message):
    if message.chat.type == 'private':
        markup = types.InlineKeyboardMarkup()
        add_bot_button = types.InlineKeyboardButton(text="Добавить бота в группу",
                                                    url=f"https://t.me/KomaruCardsBot?startgroup=iris&admin=change_info+restrict_members+delete_messages+pin_messages+invite_users")
        markup.add(add_bot_button)
        await bot.send_message(message.chat.id, (
            "👋 Добро пожаловать в бота Komaru!\n\n"
            '''Здесь вы можете собирать карточки комару и соревноватся с другими игроками.\nЧтобы начать получать карточки напиши "<code>Комару</code>"\n'''
            "Используйте /help для получения дополнительной информации.\n\n"
            "➡️ Нажмите кнопку ниже, чтобы добавить бота в группу:"
        ), parse_mode='HTML', reply_markup=markup)
    elif message.chat.type in ['group', 'supergroup']:
        await bot.send_message(message.chat.id, (
            "👋 Komaru бот готов к работе!\n\n"
            '''Здесь вы можете собирать карточки комару и соревноватся с другими игроками.\nЧтобы начать получать карточки напиши "<code>Комару</code>"\n\n'''
            "Используйте /help для получения информации о командах."
        ), parse_mode='HTML')


async def help(message):
    help_text = (
        "<b>Komaru Bot</b> - Ваш помощник в сборе карточек комару\n\n"
        "<b>Доступные команды:</b>\n"
        "/start - Начать работу с ботом\n"
        "/help - Получить помощь\n"
        "/profile, 'профиль', 'комару профиль' - Посмотреть свой профиль\n"
        "'сменить ник &lt;ник&gt;' - Смена ника в профиле.\n"
        "'комару', 'получить карту', 'камар' - Искать котов и собирать карточки\n"
    )
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    button1 = InlineKeyboardButton(text="Пользовательское соглашение", url="https://telegra.ph/Polzovatelskoe-soglashenie-06-17-6")
    button2 = InlineKeyboardButton(text="Наш канал", url="t.me/komaru_updates")
    keyboard.add(button1, button2)
    
    await bot.send_message(message.chat.id, help_text, parse_mode='HTML', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data.startswith('premium_callback'))
async def buy_premium(call):
    sender_id = call.from_user.id
    unique_number = int(call.data.split('_')[-1])

    if user_button.get(sender_id) != unique_number:
        await bot.answer_callback_query(call.id, "Не ваша кнопка.", show_alert=True)
        return

    try:
        if call.message.chat.type == "private":
            invoice = await create_and_send_invoice(sender_id)
            if not invoice:
                await bot.send_message(sender_id, "Не удалось создать инвойс.")
        else:
            invoice = await create_and_send_invoice(sender_id, is_group=True, message=call.message)
            if not invoice:
                await bot.answer_callback_query(call.id, "Пожалуйста, напишите боту что-то в личные сообщения.", show_alert=True)
    except Exception as e:
        print(e)


async def create_and_send_invoice(sender_id, is_group=False, message=None):
    try:
        invoice = await crypto.create_invoice(asset='USDT', amount=0.5)
        if not invoice:
            response = "Ошибка при создании инвойса. Попробуйте позже."
            if is_group:
                pass
            await bot.send_message(sender_id, response)
            return None

        markup = types.InlineKeyboardMarkup()
        pay_button = types.InlineKeyboardButton(text="Оплатить", url=invoice.bot_invoice_url)
        paid_button = types.InlineKeyboardButton(text="Я оплатил", callback_data=f"verify_payment_{sender_id}_{invoice.invoice_id}")
        markup.add(pay_button, paid_button)

        response = (
            f"🔓 Что даст тебе Комару премиум?\n\n"
            f"⌛️ Возможность получать карточки каждые 3 часа вместо 4\n"
            f"🃏 Повышенная вероятность выпадения легендарных, эпических и мифических карт\n"
            f"🌐 Возможность использовать смайлики в никнейме"
            f"💎 Отображение алмаза в топе карточек\n"
            f"🔄 Более быстрая обработка твоих сообщений\n"
            f"🗓️ Срок действия 30 дней\n\n"
            f"Премиум активируется после подтверждения оплаты. Реквизиты: {invoice.bot_invoice_url}"
        )
        if is_group:
            await bot.send_message(message.chat.id, "Реквизиты для оплаты отправлены в личные сообщения.")
            await bot.send_message(sender_id, response, reply_markup=markup)
        else:
            await bot.send_message(sender_id, response, reply_markup=markup)

        return invoice
    except Exception as e:
        error_message = f"Ошибка при создании инвойса: {e}"
        if is_group:
            await bot.send_message(message.chat.id, "Пожалуйста, напишите что-то боту в личные сообщения.")
        await bot.send_message(sender_id, error_message)
        return None


@bot.callback_query_handler(func=lambda call: call.data.startswith('verify_payment'))
async def verify_payment(call):
    parts = call.data.split('_')
    if len(parts) < 4:
        await bot.send_message(call.message.chat.id, "Ошибка в данных платежа.")
        return

    action, context, sender_id, invoice = parts[0], parts[1], parts[2], parts[3]

    try:
        print("Invoice ID:", invoice)
        payment_status = await get_invoice_status(invoice)
        if payment_status == 'paid':
            await activate_premium(sender_id)
            await bot.send_message(sender_id,
                                   "🌟 Спасибо за покупку Премиума! Наслаждайтесь эксклюзивными преимуществами.")
            await bot.delete_message(call.message.chat.id, call.message.message_id)
        else:
            await bot.send_message(sender_id, "Оплата не прошла! Попробуйте еще раз.")
    except Exception as e:
        await bot.send_message(sender_id, f"Произошла ошибка при проверке статуса платежа: {str(e)}")


async def get_invoice_status(invoice_id):
    try:
        print(invoice_id)
        invoice = await crypto.get_invoices(invoice_ids=int(invoice_id))
        return invoice.status
    except Exception as e:
        print(f"Ошибка при получении данных инвойса: {e}")
        return None


async def activate_premium(sender_id):
    premium_duration = timedelta(days=30)
    expiration_date = datetime.now() + premium_duration
    with open('premium_users.json', 'r+') as file:
        data = json.load(file)
        data[str(sender_id)] = expiration_date.strftime('%Y-%m-%d')
        file.seek(0)
        json.dump(data, file)
        file.truncate()


async def check_and_update_premium_status(user_id):
    with open('premium_users.json', 'r') as file:
        premium_users = json.load(file)

    if str(user_id) in premium_users:
        expiration_date = datetime.strptime(premium_users[str(user_id)], '%Y-%m-%d')
        if expiration_date > datetime.now():
            return True, expiration_date.strftime('%Y-%m-%d')
        else:
            del premium_users[str(user_id)]
            with open('premium_users.json', 'w') as file:
                json.dump(premium_users, file)
            return False, None
    else:
        return False, None


async def register_user_and_group_async(message):
    chat_type = message.chat.type
    update_data = {}

    if chat_type == 'private':
        user_info = {
            "user_id": message.from_user.id,
            "username": message.from_user.username or "",
            "first_name": message.from_user.first_name or ""
        }
        user_key = str(message.from_user.id)
        update_data['users'] = {user_key: user_info}

    if chat_type in ['group', 'supergroup']:
        group_info = {
            "group_id": message.chat.id,
            "title": message.chat.title
        }
        group_key = str(message.chat.id)
        update_data['groups'] = {group_key: group_info}

    try:
        async with aiofiles.open("user_group_data.json", "r") as file:
            data = await file.read()
            data = json.loads(data)
    except FileNotFoundError:
        data = {"users": {}, "groups": {}}

    updated = False
    for section, items in update_data.items():
        for key, info in items.items():
            if key not in data[section]:
                data[section][key] = info
                updated = True
    if updated:
        async with aiofiles.open("user_group_data.json", "w") as file:
            await file.write(json.dumps(data, indent=4))


async def admin_panel(message):
    if message.chat.type == 'private' and message.from_user.id in [1130692453, 1268026433]:
        markup = types.InlineKeyboardMarkup()
        stats_button = types.InlineKeyboardButton(text="Стата пользователей", callback_data="user_stats")
        issue_premium_button = types.InlineKeyboardButton(text="Выдать премиум", callback_data="issue_premium")
        reset_stats_button = types.InlineKeyboardButton(text="Обнулить статистику", callback_data="reset_stats")
        revoke_premium_button = types.InlineKeyboardButton(text="Забрать премиум", callback_data="revoke_premium")
        group_broadcast_button = types.InlineKeyboardButton(text="Рассылка группы", callback_data="group_broadcast")
        private_msg_broadcast_button = types.InlineKeyboardButton(text="Рассылка ЛС",
                                                                  callback_data="private_msg_broadcast")
        markup.add(stats_button, issue_premium_button, reset_stats_button, revoke_premium_button,
                   group_broadcast_button, private_msg_broadcast_button)
        await bot.send_message(message.chat.id, "Админ панель:", reply_markup=markup)
    else:
        await bot.send_message(message.chat.id, "У вас нет доступа к этой команде.")


user_state = {}
user_data = {}


@bot.message_handler(
    func=lambda message: message.text and user_state.get(message.from_user.id) in [
        'awaiting_user_id_for_premium',
        'awaiting_user_id_for_reset',
        'awaiting_user_id_for_revoke',
        'awaiting_broadcast_message_to_groups',
        'awaiting_broadcast_message_to_users'
    ]
)
async def handle_user_input(message):
    user_id = message.from_user.id
    state = user_state[user_id]
    input_text = message.text.strip()

    if state == 'awaiting_user_id_for_premium':
        await activate_premium(input_text)
        await bot.send_message(message.chat.id, "Премиум выдан.")
        del user_state[user_id]

    elif state == 'awaiting_user_id_for_reset':
        with open('komaru_user_cards.json', 'r+') as file:
            data = json.load(file)
            if input_text in data:
                del data[input_text]
                file.seek(0)
                json.dump(data, file, indent=4)
                file.truncate()
        await bot.send_message(message.chat.id, "Статистика пользователя обнулена.")
        del user_state[user_id]

    elif state == 'awaiting_user_id_for_revoke':
        with open('premium_users.json', 'r+') as file:
            data = json.load(file)
            if input_text in data:
                del data[input_text]
                file.seek(0)
                json.dump(data, file, indent=4)
                file.truncate()
        await bot.send_message(message.chat.id, "Премиум статус пользователя забран.")
        del user_state[user_id]

    elif state == 'awaiting_broadcast_message_to_groups':
        try:
            async with aiofiles.open("user_group_data.json", "r") as file:
                data = await file.read()
                groups = json.loads(data)['groups']
                for group_id in groups:
                    await bot.send_message(group_id, input_text)
            await bot.send_message(message.chat.id, "Сообщение успешно разослано по группам.")
        except Exception as e:
            await bot.send_message(message.chat.id, f"Ошибка при рассылке: {str(e)}")
        del user_state[user_id]

    elif state == 'awaiting_broadcast_message_to_users':
        try:
            async with aiofiles.open("user_group_data.json", "r") as file:
                data = await file.read()
                users = json.loads(data)['users']
                for user_id in users:
                    await bot.send_message(user_id, input_text)
            await bot.send_message(message.chat.id, "Сообщение успешно разослано пользователям в ЛС.")
        except Exception as e:
            await bot.send_message(message.chat.id, f"Ошибка при рассылке: {str(e)}")
        del user_state[user_id]


@bot.callback_query_handler(func=lambda call: call.data.startswith('issue_premium'))
async def issue_premium(call):
    if call.from_user.id in [1130692453, 1268026433]:
        user_state[call.from_user.id] = 'awaiting_user_id_for_premium'
        await bot.send_message(call.message.chat.id, "Введите ID пользователя для выдачи премиума:")
    else:
        await bot.answer_callback_query(call.id, "Не ваша кнопка.", show_alert=True)


@bot.callback_query_handler(func=lambda call: call.data.startswith('reset_stats'))
async def reset_stats(call):
    if call.from_user.id in [1130692453, 1268026433]:
        user_state[call.from_user.id] = 'awaiting_user_id_for_reset'
        await bot.send_message(call.message.chat.id, "Введите ID пользователя для обнуления статистики:")
    else:
        await bot.answer_callback_query(call.id, "Не ваша кнопка.", show_alert=True)


@bot.callback_query_handler(func=lambda call: call.data.startswith('revoke_premium'))
async def revoke_premium(call):
    if call.from_user.id in [1130692453, 1268026433]:
        user_state[call.from_user.id] = 'awaiting_user_id_for_revoke'
        await bot.send_message(call.message.chat.id, "Введите ID пользователя для удаления премиума:")
    else:
        await bot.answer_callback_query(call.id, "Не ваша кнопка.", show_alert=True)


@bot.callback_query_handler(func=lambda call: call.data.startswith('user_stats'))
async def send_user_stats(call):
    if call.from_user.id in [1130692453, 1268026433]:
        with open('user_group_data.json', 'rb') as file:
            await bot.send_document(call.message.chat.id, file)
    else:
        await bot.answer_callback_query(call.id, "Не ваша кнопка.", show_alert=True)


@bot.callback_query_handler(func=lambda call: call.data == 'group_broadcast')
async def initiate_group_broadcast(call):
    if call.from_user.id in [1130692453, 1268026433]:
        user_state[call.from_user.id] = 'awaiting_broadcast_message_to_groups'
        await bot.send_message(call.message.chat.id, "Введите сообщение для рассылки по группам:")
    else:
        await bot.answer_callback_query(call.id, "Не ваша кнопка.", show_alert=True)


@bot.callback_query_handler(func=lambda call: call.data == 'private_msg_broadcast')
async def initiate_private_msg_broadcast(call):
    if call.from_user.id in [1130692453, 1268026433]:
        user_state[call.from_user.id] = 'awaiting_broadcast_message_to_users'
        await bot.send_message(call.message.chat.id, "Введите сообщение для рассылки в ЛС:")
    else:
        await bot.answer_callback_query(call.id, "Не ваша кнопка.", show_alert=True)


@bot.message_handler(
    func=lambda message: user_state.get(message.from_user.id) in ['awaiting_broadcast_message_to_groups',
                                                                  'awaiting_broadcast_message_to_users'])
async def process_broadcast_message(message):
    broadcast_message = message.text
    if user_state[message.from_user.id] == 'awaiting_broadcast_message_to_groups':
        try:
            async with aiofiles.open("user_group_data.json", "r") as file:
                data = await file.read()
                groups = json.loads(data)['groups']
                for group_id in groups:
                    await bot.send_message(group_id, broadcast_message)
            await bot.send_message(message.chat.id, "Сообщение успешно разослано по группам.")
        except Exception as e:
            await bot.send_message(message.chat.id, f"Ошибка при рассылке: {str(e)}")
    elif user_state[message.from_user.id] == 'awaiting_broadcast_message_to_users':
        try:
            async with aiofiles.open("user_group_data.json", "r") as file:
                data = await file.read()
                users = json.loads(data)['users']
                for user_id in users:
                    await bot.send_message(user_id, broadcast_message)
            await bot.send_message(message.chat.id, "Сообщение успешно разослано пользователям в ЛС.")
        except Exception as e:
            await bot.send_message(message.chat.id, f"Ошибка при рассылке: {str(e)}")
    del user_state[message.from_user.id]

async def changeNickname(message):
    userId = message.from_user.id
    data = await load_data_cards()
    first_name = message.from_user.first_name
    premium_status, _ = await check_and_update_premium_status(str(userId))
    user_data = data.get(str(userId), {'cats': [], 'last_usage': 0, 'points': 0, 'nickname': first_name, 'card_count': 0})
    parts = message.text.split('сменить ник', 1)
    
    if len(parts) > 1 and parts[1].strip():
        new_nick = parts[1].strip()
        if len(new_nick) > 64:
            await bot.send_message(message.chat.id, "Никнейм не может быть длиннее 64 символов.")
            return
        if not premium_status and any(emoji.is_emoji(char) for char in new_nick):
            await bot.send_message(message.chat.id, "Вы не можете использовать эмодзи в нике. Приобретите премиум в профиле!")
            return
        user_data['nickname'] = new_nick
        data[str(userId)] = user_data
        await save_data(data)
        await bot.send_message(message.chat.id, f"Ваш никнейм был изменен на {new_nick}.")
    else:
        await bot.send_message(message.chat.id, "Никнейм не может быть пустым. Укажите значение после команды.")

last_request_time = {}

async def last_time_usage(user_id):
    current_time = time.time()
    if user_id in last_request_time and (current_time - last_request_time[user_id]) < 2:
        return False
    last_request_time[user_id] = current_time
    return True


@bot.message_handler(func=lambda message: True)
async def handle_text(message):
    try: 
        text = registr(message.text)
        if text in ["комару", "получить карту", "камар", "камару"]:
            if await last_time_usage(message.from_user.id):
                await komaru_cards_function(message)
        elif text in ["/profile", "профиль", "комару профиль", "камару профиль"]:
            if await last_time_usage(message.from_user.id):
                await user_profile(message)
        elif text in ["/start", "/start@komarucardsbot"]:
            if await last_time_usage(message.from_user.id):
                await start(message)
        elif text in ["/help", "/help@komarucardsbot"]:
            if await last_time_usage(message.from_user.id):
                await help(message)
        elif text in ['/admin_panel', '/admin_panel@komarucardsbot', 'админ панель']:
            if await last_time_usage(message.from_user.id):
                await admin_panel(message)
        elif text.startswith('сменить ник'):
            if await last_time_usage(message.from_user.id):
                await changeNickname(message)
            
    except Exception as e:
        await bot.send_message(message.chat.id, "Временная ошибка в обработке, повторите позже.")
        await bot.send_message(1130692453,
                               f"Произошла ошибка при обработке команды: в чате: {message.chat.id}. Ошибка: {e}")
        await bot.send_message(1268026433,
                               f"Произошла ошибка при обработке команды: в чате: {message.chat.id}. Ошибка: {e}")
        await bot.send_message(-1002202469628,
                               f"Произошла ошибка при обработке команды: в чате: {message.chat.id}. Ошибка: {e}")


async def main():
    config_data = await config_func()
    global cats
    cats = config_data['cats']
    await bot.infinity_polling(timeout=10, request_timeout=120)


import asyncio

if __name__ == "__main__":
    asyncio.run(main())
