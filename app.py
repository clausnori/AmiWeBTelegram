import telebot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import TOKEN
import database as db
import threading
import random
import re
from datetime import datetime, timedelta
from collections import defaultdict

bot = telebot.TeleBot(TOKEN)

conn, cursor = db.connect_db()
db.create_tables(cursor)
db.load_shop_items(cursor)
conn.commit()

RATE_LIMIT = 5  # максимальное количество команд
TIME_INTERVAL = 10  # интервал в секундах
user_command_times = defaultdict(list)

def anti_spam(func):
    def wrapper(message):
        user_id = message.from_user.id
        if check_spam(user_id):
            bot.reply_to(message, "Пожалуйста, не отправляйте команды так часто. Подождите немного.")
        else:
            return func(message)
    return wrapper

def check_spam(user_id):
    current_time = datetime.now()
    user_times = user_command_times[user_id]
    user_times = [time for time in user_times if (current_time - time).total_seconds() < TIME_INTERVAL]
    user_times.append(current_time)
    user_command_times[user_id] = user_times
    
    if len(user_times) > RATE_LIMIT:
        return True
    return False

def is_private_chat(message):
    return message.chat.type == 'private'

def payment_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(text="Оплатить ⭐", pay=True)
    keyboard.add(button)
    return keyboard

def start_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(text="Подтвердить", callback_data="donate")
    keyboard.add(button)
    return keyboard

@bot.message_handler(commands=['start'])
@anti_spam
def handle_start(message):
    bot.send_message(message.chat.id, "Добро пожаловать!!! \n Тык=> /helpa")
    
@bot.message_handler(commands=['ami'])
def send_welcome(message):
  if not is_private_chat(message):
        bot.send_message(message.chat.id, "Эта команда доступна только в личных сообщениях.")
  else:
    user_id = message.from_user.id
    link = f"https://clausbb.pythonanywhere.com/main/{user_id}"
    keyboard = InlineKeyboardMarkup()
    button = InlineKeyboardButton("Открыть веб-приложение", url=link)
    keyboard.add(button)
    bot.send_message(message.chat.id, "Нажмите на кнопку, чтобы открыть Ленту:", reply_markup=keyboard)


@bot.message_handler(commands=['balance'])
@anti_spam
def handle_balance(message):
  user_id = message.from_user.id
  ball = db.get_user_balance(cursor, user_id)
  conn.commit()
  if not is_private_chat(message):
        bot.send_message(message.chat.id, "Эта команда доступна только в личных сообщениях.")
  else:
    bot.send_message(message.chat.id, f"Ваш баланс {ball} ⭐")    
    
@bot.message_handler(commands=['helpa'])
@anti_spam
def handle_help(message):
    bot.send_message(message.chat.id, "Помощь по боту \n job - Получить 3 звезды \n1 helpa-Помощь \n2 donate- Донат звёздами Telegram \n3 balance- Показать баланс \n4 get - Передать монеты / get @ник количество \n5 rating -Рейтинг звёзд \n6 vin - Игра в Случайный выиграш \n7 shop- Купить штуки)) \n8 inventory- Инвентарь\n use-Использовать придмет из инвентаря")

@bot.message_handler(commands=['get'])
@anti_spam
def handle_get(message):
    if not is_private_chat(message):
        bot.send_message(message.chat.id, "Эта команда доступна только в личных сообщениях.")
    else:
        try:
            command_parts = message.text.split()
            if len(command_parts) != 3:
                bot.send_message(message.chat.id, "Используйте формат команды: /get @пользователь количество")
                return
            target_username = command_parts[1]
            amount = int(command_parts[2])
            if not re.match(r'^@[\w]+$', target_username):
                bot.send_message(message.chat.id, "Некорректное имя пользователя.")
                return
            sender_id = message.from_user.id
            sender_username = message.from_user.username if message.from_user.username else "Неизвестный пользователь"
            target_username = target_username[1:]
            target_user_id = db.get_user_id_by_username(cursor, target_username)
            conn.commit()
            if not target_user_id:
                bot.send_message(message.chat.id, "Пользователь не найден.")
                return

            # Проверка баланса отправителя
            if db.get_user_balance(cursor, sender_id) < amount:
                bot.send_message(message.chat.id, "У вас недостаточно звезд для перевода.")
                return

            # Обновление балансов
            db.update_user_balance(cursor, sender_id, sender_username, -amount)
            conn.commit()
            db.update_user_balance(cursor, target_user_id, target_username, amount)
            conn.commit()

            bot.send_message(message.chat.id, f"Вы успешно передали {amount} ⭐ пользователю @{target_username}!")
        except ValueError:
            bot.send_message(message.chat.id, "Пожалуйста, введите корректное количество.")
            
