# pip install pybit pyTelegramBotAPI
import telebot
from pybit.unified_trading import HTTP
import json
import os
import time
import threading
from decimal import Decimal
import requests, re, time
from telethon import TelegramClient, events
import re
import asyncio


#тг бот
TOKEN = "7507620983:AAG352JQufEp-mq0fs98ZTNq_AMPl1X_sKs"
bot = telebot.TeleBot(TOKEN)

#путь для сохранения данных юзеров
USER_DATA_PATH = "user_data"
os.makedirs(USER_DATA_PATH, exist_ok=True)

#API ID и API Hash на https://my.telegram.org
api_id = 29128603
api_hash = '5cb863ca1aef0ae8b0db2e0d80f1a5d8'
telethon_client = TelegramClient('Bybit_Announcements', api_id, api_hash)


# Список для хранения последних обработанных постов, чтобы не дублировать
seen_messages = set()

#настройки юзера
user_states = {}



#MATH
def count_decimal_places(number: float) -> int:
    s = f"{number:.16f}".rstrip('0')  # преобразуем с запасом знаков, убираем хвостящие нули
    if '.' in s:
        return len(s.split('.')[1])
    else:
        return 0
    
    
#GET USER + SAVE USER INFO
# ======================================================================================================================
def get_user_file(user_id):
    return os.path.join(USER_DATA_PATH, f"{user_id}.json")

def load_user_data(user_id):
    try:
        with open(get_user_file(user_id), 'r') as f:
            return json.load(f)
    except:
        return {}

def save_user_data(user_id, data):
    with open(get_user_file(user_id), 'w') as f:
        json.dump(data, f)


def get_all_user_ids():
    user_ids = []
    for filename in os.listdir(USER_DATA_PATH):
        if filename.endswith(".json"):
            try:
                user_id = int(filename.split(".")[0])
                user_ids.append(user_id)
            except:
                continue
    return user_ids


def notify_all_enabled_users(token):
    user_ids = get_all_user_ids()
    for uid in user_ids:
        data = load_user_data(uid)
        if data.get("bot_enabled"):
            execute_short_from_news(uid, token_symbol=token)
#============================================================================================================================
def get_menu_markup(user_id):
    data = load_user_data(user_id)
    bot_enabled = data.get("bot_enabled", False)
    state_button = "🟢 Бот включен" if bot_enabled else "🔴 Бот выключен"

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(state_button, "ℹ️ Информация о боте")
    markup.row("⚙️ Настройки")
    return markup




settings_markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
settings_markup.row("API Key", "Secret key")
settings_markup.row("Leverage", "Margin")
settings_markup.row("Stop", "Take")
settings_markup.row("Назад")





#КОМАНДЫ ДЛЯ БОТА
#=======================================================================================================================                         
@bot.message_handler(func=lambda msg: msg.text in ["🟢 Бот включен", "🔴 Бот выключен"])
def toggle_bot_state(message):
    user_id = message.chat.id
    data = load_user_data(user_id)
    current_state = data.get("bot_enabled", False)
    data["bot_enabled"] = not current_state
    save_user_data(user_id, data)
    
    status = "включен" if data["bot_enabled"] else "выключен"
    bot.send_message(user_id, f"Бот теперь {status}.", reply_markup=get_menu_markup(user_id))




@bot.message_handler(func=lambda msg: msg.text == "ℹ️ Информация о боте")
def bot_info(message):
    user_id = message.chat.id
    info_text = (
        "Это торговый бот для биржи Bybit, торгующий по новостям с сайта Binance.\n"
        "Вы можете включать и выключать бота, а также настраивать параметры в разделе Настройки. Для грамотной работы бота необходимо обязательно указать всё, кроме take и stop.\n"
        "Если нужна помощь — обращайтесь @perpetual_god."
    )
    bot.send_message(user_id, info_text, reply_markup=get_menu_markup(user_id))

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    bot.send_message(user_id, "Добро пожаловать! Выберите действие:", reply_markup=get_menu_markup(user_id))
 
    threading.Thread(target=news_watcher, args=(user_id,), daemon=True).start()

@bot.message_handler(func=lambda msg: msg.text in ["⚙️ Настройки"])
def handle_settings_menu(message):
    user_id = message.chat.id
    bot.send_message(user_id, "Выберите параметр:", reply_markup=settings_markup)

@bot.message_handler(func=lambda msg: msg.text in ["API Key", "Secret", "Leverage", "Margin", "Stop", "Take"])
def ask_for_value(message):
    user_id = message.chat.id
    key = message.text.lower().replace(" ", "_")
    
    data = load_user_data(user_id)
    current_value = data.get(key, "(не задано)")
    
    user_states[user_id] = key
    if message.text == 'Stop' or message.text == 'Take':
        bot.send_message(user_id, f"Установленный {message.text} для позиции: {current_value}% чистого движения\n\nВведите новое значение:")
    else:
        bot.send_message(user_id, f"Текущее значение {message.text}: {current_value}\n\nВведите новое значение:")



