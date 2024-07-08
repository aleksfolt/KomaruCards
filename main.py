# -*- coding: utf-8 -*-
import json
import random
import time
import os
import logging
from os import path
from datetime import datetime, timedelta
from telebot.async_telebot import AsyncTeleBot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice
import aiohttp
import asyncio
import telebot
from aiocryptopay import AioCryptoPay, Networks
import aiofiles
import emoji

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
crypto = AioCryptoPay(token='205872:AAN4Wj4SoVxVqtjBhfnXqQ1POMYCANkAuV8', network=Networks.MAIN_NET)
bot = AsyncTeleBot("7409912773:AAGLCpIH6TyjhrQzNSedFo7e6USf1RFXF5w")

user_button = {}
button_ids = {}


async def config_func():
    async with aiofiles.open('config.json', 'r', encoding='utf-8') as file:
        data = json.loads(await file.read())
    return data


if not path.exists("premium_users.json"):
    with open("premium_users.json", 'w') as f:
        json.dump({}, f)

if not path.exists("komaru_user_cards.json"):
    with open("komaru_user_cards.json", 'w') as f:
        json.dump({}, f)

responses = [
    "Уберите лапки от чужой кнопки.",
    "Лапки вверх, вы арестованы!",
    "Ваши лапки не для этой кнопки.",
    "Лапки прочь от этой кнопки!",
    "Ваши лапки здесь лишние."
]


async def save_data(data):
    try:
        async with aiofiles.open("komaru_user_cards.json", 'w') as f:
            await f.write(json.dumps(data, ensure_ascii=False, indent=4))
        logging.info("Data successfully saved.")
    except Exception as e:
        logging.error(f"Failed to save data: {e}")


async def load_data_cards():
    try:
        async with aiofiles.open("komaru_user_cards.json", 'r') as f:
            return json.loads(await f.read())
    except Exception as e:
        logging.error(f"Failed to load data: {e}")
        return {}


async def get_titul(card_count, user_id):
    if user_id in [1130692453, 1268026433]:
        return "Создатель"
    if user_id in [1497833411, 6679727618, 5872877426]:
        return "Лох"
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
    user_data = data.get(str(user_id),
                         {'cats': [], 'last_usage': 0, 'points': 0, 'nickname': first_name, 'card_count': 0})
    card_count = user_data.get('card_count', 0)
    favorite_card = user_data.get('love_card', 'Не выбрана')
    titul = await get_titul(card_count, user_id)

    collected_cards = len(user_data['cats'])
    total_cards = len(cats)

    premium_status, premium_expiration = await check_and_update_premium_status(user_id)
    premium_message = f"Премиум: активен до {premium_expiration}" if premium_status else "Премиум: не активен"

    try:
        user_profile_photos = await bot.get_user_profile_photos(user_id, limit=1)
        if user_profile_photos.photos:
            photo = user_profile_photos.photos[0][-1]
            file_id = photo.file_id

            file_info = await bot.get_file(file_id)
            downloaded_file = await bot.download_file(file_info.file_path)

            photo_cache = downloaded_file
        else:
            with open('avatar.jpg', 'rb') as f:
                photo_cache = f.read()

        caption = (
            f"Привет {user_data['nickname']}!\n\n"
            f"🏡 Твой профиль:\n"
            f"🃏 Собрано {collected_cards} из {total_cards} карточек\n"
            f"💰 Очки: {user_data['points']}\n"
            f"🎖️ Титул: {titul}\n"
            f"💖 Любимая карточка: {favorite_card}\n"
            f"🌟 {premium_message}"
        )

        unique_id = str(random.randint(100000, 999999))
        user_button[unique_id] = user_id
        keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
        button_1 = telebot.types.InlineKeyboardButton(text="🃏 Мои карточки", callback_data=f'show_cards_{unique_id}')
        button_2 = telebot.types.InlineKeyboardButton(text="🀄️ Топ карточек", callback_data=f'top_komaru_{unique_id}')
        button_3 = telebot.types.InlineKeyboardButton(text="💎 Премиум", callback_data=f'premium_callback_{unique_id}')
        keyboard.add(button_1, button_2, button_3)
        await bot.send_photo(message.chat.id, photo=photo_cache, caption=caption, reply_markup=keyboard)
    except telebot.apihelper.ApiException as e:
        if "bot was blocked by the user" in str(e):
            await bot.send_message(message.chat.id, "Пожалуйста, разблокируйте бота для доступа к вашему профилю.")
        else:
            await bot.send_message(message.chat.id, "Произошла ошибка при доступе к вашему профилю. Попробуйте позже.")