@bot.message_handler(commands=['getadmin'])
@anti_spam
def handle_get(message):
    user_id = message.from_user.id
    admin = 1219350082
    if user_id == admin:
      try:
            command_parts = message.text.split()
            if len(command_parts) != 3:
                bot.send_message(message.chat.id, "Используйте формат команды: /get @пользователь количество")
                return
            target_username = command_parts[1]
            amount = int(command_parts[2])
            if not re.match(r'^@[\w]+$', target_username):
                bot.send_message(message.chat.id, "Некорректное имя пользователя.")
                return
            sender_id = message.from_user.id
            sender_username = message.from_user.username if message.from_user.username else "Неизвестный пользователь"
            target_username = target_username[1:]
            target_user_id = db.get_user_id_by_username(cursor, target_username)
            if not target_user_id:
                bot.send_message(message.chat.id, "Пользователь не найден.")
                return
            # Обновление балансов
            db.update_user_balance(cursor, target_user_id, target_username, amount)
            conn.commit()

            bot.send_message(message.chat.id, f"Вы успешно передали {amount} ⭐ пользователю @{target_username}!")
      except ValueError:
            bot.send_message(message.chat.id, "Пожалуйста, введите корректное количество.")
    else:
      bot.send_message(message.chat.id, "))")

@bot.message_handler(commands=['pins'])
@anti_spam
def link(message):
  command_parts = message.text.split()
  username = message.from_user.username if message.from_user.username else "Неизвестный пользователь"
  if len(command_parts) >= 2:
    link = ' '.join(command_parts[1:])
    user_id = message.from_user.id
    if db.get_user_balance(cursor, user_id) < 500:
      bot.send_message(message.chat.id, "У вас недостаточно звезд для закрепа,нужно 500 stars.")
      return
    else:
      db.update_user_balance(cursor, user_id, username,-500)
      sent_message = bot.send_message(message.chat.id, link)
      message_id = sent_message.message_id
      bot.pin_chat_message(message.chat.id, message_id)
  else:
      bot.send_message(message.chat.id,"Нет текста")
      
      
# Функция для расчета общего баланса
def calculate_total_balance(users):
    total_balance = sum(user['balance'] for user in users)
    return total_balance
@bot.message_handler(commands=['rating'])
@anti_spam
def handle_rating(message):
    users = db.get_user_ranking(cursor)
    total_balance = calculate_total_balance(users)
    response = "Рейтинг пользователей по ⭐:\n"
    # Assuming users is a list of dictionaries
    sorted_users = sorted(users, key=lambda x: x['balance'], reverse=True)
    
    response = ""
    for index, user in enumerate(sorted_users[:10], start=1):
        user_id = user['user_id']
        username = user['username']
        balance = user['balance']
        response += f"{index}. {username} - Баланс: {balance}⭐ \n"
    
    response += f"\nОбщая сумма всех ⭐: {total_balance} "
    
    # Send the response message
    bot.send_message(message.chat.id, response)

@bot.message_handler(commands=['shop'])
def handle_shop(message):
    if not is_private_chat(message):
      items = db.get_shop_items(cursor)
      print(items)
      response = "Доступные предметы:\n"
      for item in items:
          response += f"{item['name']} - {item['price']} ⭐\nОписание: {item['description']}\n\n"
      bot.send_message(message.chat.id, response)
      bot.send_message(message.chat.id,"Покупка только в личных сообщениях с ботом")
    else:
        items = db.get_shop_items(cursor)
        
        response = "Доступные предметы:\n"
        for item in items:
            response += f"{item['name']} - {item['price']} ⭐\nОписание: {item['description']}\n\n"
        bot.send_message(message.chat.id, response)

        bot.send_message(message.chat.id, "Введите название предмета для покупки:")
        bot.register_next_step_handler(message, process_item_purchase)

def process_item_purchase(message):
    item_name = message.text.strip()
    user_id = message.from_user.id

    if db.purchase_item(cursor, user_id, item_name):
        conn.commit()
        bot.send_message(message.chat.id, f"Вы купили {item_name}!")
    else:
        bot.send_message(message.chat.id, "Предмет не найден или недостаточно средств для покупки.")