@bot.message_handler(func=lambda msg: msg.text == "Назад")
def back_to_menu(message):
    user_id = message.chat.id
    bot.send_message(user_id, "Вы вернулись в меню", reply_markup=get_menu_markup(user_id))
#============================================================================================================================



def get_time_diff():
    session = HTTP()
    resp = session.get_server_time()
    print("Ответ сервера:", resp)
    if resp['retCode'] == 0:
        time_now = float(resp['result']['timeSecond'])
        local_time = time.time()
        return time_now - local_time
    else:
        raise Exception(f"Ошибка получения времени сервера: {resp['retMsg']}")

time_difference = get_time_diff()
print(f"Смещение времени: {time_difference:.3f} секунд")


#PARESER
#==========================================================================================================================#

def get_latest_article_code():
    url = "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query?type=1&catalogId=161&pageSize=1&pageNo=1"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Referer": "https://www.binance.com"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"⚠️ Ошибка запроса: {response.status_code}")
            print(f"➡️ Raw content: {response.text}")
            return None
        data = response.json()
        catalogs = data.get("data", {}).get("catalogs", [])
        if catalogs and "articles" in catalogs[0]:
            return catalogs[0]["articles"][0]["code"]
        else:
            raise ValueError("⚠️ 'articles' не найден в ответе Binance")
    except Exception as e:
        print("⚠️ Ошибка при запросе к Binance (get_latest_article_code):", e)
        return None



def get_article_text(code):
    url = f"https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query?articleCode={code}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin": "https://www.binance.com",
        "Referer": "https://www.binance.com/",
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        if 'data' in data and 'body' in data['data']:
            return data['data']
        else:
            raise ValueError("⛔ 'body' отсутствует в ответе Binance")
    except Exception as e:
        print("Ошибка при получении статьи:", e)
        return {}
    
def extract_text_from_body(body_raw):
    try:
        body_json = json.loads(body_raw)
    except json.JSONDecodeError as e:
        print("❌ Ошибка декодирования JSON:", e)
        return ""

    def recurse_extract(node):
        if isinstance(node, dict):
            if node.get("node") == "text":
                return node.get("text", "")
            elif "child" in node:
                return "".join([recurse_extract(child) for child in node["child"]])
            else:
                return ""
        elif isinstance(node, list):
            return "".join([recurse_extract(child) for child in node])
        else:
            return ""

    return recurse_extract(body_json)


def _traverse_nodes(node):
    if not isinstance(node, dict):
        return ""

    text = ""
    if node.get("node") == "text":
        return node.get("text", "")
    elif "child" in node:
        for child in node["child"]:
            text += _traverse_nodes(child)
    return text


def extract_text_nodes(node):
    if isinstance(node, dict):
        if node.get("node") == "text":
            return node.get("text", "")
        elif node.get("child"):
            return " ".join(extract_text_nodes(child) for child in node["child"])
    elif isinstance(node, list):
        return " ".join(extract_text_nodes(item) for item in node)
    return ""


# ←——— ИЗВЛЕЧЕНИЕ ТИКЕРОВ
def extract_usdt_pairs(text):

    # Ищем как "ALPHA/USDT"
    pairs = set(re.findall(r'\b([A-Z0-9\-]{3,})/USDT\b', text))

    # Также ищем одиночные токены в верхнем регистре, исключая дубли и общие слова
    tickers = set(re.findall(r'\b([A-Z]{3,})\b', text))

    # Фильтруем явно не тикеры (по длине, например)
    common_words = {"USDT", "USD", "BTC", "ETH", "NFT", "API", "KYC", "APR"}
    filtered_tickers = {t for t in tickers if 3 <= len(t) <= 6 and t not in common_words}

    return list(pairs.union(filtered_tickers))




#==========================================================================================================================#
#ПАРСЕР @BYBIT_ANNOUNCEMENTS



#==========================================================================================================================#

def execute_trade(message):
    side = "Buy" if message.text == "Покупка" else "Sell"
    user_id = message.chat.id
   
    try:
        data = load_user_data(user_id)
        session = HTTP(api_key=data['api_key'], api_secret=data['secret_key'], recv_window=30000)

        leverage = int(data.get("leverage", 5))
        margin = float(data.get("margin", 10))
        stop_pct = float(data.get("stop", 1)) / 100
        take_pct = float(data.get("take", 2)) / 100

        
        
        #/Получаем цену
        ticker = session.get_tickers(category="linear", symbol="ETHUSDT")
        mark_price = float(ticker['result']['list'][0]['lastPrice'])

        qty = round(float(margin) / mark_price, 4)
        stop_price = mark_price * (1 - stop_pct if side == "Buy" else 1 + stop_pct)
        take_price = mark_price * (1 + take_pct if side == "Buy" else 1 - take_pct)


        
        
      

        
        bot.send_message(user_id, f"✅ Сделка {side} выполнена по цене {mark_price:.2f}")
    except Exception as e:
        bot.send_message(user_id, f"❌ Ошибка: {e}")


