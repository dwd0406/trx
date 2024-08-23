import requests
from datetime import datetime
import asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
import telegram.constants
import re


API_KEY = ''
WALLET_ADDRESS = ''
TELEGRAM_TOKEN = ''
CHAT_ID = ''
#https://www.trongrid.io/

def is_url(string):
    url_regex = re.compile(r'^(?:http|ftp)s?://' 
                           r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' 
                           r'localhost|'  
                           r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  
                           r'\[?[A-F0-9]*:[A-F0-9:]+\]?)' 
                           r'(?::\d+)?'  
                           r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(url_regex, string) is not None

async def send_telegram_message(data, message):
    bot = Bot(token=TELEGRAM_TOKEN)
    
    bot_button = [
        InlineKeyboardButton("SunPump BOT", url=f"https://t.me/tron_trading_bot?start={data['contractAddress']}"),
        InlineKeyboardButton("MAESTRO BOT", url=f"https://t.me/maestro?start={data['contractAddress']}"),
        InlineKeyboardButton("SUNDOG BOT", url=f"https://t.me/sundog_trade_bot?start={data['contractAddress']}"),
    ]
    bot_button3 = [
        InlineKeyboardButton("Ave.ai", url=f"https://ave.ai/token/{data['contractAddress']}-tron?from=Default"),
        InlineKeyboardButton("Sunpump.meme", url='https://sunpump.meme/token/' + data['contractAddress']),
    ]
    keyboard = []
    

    reply_markup = InlineKeyboardMarkup([keyboard, bot_button3, bot_button])
    try:
        chat_id = CHAT_ID
        await bot.send_message(chat_id=chat_id, text=message, parse_mode=telegram.constants.ParseMode.HTML, reply_markup=reply_markup)
        print(f"Notification sent to Telegram group with buttons")
    except Exception as e:
        print(f"Failed to send message: {e}")

def get_transactions(wallet_address):
    url = f"https://api.trongrid.io/v1/accounts/{wallet_address}/transactions/trc20"
    headers = {
        'Accept': 'application/json',
        'TRON-PRO-API-KEY': API_KEY
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json().get('data', [])
    except requests.exceptions.RequestException as e:
        print(f"Failed to get transactions for wallet {wallet_address}: {e}")
        return []

def get_transaction_info(tx_id): 
    url = f"https://api.trongrid.io/v1/transactions/{tx_id}" 
    headers = {
        'Accept': 'application/json',
        'TRON-PRO-API-KEY': API_KEY
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data['raw_data']['contract'][0]['parameter']['value'].get('amount', 0) / 1e6
    except requests.exceptions.RequestException as e:
        print(f"Failed to get transaction info for TX ID {tx_id}: {e}")
        return 0

def is_new_transaction(transaction, last_transaction_id):
    return transaction['transaction_id'] != last_transaction_id

def determine_transaction_type(transaction, wallet_address):
    from_address = transaction.get('from', '')
    to_address = transaction.get('to', '')
    if from_address == wallet_address:
        return 'Sell'
    elif to_address == wallet_address:
        return 'Buy'
    else:
        return 'Unknown'

async def monitor_wallet(wallet_address):
    print(f"Monitoring wallet: {wallet_address} for token purchases...") 
    last_transaction_id = None 

    while True:
        transactions = get_transactions(wallet_address)
        if transactions:
            latest_transaction = transactions[0]

            if is_new_transaction(latest_transaction, last_transaction_id):
                transaction_type = determine_transaction_type(latest_transaction, wallet_address)
                token_info = latest_transaction.get('token_info', {})
                token_address = token_info.get('address', 'Unknown')
                token_name = token_info.get('name', 'Unknown')
                token_symbol = token_info.get('symbol', 'Unknown')
                transaction_time = datetime.fromtimestamp(int(latest_transaction['block_timestamp']) / 1000)
                transaction_hash = latest_transaction.get('transaction_id', 'Unknown')
                trx_url = f"https://tronscan.org/#/transaction/{transaction_hash}"
                
                message = (
                    f"{transaction_time}\n"
                    f"{transaction_type}\n"
                    f"name: {token_name}\n"
                    f"ticker: ({token_symbol})\n"
                    f"TokenCA:\n<pre>{token_address}</pre>\n"
                    f"{trx_url}"
                )
                
                data = {
                    'contractAddress': token_address,
                    'name': token_name,
                }

                await send_telegram_message(data, message)
                
                last_transaction_id = latest_transaction['transaction_id']
        else:
            print("No transactions found or an error occurred.")
        
        await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(monitor_wallet(WALLET_ADDRESS))
    except Exception as e:
        print(f"An unexpected error occurred: {e}")