@bot.message_handler(commands=['inventory'])
def handle_inventory(message):
    user_id = message.from_user.id
    items = db.get_user_inventory(cursor, user_id)

    if items:
        response = "Ваш инвентарь:\n"
        for item in items:
            response += f"- {item['item_name']}\n"
    else:
        response = "Ваш инвентарь пуст."

    bot.send_message(message.chat.id, response)

@bot.message_handler(commands=['donate'])
@anti_spam
def handle_donate(message):
    if not is_private_chat(message):
        bot.send_message(message.chat.id,"Донатить лучше через директ))")
    else:
        bot.send_message(message.chat.id, "Введите сумму доната в ⭐:")
        bot.register_next_step_handler(message, process_donation_amount)

def process_donation_amount(message):
    try:
        amount = int(float(message.text))
        bot.send_message(
            message.chat.id,
            f"Вы выбрали {amount} ⭐ для доната. Подтвердите оплату.",
            reply_markup=start_keyboard()
        )
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректное число.")

@bot.callback_query_handler(func=lambda call: call.data == "donate")
def handle_buy_image(call):
    amount = int(call.message.text.split()[2])  # Извлекаем сумму из сообщения
    prices = [types.LabeledPrice(label="XTR", amount=amount)]
    bot.send_invoice(
        call.message.chat.id,
        title="Донат",
        description=f"Донат на {amount} ⭐ !",
        invoice_payload="donate_purchase_payload",
        provider_token="",  # Укажите свой токен провайдера
        currency="XTR",
        prices=prices,
        reply_markup=payment_keyboard()
    )