def get_valid_qty(session, symbol, raw_qty):
    try:
        info = session.get_instruments_info(category="linear", symbol=symbol)
        
        if 'result' not in info or 'list' not in info['result'] or not info['result']['list']:
            print(f"❌ Пара {symbol} не найдена в get_instruments_info.")
            return None

        lot_filter = info['result']['list'][0].get('lotSizeFilter', {})
        step = float(lot_filter.get('qtyStep', 0))
        min_qty = float(lot_filter.get('minOrderQty', 0))

        if step == 0:
            print(f"❌ qtyStep равен 0 для {symbol}")
            return None

        qty = max(raw_qty, min_qty)
        precision = abs(Decimal(str(step)).as_tuple().exponent)
        valid_qty = round(qty, precision-1)
        
        
        return valid_qty
    except Exception as e:
        print(f"⚠️ Ошибка получения допустимого объема для {symbol}: {e}")
        return None
    

def execute_short_from_news(user_id, token_symbol):
    try:
        data = load_user_data(user_id)
        session = HTTP(api_key=data['api_key'], api_secret=data['secret_key'], recv_window=30000)

        symbol = f"{token_symbol}USDT"

        # Проверка доступности на Bybit
        res = session.get_tickers(category="linear", symbol=symbol)
        if not res.get("result", {}).get("list"):
            print(f"⛔ {symbol} не найден на Bybit")
            return

        price = float(res['result']['list'][0]['lastPrice'])
        leverage = int(data.get("leverage", 5))
        margin = float(data.get("margin", 10))


        stop_pct = float(data.get("stop", 1)) / 100
        take_pct = float(data.get("take", 2)) / 100

        raw_qty = leverage * margin / price
        qty = get_valid_qty(session, symbol, raw_qty)
        
        precision = int(count_decimal_places(price))



        if qty is None:
            bot.send_message(user_id, f"❌ Не удалось определить допустимый объем для {symbol}")
            return
        stop_price = round(price * (1 + stop_pct), precision)
        take_price = round(price * (1 - take_pct), precision)

        order = session.place_order(
            category="linear",
            symbol=symbol,
            order_type="Market",
            side = 'Sell',
            qty=qty,
            leverage=leverage,
            takeProfit=  take_price,
            stopLoss=stop_price,
            position_idx=0,
        )

        bot.send_message(user_id, f"🔻 SHORT по {symbol} выполнен по цене {price:.2f}")
    except Exception as e:
        bot.send_message(user_id, f"❌ Ошибка при SHORT по {token_symbol}: {e}")

def news_watcher(user_id):
    last_code = get_latest_article_code()

    while True:
        try:
            #print('🔍 Ожидание новых новостей...')
            code = get_latest_article_code()
            if not code:
                #print("🔍 Ожидание новых новостей...")
                time.sleep(10)
                continue


            if code and code != last_code:
                print(f"🆕 Найдена новая статья: {code}")
                article = get_article_text(code)
                body_raw = article.get("body", "")
                article_text = extract_text_from_body(body_raw)
                tickers = extract_usdt_pairs(article_text)
               
                for token in tickers:
                    print('executing tradde')
                    execute_short_from_news(user_id, token_symbol=token)

                last_code = code
            time.sleep(5)  # реже, чтобы не получить 429
        except Exception as e:
            print("❌ Ошибка в news_watcher:", e)
            time.sleep(5)





 

    


# запуск Telethon один раз в фоне
def start_telethon():
    async def main():
        await telethon_client.start()
        print("Telethon запущен")

        @telethon_client.on(events.NewMessage(chats='@Bybit_Announcements'))
        async def handler(event):
            text = event.raw_text
            if text in seen_messages:
                return
            seen_messages.add(text)

            if text.startswith("📢 Delisting of"):
                matches = re.findall(r'\$([A-Z0-9]+)', text)
                for token in matches:
                    notify_all_enabled_users(token)

        await telethon_client.run_until_disconnected()

    loop = asyncio.new_event_loop()
    threading.Thread(target=loop.run_until_complete, args=(main(),), daemon=True).start()

start_telethon()



#ПОЛУЧЕНИЕ БОТОВ СООБЩЕНИЕ И ЗАПУСК
@bot.message_handler(func=lambda msg: True)
def catch_input(message):
    user_id = message.chat.id
    if user_id in user_states:
        key = user_states.pop(user_id)
        data = load_user_data(user_id)
        data[key] = message.text
        save_user_data(user_id, data)
        bot.send_message(user_id, f"{key} сохранено. Выберите следующий параметр:", reply_markup=settings_markup)





bot.polling(none_stop=True)