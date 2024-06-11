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

bot = AsyncTeleBot("7409912773:AAH6zKcL5S0hAyLfr5KcUQC0bRgYtmEsxg0")


async def config_func():
  with open('config.json', 'r', encoding='utf-8') as file:
      data = json.load(file)
  return data

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

async def user_profile(message):
  user_id = message.from_user.id
  first_name = message.from_user.first_name
  last_name = message.from_user.last_name or ""
  data = await load_data_cards()
  user_data = data.get(str(user_id), {'cats': [], 'last_usage': 0, 'points': 0, 'nickname': first_name})
  collected_cards = len(user_data['cats'])
  total_cards = len(cats)
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
      f"Привет {first_name} {last_name}!\n\n"
      f"🏡 Твой профиль:\n"
      f"🃏 Собрано {collected_cards} из {total_cards} карточек\n"
      f"💰 Очки: {user_data['points']}\n"
      f"📝 Ник: {user_data['nickname']}"
  )
  unique_number = random.randint(1000, 1000000000000000000000)
  user_button[user_id] = unique_number
  keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
  button_1 = telebot.types.InlineKeyboardButton(text="Мои карточки", callback_data=f'show_cards_{unique_number}')
  button_2 = telebot.types.InlineKeyboardButton(text="Топ карточек", callback_data=f'top_komaru_{unique_number}')
  keyboard.add(button_1, button_2)
  await bot.send_photo(message.chat.id, photo=open(downloaded_file_path, 'rb'), caption=caption, reply_markup=keyboard)

last_request_time = {}