@bot.pre_checkout_query_handler(func=lambda query: True)
def handle_pre_checkout_query(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def handle_successful_payment(message):
    user_id = message.from_user.id
    username = message.from_user.username if message.from_user.username else "Неизвестный пользователь"
    amount = message.successful_payment.total_amount

    db.update_user_balance(cursor, user_id, username, amount * 10)
    conn.commit()

    bot.send_message(message.chat.id, f"✅ Платеж на сумму {amount:.2f} ⭐  принят, спасибо большое!")

@bot.message_handler(commands=['paysupport'])
def handle_pay_support(message):
    bot.send_message(
        message.chat.id,
        "Покупка доната не подразумевает возврат средств. "
        "Если у вас есть вопросы, пожалуйста, свяжитесь с нами."
    )

@bot.message_handler(commands=['job'])
def handle_job(message):
    user_id = message.from_user.id
    username = message.from_user.username if message.from_user.username else "Неизвестный пользователь"
    
    last_claim = db.get_last_claim(cursor, user_id)
    print(last_claim)
    now = datetime.now()
    
    if last_claim is None or (now - last_claim) >= timedelta(days=1):
        db.update_user_balance(cursor, user_id, username, 3)
        db.update_last_claim(cursor, user_id, now)
        conn.commit()
        bot.send_message(message.chat.id, "Вы получили 3 ⭐ за ежедневное задание!")
    else:
        next_claim = last_claim + timedelta(days=1)
        time_left = next_claim - now
        hours, remainder = divmod(time_left.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        bot.send_message(message.chat.id, f"Вы уже получили свою ежедневную награду. Попробуйте снова через {hours} ч {minutes} мин.")
        
@bot.message_handler(commands=['post'])
def posts(message):
  user_id = message.from_user.id
  username = message.from_user.username if message.from_user.username else "Неизвестный пользователь"
  command_parts = message.text.split()
  try:
    profile_photos = bot.get_user_profile_photos(user_id)
    if profile_photos.total_count > 0:
        file_id = profile_photos.photos[-1][-1].file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open(f'static/img/{user_id}.jpg', 'wb') as new_file:
          new_file.write(downloaded_file)
    post =  ' '.join(command_parts[1:])
    db.add_posts(cursor,user_id,username,post)
    conn.commit()
    bot.send_message(message.chat.id,"Опубликовано")
  except IndexError:
    bot.send_message(message.chat.id,"Добавь текст")
  
@bot.message_handler(commands=['slot'])
@anti_spam
def handle_slot(message):
  if is_private_chat(message):
    command_parts = message.text.split()
    try:
      bit = int(command_parts[1])
    except IndexError:
      return bot.send_message(message.chat.id,"Забыли указать ставку")
    user_id = message.from_user.id
    username = message.from_user.username if message.from_user.username else "Неизвестный пользователь"
    ball = db.get_user_balance(cursor,user_id)
    if ball > bit and len(command_parts) >= 1:
      db.update_user_balance(cursor, user_id, username,-bit)
      conn.commit()
      #Шансы
      probabilities = [
          (10 * bit , 0.01),  # 1% chance 
          (9 * bit, 0.10),   # 10% chance 
          (7 * bit, 0.20),   # 20% chance 
          (5 * bit, 0.30),   # 30% chance 
          (4 * bit, 0.40),   # 40% chance 
          (1 * bit, 0.50),   # 50% chance 
          (bit * 1, 0.60),   # 60% chance 
          (bit, 0.70),   # 70% chance 
          (bit, 0.80),   # 80% chance
          (0, 0.90)    # 90% chance 
      ]
      outcome = random.choices(
          [item[0] for item in probabilities],  # Values
          [item[1] for item in probabilities],  # Weights (probabilities)
          k=1
      )[0]
      db.update_user_balance(cursor, user_id, username, outcome)
      conn.commit()
      ball = db.get_user_balance(cursor,user_id)
      bot.send_message(message.chat.id, f"🎰 Результат: {outcome},Баланс:{ball}")
    else:
      bot.send_message(message.chat.id,f"У вас нет {bit} звезд для игры,или нет ставки /slot \"количество\"")
  else:
    bot.send_message(message.chat.id,"Чтобы не спамить в чатах,попробуй в личных сообщения с ботом")
    
removal_active = False

def delete_stickers_in_chat(chat_id):
    global removal_active
    removal_active = True
    end_time = time.time() + 600

    while time.time() < end_time:
        time.sleep(1)

    removal_active = False
    bot.send_message(chat_id, "Удаление стикеров завершено.")

@bot.message_handler(commands=['start_removal'])
def start_removal(message):
    global removal_active
    if not removal_active:
        threading.Thread(target=delete_stickers_in_chat, args=(message.chat.id,)).start()
        bot.send_message(message.chat.id, "Удаление стикеров запущено на 10 минут.")
    else:
        bot.send_message(message.chat.id, "Удаление стикеров уже активно.")

@bot.message_handler(content_types=['sticker'])
def handle_sticker(message):
    if removal_active:
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except Exception as e:
            print(f"Ошибка при удалении сообщения: {e}")

@bot.message_handler(commands=['use'])
@anti_spam
def handle_use(message):
    command_parts = message.text.split()
    print(command_parts)
    if len(command_parts) >= 4 or len(command_parts) <= 1:
        bot.send_message(message.chat.id, "Используйте формат команды: /use {предмет}")
        return
    item_name = command_parts[1] if len(command_parts) <= 2 else f"{command_parts[1]} {command_parts[2]}"
    user_id = message.from_user.id
    if db.use_item(cursor, user_id, item_name):
        conn.commit()
        bot.send_message(message.chat.id, f"Вы использовали предмет: {item_name}!")
        if item_name == "Vip":
          bot.send_message(message.chat.id, f"Напишите @claus_nori")
        elif item_name == "MuteBond":
          bot.send_message(message.chat.id, f"Напишите @claus_nori")
        elif item_name == "Warn":
          if message.reply_to_message and message.reply_to_message.from_user:
              tagged_user = message.reply_to_message.from_user
              username = tagged_user.username
              start_notify(message,username)
          else:
            bot.send_message(message.chat.id,"Нужно было использовать на чатере,ответив этим сообщением")
        elif item_name == "test":
          bot.send_message(message.chat.id, f"test)))")
        elif item_name == "NotStikers":
            bot.send_message(message.chat.id, f"Чат без стикеров на 10 минут")
            global removal_active
            removal_active = True
        else:
          bot.send_message(message.chat.id, f"У этой штуки нет способностей")
    else:
        bot.send_message(message.chat.id, "Предмет не найден в вашем инвентаре или вы не можете его использовать.")
        
active_users = set()
removal_time = 60  # 5 минут (300 секунд)

def notify_user(chat_id, username):
    end_time = time.time() + removal_time
    while time.time() < end_time:
        bot.send_message(chat_id, f"@{username} опасен для общества")
        time.sleep(10)

@bot.message_handler(commands=['start_notify'])
def start_notify(message,target_username):
    user_id = message.from_user.id

    if target_username not in active_users:
        active_users.add(target_username)
        threading.Thread(target=notify_user, args=(message.chat.id, target_username)).start()
        bot.send_message(message.chat.id, f"Удачи {target_username}.")
    else:
        bot.send_message(message.chat.id, f" {target_username} уже активно.")
        
        
bot.polling()