async def komaru_cards_function(call):
    if await last_time_usage(call.from_user.id):
        user_id = str(call.from_user.id)
        user_nickname = call.from_user.first_name
        await register_user_and_group_async(call.message)
    
        data = await load_data_cards()
        user_data = data.get(user_id, {'cats': [], 'last_usage': 0, 'points': 0, 'nickname': user_nickname, 'card_count': 0,
                                       'all_points': 0})
    
        if 'card_count' not in user_data:
            user_data['card_count'] = 0
    
        if 'all_points' not in user_data:
            user_data['all_points'] = 0
    
        user_data['points'] = int(user_data['points'])
        time_since_last_usage = time.time() - user_data['last_usage']
    
        premium_status, _ = await check_and_update_premium_status(user_id)
        wait_time = 14400 if not premium_status else 10800
    
        if time_since_last_usage < wait_time:
            remaining_time = wait_time - time_since_last_usage
            remaining_hours = int(remaining_time // 3600)
            remaining_minutes = int((remaining_time % 3600) // 60)
            remaining_seconds = int(remaining_time % 60)
            await bot.send_message(call.message.chat.id,
                                   f"{call.from_user.first_name}, вы осмотрелись, но не увидели рядом Комару. Попробуйте еще раз через {remaining_hours} часов {remaining_minutes} минут {remaining_seconds} секунд.")
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
                await bot.send_photo(call.message.chat.id, photo_data,
                                     caption=f"✨{call.from_user.first_name}, вы осмотрелись вокруг и снова увидели {chosen_cat['name']}! ✨\nБудут начислены только очки.\n\n🎲 Редкость: {chosen_cat['rarity']}\n💯 +{chosen_cat['points']} очков.\n🌟 Всего поинтов: {user_data['points'] + int(chosen_cat['points'])}")
                user_data['points'] += int(chosen_cat['points'])
                user_data['all_points'] += int(chosen_cat['points'])
            else:
                await bot.send_photo(call.message.chat.id, photo_data,
                                     caption=f"✨{call.from_user.first_name}, вы осмотрелись вокруг и увидели.. {chosen_cat['name']}! ✨\n\n🎲 Редкость: {chosen_cat['rarity']}\n💯 Очки: {chosen_cat['points']}\n🌟 Всего поинтов: {user_data['points'] + int(chosen_cat['points'])}")
                user_data['cats'].append(chosen_cat['name'])
                user_data['points'] += int(chosen_cat['points'])
                user_data['all_points'] += int(chosen_cat['points'])
                user_data['card_count'] += 1
            user_data['last_usage'] = time.time()
            data[user_id] = user_data
            await save_data(data)
            await bot.delete_message(call.message.chat.id, call.message.message_id)


async def promo(message):
    try:
        promo_code = message.text[6:]
        async with aiofiles.open("promo.json", 'r') as f:
            promo_data = json.loads(await f.read())

        data = promo_data.get(promo_code)
        if not data:
            await bot.send_message(message.chat.id, "Промокод не найден.")
            return

        user_id = message.from_user.id
        current_time = time.time()

        if current_time > data['until']:
            markup = InlineKeyboardMarkup()
            subscribe_button = InlineKeyboardButton("Подписаться", url="https://t.me/komaru_updates")
            markup.add(subscribe_button)
            await bot.send_message(message.chat.id,
                                   "Срок действия промокода истек. Подпишитесь на канал, чтобы не пропускать новые промо!",
                                   reply_markup=markup)
            return

        if data['activation_limit'] != -1 and data['activation_counts'] >= data['activation_limit']:
            markup = InlineKeyboardMarkup()
            subscribe_button = InlineKeyboardButton("Подписаться", url="https://t.me/komaru_updates")
            markup.add(subscribe_button)
            await bot.send_message(message.chat.id,
                                   "Этот промокод уже был активирован максимальное количество раз. Подпишитесь на канал, чтобы не пропускать новые промо!",
                                   reply_markup=markup)
            return

        try:
            chat_member = await bot.get_chat_member('@komaru_updates', user_id)
            if chat_member.status not in ['member', 'administrator', 'creator']:
                markup = InlineKeyboardMarkup()
                subscribe_button = InlineKeyboardButton("Подписаться", url="https://t.me/komaru_updates")
                markup.add(subscribe_button)
                await bot.send_message(message.chat.id,
                                       "Подпишитесь на канал, чтобы получить подарок.",
                                       reply_markup=markup)
                return
        except telebot.apihelper.ApiException as e:
            await bot.send_message(1130692453, f"Произошла ошибка {e}")
            await bot.send_message(1268026433, f"Произошла ошибка {e}")

        if user_id in data['users']:
            markup = InlineKeyboardMarkup()
            subscribe_button = InlineKeyboardButton("Подписаться", url="https://t.me/komaru_updates")
            markup.add(subscribe_button)
            await bot.send_message(message.chat.id,
                                   "Вы уже активировали этот промокод. Подпишитесь на канал, чтобы не пропускать новые промо!",
                                   reply_markup=markup)
            return

        action = data['action'].split()
        if action[0] == 'give_prem':
            await activate_premium(user_id, int(action[1]))
            data['users'].append(user_id)
            data["activation_counts"] += 1

            async with aiofiles.open("promo.json", 'w') as f:
                await f.write(json.dumps(promo_data, ensure_ascii=False, indent=4))

            await bot.send_message(message.chat.id,
                                   f"Промокод успешно активирован!\n\nВы получили премиум на {int(action[1])} дней!")
        elif action[0] == "kd":
            data_komaru = await load_data_cards()
            if str(user_id) in data_komaru:
                user_data = data_komaru[str(user_id)]
                current_time = time.time()
                premium_status, _ = await check_and_update_premium_status(user_id)
                wait_time = 10800 if premium_status else 14400

                time_since_last_usage = current_time - user_data['last_usage']
                if time_since_last_usage < wait_time:
                    user_data['last_usage'] = 0
                    data_komaru[str(user_id)] = user_data
                    await save_data(data_komaru)
                    logging.info(f"Waiting time for user {user_id} has been reset.")
                    data['users'].append(user_id)
                    data["activation_counts"] += 1

                    async with aiofiles.open("promo.json", 'w') as f:
                        await f.write(json.dumps(promo_data, ensure_ascii=False, indent=4))

                    await bot.send_message(message.chat.id,
                                           "Промокод успешно активирован!\n\nВы полуили обнуление кд на карточку!")
                else:
                    await bot.send_message(message.chat.id,
                                           "Пожалуйста откройте сначала карточку, а потом заново активируйте промокод.")
            else:
                logging.warning(f"User {user_id} not found in the data.")
                await bot.send_message(message.chat.id,
                                       "Пожалуйста откройте сначала карточку, а потом заново активируйте промокод.")

    except Exception as e:
        logging.error(f"Error processing promo code: {e}")
        await bot.send_message(1130692453, f"Произошла ошибка {e}")
        await bot.send_message(1268026433, f"Произошла ошибка {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith('show_cards'))
async def show_knock_cards(call):
    unique_id = call.data.split('_')[-1]
    if unique_id not in user_button or user_button[unique_id] != call.from_user.id:
        await bot.answer_callback_query(call.id, random.choice(responses), show_alert=True)
        return
    user_id = str(call.from_user.id)
    user_nickname = call.from_user.first_name
    data = await load_data_cards()
    user_data = data.get(user_id,
                         {'cats': [], 'last_usage': 0, 'points': 0, 'nickname': user_nickname, 'card_count': 0})
    collected_cards = len(user_data['cats'])
    total_cards = len(cats)
    if user_data['cats']:
        cats_owned_by_user = {cat['name'] for cat in cats if cat['name'] in user_data['cats']}
        rarities = {cat['rarity'] for cat in cats if cat['name'] in cats_owned_by_user}
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        for rarity in rarities:
            callback_data = f'show_{rarity[:15]}'  # Truncate to 15 characters
            keyboard.add(types.InlineKeyboardButton(text=rarity, callback_data=callback_data))
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
        await bot.answer_callback_query(call.id, "Вы пока что не наблюдали за птичками (в память о birdy).",
                                        show_alert=True)


@bot.callback_query_handler(func=lambda call: call.data.startswith('show_'))
async def show_cards(call):
    try:
        rarity = call.data[len('show_'):]
        user_id = str(call.from_user.id)
        user_nickname = call.from_user.first_name
        data = await load_data_cards()
        user_data = data.get(user_id,
                             {'cats': [], 'last_usage': 0, 'points': 0, 'nickname': user_nickname, 'card_count': 0})
        rarity_cards = [cat for cat in cats if cat['name'] in user_data['cats'] and cat['rarity'].startswith(rarity)]

        if rarity_cards:
            first_card_index = 0
            if first_card_index < len(rarity_cards):
                await send_initial_card_with_navigation(call.message.chat.id, user_id, rarity, rarity_cards,
                                                        first_card_index)
        else:
            await bot.send_message(call.message.chat.id, f"У вас нет карточек редкости {rarity}")
    except Exception as e:
        logging.error(f"Error in show_cards: {e}")
        await bot.send_message(call.message.chat.id, "Произошла ошибка при отображении карточек.")


async def send_initial_card_with_navigation(chat_id, user_id, rarity, rarity_cards, card_index):
    if card_index < len(rarity_cards):
        card = rarity_cards[card_index]
        photo_data = card['photo']
        caption = f"{card['name']}\nРедкость: {card['rarity']}"
        if 'points' in card:
            caption += f"\nОчки: {card['points']}"

        keyboard = types.InlineKeyboardMarkup(row_width=3)
        love_button = types.InlineKeyboardButton(text="❤️ Love", callback_data=f'love_{user_id[:15]}_{card["id"]}')
        keyboard.add(love_button)
        if card_index > 0:
            prev_button = types.InlineKeyboardButton(text="Назад",
                                                     callback_data=f'navigate_{user_id[:15]}_prev_{card_index - 1}_{rarity[:15]}')
            keyboard.add(prev_button)
        if card_index < len(rarity_cards) - 1:
            next_button = types.InlineKeyboardButton(text="Вперед",
                                                     callback_data=f'navigate_{user_id[:15]}_next_{card_index + 1}_{rarity[:15]}')
            keyboard.add(next_button)

        await bot.send_photo(chat_id, photo_data, caption=caption, reply_markup=keyboard)
    else:
        logging.error(f"Card index {card_index} out of range for rarity cards")


async def send_card_with_navigation(chat_id, message_id, user_id, rarity, rarity_cards, card_index):
    if card_index < len(rarity_cards):
        card = rarity_cards[card_index]
        photo_data = card['photo']
        caption = f"{card['name']}\nРедкость: {card['rarity']}"
        if 'points' in card:
            caption += f"\nОчки: {card['points']}"

        keyboard = types.InlineKeyboardMarkup(row_width=3)
        love_button = types.InlineKeyboardButton(text="❤️ Love", callback_data=f'love_{user_id[:15]}_{card["id"]}')
        keyboard.add(love_button)
        if card_index > 0:
            prev_button = types.InlineKeyboardButton(text="Назад",
                                                     callback_data=f'navigate_{user_id[:15]}_prev_{card_index - 1}_{rarity[:15]}')
            keyboard.add(prev_button)
        if card_index < len(rarity_cards) - 1:
            next_button = types.InlineKeyboardButton(text="Вперед",
                                                     callback_data=f'navigate_{user_id[:15]}_next_{card_index + 1}_{rarity[:15]}')
            keyboard.add(next_button)

        media = types.InputMediaPhoto(photo_data, caption=caption)
        await bot.edit_message_media(media, chat_id=chat_id, message_id=message_id, reply_markup=keyboard)
    else:
        logging.error(f"Card index {card_index} out of range for rarity cards")


@bot.callback_query_handler(func=lambda call: call.data.startswith('love_'))
async def handle_love_card(call):
    parts = call.data.split('_')
    user_id, card_id = parts[1], parts[2]
    data = await load_data_cards()
    user_data = data.get(user_id, {'cats': [], 'last_usage': 0, 'points': 0, 'nickname': '', 'love_card': ''})
    card_name = next((card['name'] for card in cats if card['id'] == card_id), None)
    if card_name:
        user_data['love_card'] = card_name
        data[user_id] = user_data
        await save_data(data)
        await bot.answer_callback_query(call.id, f"Карточка '{card_name}' теперь ваша любимая!")
    else:
        await bot.answer_callback_query(call.id, "Не найдено карточек с таким ID.")


@bot.callback_query_handler(func=lambda call: call.data.startswith('navigate_'))
async def navigate_cards(call):
    try:
        parts = call.data.split('_')
        user_id = parts[1]
        direction = parts[2]
        new_index = int(parts[3])
        rarity = parts[4]

        data = await load_data_cards()
        user_data = data.get(user_id, {'cats': [], 'last_usage': 0, 'points': 0, 'nickname': ''})
        rarity_cards = [cat for cat in cats if cat['name'] in user_data['cats'] and cat['rarity'].startswith(rarity)]

        logging.info(f"Navigating to card {new_index} of {len(rarity_cards) - 1}")

        if 0 <= new_index < len(rarity_cards):
            await send_card_with_navigation(call.message.chat.id, call.message.message_id, user_id, rarity,
                                            rarity_cards, new_index)
        else:
            await bot.send_message(call.message.chat.id, "Индекс карточки вне диапазона.")
    except Exception as e:
        logging.error(f"Error in navigate_cards: {e}")
        await bot.send_message(call.message.chat.id, "Произошла ошибка при навигации по карточкам.")


@bot.callback_query_handler(func=lambda call: call.data.startswith('top_komaru'))
async def top_komaru(call):
    unique_id = call.data.split('_')[-1]
    if unique_id not in user_button or user_button[unique_id] != call.from_user.id:
        await bot.answer_callback_query(call.id, random.choice(responses), show_alert=True)
        return
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
    button_1 = telebot.types.InlineKeyboardButton(text="🃏 Топ по карточкам",
                                                  callback_data=f'top_cards_cards_{unique_id}')
    button_2 = telebot.types.InlineKeyboardButton(text="💯 Топ по очкам", callback_data=f'top_cards_point_{unique_id}')
    button_3 = telebot.types.InlineKeyboardButton(text="⌛️ Топ за все время",
                                                  callback_data=f'top_cards_all_{unique_id}')
    keyboard.add(button_1, button_2, button_3)
    await bot.send_message(call.message.chat.id, "Топ 10 пользователей по карточкам. Выберите кнопку:",
                           reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data.startswith('top_cards_'))
async def cards_top_callback(call):
    parts = call.data.split('_')
    choice = parts[2]
    unique_id = parts[-1]

    if unique_id not in user_button or user_button[unique_id] != call.from_user.id:
        await bot.answer_callback_query(call.id, random.choice(responses), show_alert=True)
        return

    data = await load_data_cards()
    user_id = str(call.from_user.id)
    user_data = data.get(user_id, {'cats': [], 'points': 0, 'all_points': 0})
    message_text = ""

    if choice == "cards":
        sorted_data = sorted(data.items(), key=lambda x: len(x[1].get('cats', [])), reverse=True)
        user_rank = next((i for i, item in enumerate(sorted_data, 1) if item[0] == user_id), None)
        top_10 = sorted_data[:10]

        message_text = "🏆 Топ-10 пользователей по количеству собранных карточек:\n\n"
        for i, (uid, u_data) in enumerate(top_10, 1):
            nickname = u_data.get('nickname', 'Unknown')
            num_cards = len(u_data.get('cats', []))
            premium_status, _ = await check_and_update_premium_status(uid)
            premium_icon = "💎" if premium_status else ""
            message_text += f"{i}. {premium_icon} {nickname}: {num_cards} карточек\n"

        if user_rank and user_rank > 10:
            message_text += f"\nВаше место: {user_rank} ({data[user_id]['nickname']}: {len(user_data['cats'])} карточек)"

        keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
        button_2 = telebot.types.InlineKeyboardButton(text="💯 Топ по очкам",
                                                      callback_data=f'top_cards_point_{unique_id}')
        button_3 = telebot.types.InlineKeyboardButton(text="⌛️ Топ за все время",
                                                      callback_data=f'top_cards_all_{unique_id}')
        keyboard.add(button_2, button_3)

    elif choice == "point":
        sorted_data_points = sorted(data.items(), key=lambda x: x[1].get('points', 0), reverse=True)
        user_rank_points = next((j for j, item in enumerate(sorted_data_points, 1) if item[0] == user_id), None)
        top_10 = sorted_data_points[:10]

        message_text = "🏆 Топ-10 пользователей по количеству набранных очков:\n\n"
        for j, (uid, u_data) in enumerate(top_10, 1):
            nickname_2 = u_data.get('nickname', 'Unknown')
            points = u_data.get('points', 0)
            premium_status, _ = await check_and_update_premium_status(uid)
            premium_icon = "💎" if premium_status else ""
            message_text += f"{j}. {premium_icon} {nickname_2}: {points} очков\n"

        if user_rank_points and user_rank_points > 10:
            message_text += f"\nВаше место: {user_rank_points} ({data[user_id]['nickname']}: {user_data['points']} очков)"

        keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
        button_1 = telebot.types.InlineKeyboardButton(text="🃏 Топ по карточкам",
                                                      callback_data=f'top_cards_cards_{unique_id}')
        button_3 = telebot.types.InlineKeyboardButton(text="⌛ Топ за все время",
                                                      callback_data=f'top_cards_all_{unique_id}')
        keyboard.add(button_1, button_3)

    elif choice == "all":
        sorted_data = sorted(data.items(), key=lambda x: x[1].get('all_points', 0), reverse=True)
        user_rank_all = next((index for index, item in enumerate(sorted_data, 1) if item[0] == user_id), None)
        top_10 = sorted_data[:10]

        message_text = "🏆 Топ-10 пользователей по всем временам (очки):\n\n"
        for index, (uid, u_data) in enumerate(top_10, 1):
            nickname = u_data.get('nickname', 'Unknown')
            premium_status, _ = await check_and_update_premium_status(uid)
            premium_icon = "💎" if premium_status else ""
            total_points = u_data.get('all_points', 0)
            message_text += f"{index}. {premium_icon} {nickname}: {total_points} очков\n"

        if user_rank_all and user_rank_all > 10:
            message_text += f"\nВаше место: {user_rank_all} ({data[user_id]['nickname']}: {user_data['all_points']} очков)"

        keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
        button_1 = telebot.types.InlineKeyboardButton(text="🃏 Топ по карточкам",
                                                      callback_data=f'top_cards_cards_{unique_id}')
        button_2 = telebot.types.InlineKeyboardButton(text="💯 Топ по очкам",
                                                      callback_data=f'top_cards_point_{unique_id}')
        keyboard.add(button_1, button_2)

    if not message_text:
        message_text = "Не удалось получить данные. Попробуйте позже."

    await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=message_text,
                                reply_markup=keyboard)


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
    button1 = InlineKeyboardButton(text="Пользовательское соглашение",
                                   url="https://telegra.ph/Polzovatelskoe-soglashenie-06-17-6")
    button2 = InlineKeyboardButton(text="Наш канал", url="t.me/komaru_updates")
    keyboard.add(button1, button2)

    await bot.send_message(message.chat.id, help_text, parse_mode='HTML', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data.startswith('premium_callback'))
async def buy_premium(call):
    unique_id = call.data.split('_')[-1]
    if unique_id not in user_button or user_button[unique_id] != call.from_user.id:
        await bot.answer_callback_query(call.id, random.choice(responses), show_alert=True)
        return

    try:
        if call.message.chat.type == "private":
            await send_payment_method_selection(call.from_user.id, unique_id)
        else:
            try:
                await send_payment_method_selection(call.from_user.id, unique_id)
                await bot.send_message(call.message.chat.id, "Выбор способа оплаты отправлен в личные сообщения.")
            except telebot.apihelper.ApiException:
                await bot.answer_callback_query(call.id, "Пожалуйста, напишите боту что-то в личные сообщения.",
                                                show_alert=True)
    except Exception as e:
        await bot.answer_callback_query(call.id, "Пожалуйста, напишите боту что-то в личные сообщения.",
                                        show_alert=True)
        logging.error(f"Error in buy_premium: {e}")


async def send_payment_method_selection(user_id, unique_id):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    stars_button = types.InlineKeyboardButton(text="Telegram Stars", callback_data=f"pay_stars_{unique_id}")
    crypto_button = types.InlineKeyboardButton(text="CryptoBot", callback_data=f"pay_crypto_{unique_id}")
    keyboard.add(stars_button, crypto_button)
    await bot.send_message(user_id, "Выберите способ оплаты премиума:", reply_markup=keyboard)


prices = [LabeledPrice(label="25 Stars", amount=25)]


@bot.callback_query_handler(func=lambda call: call.data.startswith('pay_stars_'))
async def pay_with_stars(call):
    unique_id = call.data.split('_')[-1]
    if unique_id not in user_button or user_button[unique_id] != call.from_user.id:
        await bot.answer_callback_query(call.id, random.choice(responses), show_alert=True)
        return

    try:
        markup = InlineKeyboardMarkup()
        pay_button = InlineKeyboardButton(text="Оплатить", pay=True)
        markup.add(pay_button)

        await bot.send_invoice(
            call.from_user.id,
            title="Покупка премиума",
            description=f"🔓 Комару премиум:\n\n⌛️ Карточки каждые 3 часа\n🃏 Шанс на легендарные и мифические карты\n🌐 Смайлики в никнейме\n💎 Алмаз в топе\n🔄 Быстрая обработка сообщений\n🗓 Действует 30 дней\n\n",
            provider_token=None,
            currency='XTR',
            prices=prices,
            start_parameter='purchase-stars',
            invoice_payload='stars-invoice',
            reply_markup=markup
        )
        await bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception as e:
        await bot.send_message(call.from_user.id, f"Произошла ошибка: {str(e)}")
        logging.error(f"Error in pay_with_stars: {e}")


@bot.pre_checkout_query_handler(func=lambda query: True)
async def checkout(pre_checkout_query):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@bot.message_handler(content_types=['successful_payment'])
async def got_payment(message):
    await activate_premium(message.from_user.id, 30)
    await bot.send_message(message.chat.id,
                           '🌟 Спасибо за покупку Премиума! Наслаждайтесь эксклюзивными преимуществами.')


@bot.callback_query_handler(func=lambda call: call.data.startswith('pay_crypto_'))
async def pay_with_crypto(call):
    unique_id = call.data.split('_')[-1]
    if unique_id not in user_button or user_button[unique_id] != call.from_user.id:
        await bot.answer_callback_query(call.id, random.choice(responses), show_alert=True)
        return

    await create_and_send_invoice(call.from_user.id, unique_id)


async def create_and_send_invoice(user_id, unique_id):
    try:
        invoice = await crypto.create_invoice(asset='USDT', amount=0.5)
        if not invoice:
            response = "Ошибка при создании инвойса. Попробуйте позже."
            await bot.send_message(user_id, response)
            return None

        markup = types.InlineKeyboardMarkup()
        pay_button = types.InlineKeyboardButton(text="Оплатить", url=invoice.bot_invoice_url)
        paid_button = types.InlineKeyboardButton(text="Я оплатил",
                                                 callback_data=f"verify_payment_{unique_id}_{invoice.invoice_id}")
        markup.add(pay_button, paid_button)

        response = (
            f"🔓 Что даст тебе Комару премиум?\n\n"
            f"⌛️ Возможность получать карточки каждые 3 часа вместо 4\n"
            f"🃏 Повышенная вероятность выпадения легендарных и мифических карт\n"
            f"🌐 Возможность использовать смайлики в никнейме\n"
            f"💎 Отображение алмаза в топе карточек\n"
            f"🔄 Более быстрая обработка твоих сообщений\n"
            f"🗓️ Срок действия 30 дней\n\n"
            f"Премиум активируется после подтверждения оплаты. Реквизиты: {invoice.bot_invoice_url}"
        )
        await bot.send_message(user_id, response, reply_markup=markup)
        return invoice
    except Exception as e:
        error_message = f"Ошибка при создании инвойса: {e}"
        await bot.send_message(user_id, error_message)
        return None


@bot.callback_query_handler(func=lambda call: call.data.startswith('verify_payment'))
async def verify_payment(call):
    parts = call.data.split('_')
    if len(parts) < 4:
        await bot.send_message(call.message.chat.id, "Ошибка в данных платежа.")
        return

    action, context, unique_id, invoice = parts[0], parts[1], parts[2], parts[3]

    if unique_id not in user_button or user_button[unique_id] != call.from_user.id:
        await bot.answer_callback_query(call.id, random.choice(responses), show_alert=True)
        return

    try:
        print("Invoice ID:", invoice)
        payment_status = await get_invoice_status(invoice)
        if payment_status == 'paid':
            await activate_premium(call.from_user.id, 30)
            await bot.send_message(call.from_user.id,
                                   "🌟 Спасибо за покупку Премиума! Наслаждайтесь эксклюзивными преимуществами.")
            await bot.delete_message(call.message.chat.id, call.message.message_id)
        else:
            await bot.send_message(call.from_user.id, "Оплата не прошла! Попробуйте еще раз.")
    except Exception as e:
        await bot.send_message(call.from_user.id, f"Произошла ошибка при проверке статуса платежа: {str(e)}")


async def get_invoice_status(invoice_id):
    try:
        print(invoice_id)
        invoice = await crypto.get_invoices(invoice_ids=int(invoice_id))
        return invoice.status
    except Exception as e:
        print(f"Ошибка при получении данных инвойса: {e}")
        return None


async def activate_premium(user_id, days):
    try:
        user = await bot.get_chat(user_id)
        if user is None:
            print(f"Пользователь с user_id {user_id} не найден.")
            return

        premium_duration = timedelta(days=days)
        async with aiofiles.open('premium_users.json', 'r+') as file:
            data = json.loads(await file.read())
            if str(user_id) in data:
                current_expiration = datetime.strptime(data[str(user_id)], '%Y-%m-%d')
                new_expiration_date = current_expiration + premium_duration
            else:
                new_expiration_date = datetime.now() + premium_duration

            data[str(user_id)] = new_expiration_date.strftime('%Y-%m-%d')
            await file.seek(0)
            await file.write(json.dumps(data, ensure_ascii=False, indent=4))
            await file.truncate()
    except telebot.apihelper.ApiException as e:
        print(f"Ошибка активации премиум-статуса: {e}")
        await bot.send_message(user_id, "Произошла ошибка при активации премиум-статуса. Попробуйте позже.")


async def check_and_update_premium_status(user_id):
    async with aiofiles.open('premium_users.json', 'r') as file:
        premium_users = json.loads(await file.read())

    if str(user_id) in premium_users:
        expiration_date = datetime.strptime(premium_users[str(user_id)], '%Y-%m-%d')
        if expiration_date > datetime.now():
            return True, expiration_date.strftime('%Y-%m-%d')
        else:
            del premium_users[str(user_id)]
            async with aiofiles.open('premium_users.json', 'w') as file:
                await file.write(json.dumps(premium_users, ensure_ascii=False, indent=4))
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


async def changeNickname(message):
    user_id = message.from_user.id
    data = await load_data_cards()
    first_name = message.from_user.first_name
    premium_status, _ = await check_and_update_premium_status(str(user_id))
    user_data = data.get(str(user_id),
                         {'cats': [], 'last_usage': 0, 'points': 0, 'nickname': first_name, 'card_count': 0})
    text = registr(message.text)
    parts = text.split('сменить ник', 1)

    if len(parts) > 1 and parts[1].strip():
        new_nick = parts[1].strip()

        if len(new_nick) > 64:
            await bot.send_message(message.chat.id, "Никнейм не может быть длиннее 64 символов.")
            return

        if not premium_status and any(emoji.is_emoji(char) for char in new_nick):
            await bot.send_message(message.chat.id,
                                   "Вы не можете использовать эмодзи в нике. Приобретите премиум в профиле!")
            return

        if any(entity.type == 'url' for entity in message.entities or []):
            await bot.send_message(message.chat.id, "Никнейм не может содержать ссылки.")
            return

        if '@' in new_nick:
            await bot.send_message(message.chat.id, "Никнейм не может содержать юзернеймы.")
            return

        user_data['nickname'] = new_nick
        data[str(user_id)] = user_data
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


@bot.message_handler(commands=['admin_panel'])
async def admin_panel(message):
    if message.from_user.id not in [1130692453, 1268026433]:
        await bot.reply_to(message, "У вас нет прав для выполнения этой команды.")
        return

    try:
        parts = message.text.split(' ', 3)
        if len(parts) < 4:
            await bot.reply_to(message,
                               "Неверный формат команды. Используйте: /admin_panel <action> <лс/группа> <текст> <кнопка с ссылкой[ссылка]>")
            return

        action = parts[1]
        target = parts[2]
        rest = parts[3]

        text_start = rest.find('<') + 1
        text_end = rest.find('>')
        if text_start == 0 or text_end == -1:
            await bot.reply_to(message, "Неверный формат текста. Используйте: <текст>")
            return

        text = rest[text_start:text_end]
        button_text = None
        button_url = None

        button_start = rest.find('<', text_end + 1)
        button_end = rest.find('>', button_start + 1)
        if button_start != -1 and button_end != -1:
            button_text_url = rest[button_start + 1:button_end]
            button_text, button_url = button_text_url.split('[')
            button_url = button_url.strip(']')

        async with aiofiles.open("user_group_data.json", "r") as file:
            data = json.loads(await file.read())

        if target == 'группа':
            targets = data.get('groups', {}).keys()
        elif target == 'лс':
            targets = data.get('users', {}).keys()
        else:
            await bot.reply_to(message, "Неверный тип получателя. Используйте 'группа' или 'лс'.")
            return

        keyboard = None
        if button_text and button_url:
            keyboard = types.InlineKeyboardMarkup()
            button = types.InlineKeyboardButton(text=button_text, url=button_url)
            keyboard.add(button)

        for chat_id in targets:
            try:
                await bot.send_message(chat_id, text, reply_markup=keyboard)
            except Exception as e:
                logging.error(f"Error sending message to {chat_id}: {e}")

        await bot.reply_to(message, f"Сообщение успешно разослано по {target}.")

    except Exception as e:
        await bot.reply_to(message, f"Произошла ошибка: {e}")


from datetime import datetime

send_files_task = None
authorized_users = {1268026433, 1130692453}
receivers = [-1002169656453]


@bot.message_handler(commands=['send_aiofiles_start'])
async def start_sending_files(message):
    if message.from_user.id in authorized_users:
        global send_files_task
        if send_files_task is None:
            send_files_task = asyncio.create_task(send_files_periodically())
            await bot.reply_to(message, "Начинаю отправку файлов каждые 10 минут.")
        else:
            await bot.reply_to(message, "Отправка файлов уже активирована.")
    else:
        await bot.reply_to(message, "У вас нет доступа к этой команде.")


@bot.message_handler(commands=['send_aiofiles_stop'])
async def stop_sending_files(message):
    if message.from_user.id in authorized_users:
        global send_files_task
        if send_files_task is not None:
            send_files_task.cancel()
            send_files_task = None
            await bot.reply_to(message, "Отправка файлов остановлена.")
        else:
            await bot.reply_to(message, "Отправка файлов не была активирована.")
    else:
        await bot.reply_to(message, "У вас нет доступа к этой команде.")


def count_elements_in_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            return len(data)
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        return 0


async def send_files_periodically():
    try:
        while True:
            current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            file_paths = ['premium_users.json', 'komaru_user_cards.json', 'promo.json', 'user_group_data.json']
            for user_id in receivers:
                for file_path in file_paths:
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as file:
                            await bot.send_document(user_id, file)
                users = count_elements_in_json("komaru_user_cards.json")
                await bot.send_message(user_id, f"Резервная копия: {current_date}\nКоличество пользователей: {users}")
            await asyncio.sleep(600)
    except asyncio.CancelledError:
        print("Задача по отправке файлов была остановлена.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")


@bot.message_handler(func=lambda message: True)
async def handle_text(message):
    try:
        text = registr(message.text)
        if text in ["комару", "получить карту", "камар", "камару"]:
            if await last_time_usage(message.from_user.id):
                await send_card_button(message)
        elif text in ["/profile", "профиль", "комару профиль", "камару профиль"]:
            if await last_time_usage(message.from_user.id):
                await user_profile(message)
        elif text in ["/start", "/start@komarucardsbot"]:
            if await last_time_usage(message.from_user.id):
                await start(message)
        elif text in ["/help", "/help@komarucardsbot"]:
            if await last_time_usage(message.from_user.id):
                await help(message)
        elif text.startswith('сменить ник'):
            if await last_time_usage(message.from_user.id):
                await changeNickname(message)
        elif text.startswith('промо '):
            if await last_time_usage(message.from_user.id):
                await promo(message)
        elif text in ["/privacy", "/privacy@komarucardsbot"]:
            if await last_time_usage(message.from_user.id):
                keyboard = types.InlineKeyboardMarkup(row_width=2)
                button_1 = types.InlineKeyboardButton(text="Наше пользовательское соглашение",
                                                      url="https://telegra.ph/Polzovatelskoe-soglashenie-06-17-6")
                keyboard.add(button_1)
                await bot.send_message(message.chat.id,
                                       "Мы обрабатываем данные пользователей строго в целях улучшения функционала нашего бота. Гарантируем, что данные пользователя, включая идентификатор пользователя (user ID) и имя (first name), не будут переданы третьим лицам или использованы вне контекста улучшения бота. Наш приоритет — обеспечение безопасности и конфиденциальности информации, которую вы нам доверяете.\n\nДля повышения прозрачности нашей работы, мы также обязуемся предоставлять пользователю доступ к информации о том, какие данные собраны и как они используются. В случае изменения политики использования данных, мы своевременно информируем пользователей через обновления нашего пользовательского соглашения. Мы прилагаем все усилия, чтобы наш сервис был максимально безопасным и удобным для пользователя.",
                                       reply_markup=keyboard)
    except Exception as e:
        await bot.send_message(message.chat.id, "Временная ошибка в обработке, повторите позже.")
        await bot.send_message(1130692453,
                               f"Произошла ошибка при обработке команды: в чате: {message.chat.id}. Ошибка: {e}")
        await bot.send_message(1268026433,
                               f"Произошла ошибка при обработке команды: в чате: {message.chat.id}. Ошибка: {e}")
        await bot.send_message(-1002202469628,
                               f"Произошла ошибка при обработке команды: в чате: {message.chat.id}. Ошибка: {e}")


async def send_card_button(message):
    user_id = str(message.from_user.id)
    data = await load_data_cards()
    user_data = data.get(user_id, {'last_usage': 0})

    time_since_last_usage = time.time() - user_data['last_usage']
    premium_status, _ = await check_and_update_premium_status(user_id)
    wait_time = 14400 if not premium_status else 10800

    if time_since_last_usage < wait_time:
        remaining_time = wait_time - time_since_last_usage
        remaining_hours = int(remaining_time // 3600)
        remaining_minutes = int((remaining_time % 3600) // 60)
        remaining_seconds = int(remaining_time % 60)
        await bot.reply_to(message,
                           f"✨Вы осмотрелись, но не увидели рядом Комару.\n🔍 Попробуйте еще раз через {remaining_hours} часов {remaining_minutes} минут {remaining_seconds} секунд.")
    else:
        keyboard = types.InlineKeyboardMarkup()
        unique_id = str(random.randint(100000, 999999))
        user_button[unique_id] = user_id
        logging.info(f"send_card_button: unique_id={unique_id}, user_id={user_id}")
        button = types.InlineKeyboardButton(text="🐾 Тап 🃏", callback_data=f"get_card_{unique_id}")
        keyboard.add(button)
        sent_message = await bot.send_message(message.chat.id, "Нажмите кнопку ниже, чтобы получить карточку:",
                                              reply_markup=keyboard)
        await asyncio.create_task(delete_message_after_delay(sent_message.chat.id, sent_message.message_id, 35))


async def delete_message_after_delay(chat_id, message_id, delay):
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id, message_id)
    except Exception as e:
        pass


@bot.callback_query_handler(func=lambda call: call.data.startswith('get_card_'))
async def handle_get_card(call):
    unique_id = str(call.data.split('_')[-1])
    logging.info(f"handle_get_card: unique_id={unique_id}, user_id={call.from_user.id}")
    if unique_id not in user_button or user_button[unique_id] != str(call.from_user.id):
        await bot.answer_callback_query(call.id, random.choice(responses), show_alert=True)
        return
    await komaru_cards_function(call)


async def main():
    config_data = await config_func()
    global cats
    cats = config_data['cats']
    await bot.infinity_polling(timeout=10, request_timeout=120)


import asyncio

if __name__ == "__main__":
    asyncio.run(main())