async def komaru_cards_function(message):
  user_id = str(message.from_user.id)
  user_nickname = message.from_user.first_name
  current_time = time.time()
  if user_id in last_request_time and (current_time - last_request_time[user_id]) < 0.3:
      bot.reply_to(message, "Пожалуйста, подождите немного перед следующим запросом.")
      return
    
  last_request_time[user_id] = current_time
  
  data = await load_data_cards()
  user_data = data.get(user_id, {'cats': [], 'last_usage': 0, 'points': 0, 'nickname': user_nickname})
  user_data['points'] = int(user_data['points'])
  time_since_last_usage = time.time() - user_data['last_usage']
  time_left = max(0, 14400 - time_since_last_usage)

  if time_since_last_usage < 14400:
      remaining_time = 14400 - time_since_last_usage
      remaining_hours = int(remaining_time // 3600)
      remaining_minutes = int((remaining_time % 3600) // 60)
      remaining_seconds = int(remaining_time % 60)
      await bot.reply_to(message, f"Вы осмотрелись, но не увидели рядом ни одного Комару. Попробуйте еще раз через {remaining_hours} часов {remaining_minutes} минут {remaining_seconds} секунд.")
      return

  random_number = random.randint(1, 95)
  if 0 <= random_number <= 14:
      eligible_cats = [cat for cat in cats if cat["rarity"] == "Легендарная"]
  elif 15 <= random_number <= 29:
      eligible_cats = [cat for cat in cats if cat["rarity"] == "Мифическая"]
  elif 30 <= random_number <= 49:
      eligible_cats = [cat for cat in cats if cat["rarity"] == "Сверхредкая"]
  elif 50 <= random_number <= 95:
      eligible_cats = [cat for cat in cats if cat["rarity"] == "Редкая"]

  if eligible_cats:
      chosen_cat = random.choice(eligible_cats)
      photo_data = chosen_cat['photo']
      if chosen_cat['name'] in user_data['cats']:
          with open(photo_data, 'rb') as photo_file:
              await bot.send_photo(message.chat.id, photo_file, caption=f"Вы осмотрелись вокруг и снова увидели {chosen_cat['name']}! Будут начислены только очки.\nРедкость: {chosen_cat['rarity']}\n+{chosen_cat['points']} очков.\n\nВсего поинтов: {user_data['points'] + int(chosen_cat['points'])}")
          user_data['points'] += int(chosen_cat['points'])
      else:
          with open(photo_data, 'rb') as photo_file:
              await bot.send_photo(message.chat.id, photo_file, caption=f"Вы осмотрелись вокруг и увидели {chosen_cat['name']}!\nРедкость: {chosen_cat['rarity']}\nОчки: {chosen_cat['points']}\n\nВсего поинтов: {user_data['points'] + int(chosen_cat['points'])}")
          user_data['cats'].append(chosen_cat['name'])
          user_data['points'] += int(chosen_cat['points'])
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
  user_data = data.get(user_id, {'cats': [], 'last_usage': 0, 'points': 0, 'nickname': user_nickname})
  collected_cards = len(user_data['cats'])
  total_cards = len(cats)
  if user_data['cats']:
      cats_owned_by_user = {cat['name'] for cat in cats if cat['name'] in user_data['cats']}
      rarities = {cat['rarity'] for cat in cats if cat['name'] in cats_owned_by_user}
      keyboard = types.InlineKeyboardMarkup(row_width=1)
      for rarity in rarities:
          keyboard.add(types.InlineKeyboardButton(text=rarity, callback_data=f'show_{rarity}'))
      try:
          await bot.send_message(call.from_user.id, f"У вас собрано {collected_cards} из {total_cards} возможных\nВыберите редкость:", reply_markup=keyboard)
          chat_type = call.message.chat.type
          if chat_type in ['group', 'supergroup']:
              await bot.send_message(call.message.chat.id, f"{call.from_user.first_name}, карточки отправлены вам в личные сообщения!")
          else:
              pass
      except telebot.apihelper.ApiException as e:
          logging.error(f"Не удалось отправить сообщение: {str(e)}")
          await bot.send_message(call.message.chat.id, "Напишите боту что-то в личные сообщения, чтобы отправить вам карточки!")
  else:
      await bot.send_message(call.message.chat.id, "Вы пока что не наблюдали за птичками.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('show_'))
async def show_cards(call):
  rarity = call.data[len('show_'):]
  user_id = str(call.from_user.id)
  user_nickname = call.from_user.first_name
  data = await load_data_cards()
  user_data = data.get(user_id, {'cats': [], 'last_usage': 0, 'points': 0, 'nickname': user_nickname})
  rarity_cards = [cat for cat in cats if cat['name'] in user_data['cats'] and cat['rarity'] == rarity]

  if rarity_cards:
      for cat in rarity_cards:
          photo_data = cat['photo']
          caption = f"{cat['name']}\nРедкость: {cat['rarity']}"
          if 'points' in cat:
              caption += f"\nОчки: {cat['points']}"
          with open(photo_data, 'rb') as photo_file:
              chat_type = call.message.chat.type
              await bot.send_photo(call.message.chat.id, photo_file, caption=caption)
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
  await bot.send_message(call.message.chat.id, "Топ 10 пользователей по карточкам. Выберите кнопку:", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data.startswith('top_cards_'))
async def cards_top_callback(call):
    choice = call.data.split('_')[2]
    data = await load_data_cards()
    user_id = str(call.from_user.id)
    user_data = data.get(user_id, {'points': 0, 'cats': []})
    message_text = ""

    if choice == "cards":
        sorted_data = sorted(data.items(), key=lambda x: len(x[1].get('birds', [])), reverse=True)
        top_10 = sorted_data[:10]

        message_text = "Топ-10 пользователей по количеству собранных карточек:\n\n"
        for i, (user_id, user_data) in enumerate(top_10, 1):
            nickname = user_data.get('nickname', 'Unknown')
            num_cards = len(user_data.get('cats', []))
            message_text += f"{i}. {nickname}: {num_cards} карточек\n"

    elif choice == "point":
        sorted_data_points = sorted(data.items(), key=lambda x: x[1].get('points', 0), reverse=True)
        top_10 = sorted_data_points[:10]

        message_text = "Топ-10 пользователей по количеству набранных очков:\n\n"
        for j, (user_id, user_data) in enumerate(top_10, 1):
            nickname_2 = user_data.get('nickname', 'Unknown')
            points = user_data.get('points', 0)
            message_text += f"{j}. {nickname_2}: {points} очков\n"

    if not message_text:
        message_text = "Не удалось получить данные. Попробуйте позже."

    await bot.delete_message(call.message.chat.id, call.message.message_id)

    await bot.send_message(call.message.chat.id, message_text)

def registr(s):
  for i in range(len(s)):
      if s[i].isupper():
          s = s[:i] + s[i].lower() + s[i+1:]
  return s

@bot.message_handler(commands=['start'])
async def start(message):
  if message.chat.type == 'private':
      markup = types.InlineKeyboardMarkup()
      add_bot_button = types.InlineKeyboardButton(text="Добавить бота в группу", url=f"https://t.me/KomaruCardsBot?startgroup=iris&admin=change_info+restrict_members+delete_messages+pin_messages+invite_users")
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

@bot.message_handler(commands=['help'])
async def help(message):
    help_text = (
        "<b>Komaru Bot</b> - Ваш помощник в сборе карточек комару\n\n"
        "<b>Доступные команды:</b>\n"
        "/start - Начать работу с ботом\n"
        "/help - Получить помощь\n"
        "/profile, 'профиль', 'комару профиль' - Посмотреть свой профиль\n"
        "'комару', 'получить карту', 'камар' - Искать котов и собирать карточки\n"
    )
    await bot.send_message(message.chat.id, help_text, parse_mode='HTML')


@bot.message_handler(commands=['admin_send_files'])
def handle_send_files(message):
    try:
        user_id = message.from_user.id
        if user_id != 1130692453 and user_id != 1268026433:
            bot.send_message(message.chat.id, "У вас нет прав на выполнение этой команды!")
            return
        filenames = message.text.split()[1:]
        if len(filenames) == 0:
            bot.reply_to(message, "Пожалуйста, укажите имена файлов для отправки.")
            return
        send_files(message.chat.id, filenames)
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")
        print(f"Ошибка: {e}")

def send_files(chat_id, filenames):
    try:
        for filename in filenames:
            with open(filename, 'rb') as file:
                bot.send_document(chat_id, file)
    except Exception as e:
        bot.send_message(chat_id, f"Не удалось отправить файл {filename}: {e}")
        print(f"Не удалось отправить файл {filename}: {e}")


@bot.message_handler(func=lambda message: True)
async def handle_text(message):
  try:
      text = registr(message.text)
      if text in ["комару", "получить карту", "камар"]:
          await komaru_cards_function(message)
      elif text in ["/profile", "профиль", "комару профиль"]:
          await user_profile(message)
  except Exception as e:
      await bot.send_message(message.chat.id, "Временная ошибка в обработке, повторите позже.")
      await bot.send_message(1130692453, f"Произошла ошибка при обработке команды: в чате: {message.chat.id}. Ошибка: {e}")
      await bot.send_message(1268026433, f"Произошла ошибка при обработке команды: в чате: {message.chat.id}. Ошибка: {e}")
      await bot.send_message(-1002202469628, f"Произошла ошибка при обработке команды: в чате: {message.chat.id}. Ошибка: {e}")

async def main():
  config_data = await config_func()
  global cats
  cats = config_data['cats']
  await bot.infinity_polling()

import asyncio
if __name__ == "__main__":
  asyncio.run(main())
