import requests
from openpyxl import Workbook
from tqdm import tqdm
from collections import defaultdict
from datetime import datetime

API_KEY = 'SE6CI5YJBUJJX39SK9S3B3KWNH8194P222'
BASE_URL = 'https://api.scrollscan.com/api'
EXCEL_FILE = 'stats.xlsx'

# Функция для получения текущей цены эфира
def get_current_eth_price():
    url = 'https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd'
    response = requests.get(url)
    response.raise_for_status()  # Проверка на ошибку запроса
    price_data = response.json()
    return price_data['ethereum']['usd']

# Получение текущей цены эфира
ETHER_PRICE = get_current_eth_price()

contract_interactions = {
    'AAVE': {'address': '0xFF75A4B698E3Ec95E608ac0f22A03B8368E05F5D', 'count': 0},
    'Ambient': {'address': '0xaaaaAAAACB71BF2C8CaE522EA5fa455571A74106', 'count': 0},
    'CogFinance': {'address': '0x6ACE91e105Cd5288DC46598E96538e9AD0e421Aa', 'count': 0},
    'Compound': {'address': '0x53C6D04e3EC7031105bAeA05B36cBc3C987C56fA', 'count': 0},
    'KeplDao': {'address': '0xb80deaecd7F4Bca934DE201B11a8711644156a0a', 'count': 0},
    'LayerBank': {'address': '0xEC53c830f4444a8A56455c6836b5D2aA794289Aa', 'count': 0},
    'Loanshark': {'address': '0xF017f9CF11558d143E603d56Ec81E4E3B6d39D7F', 'count': 0},
    'Meowprotocol': {'address': '0xCA8edCC306119143DD010A1d61F31c3380f409bb', 'count': 0},
    'PunkSwap': {'address': '0x26cB8660EeFCB2F7652e7796ed713c9fB8373f8e', 'count': 0},
    'SkyDrome': {'address': '0x03290A52BA3164639067622E20B90857eADed299', 'count': 0},
    'Zksynth': {'address': '0x78B2fa94A94bF3E96fcF9CE965bed55bE49FA9E7', 'count': 0},
    'DMAIL': {'address': '0x47fbe95e981c0df9737b6971b451fb15fdc989d9', 'count': 0},
    'RUBYSCORE': {'address': '0xe10Add2ad591A7AC3CA46788a06290De017b9fB4', 'count': 0},
    'SyncSwap': {'address': '0x80e38291e06339d10aab483c65695d004dbd5c69', 'count': 0},
    'Bridge Withdraw': {'address': '0x781e90f1c8Fc4611c9b7497C3B47F99Ef6969CbC', 'count': 0},
    'Zerius': {'address': '0xeb22c3e221080ead305cae5f37f0753970d973cd', 'count': 0},
    'Gnosis Safe': {'address': '0xa6B71E26C5e0845f74c812102Ca7114b6a896AB2', 'count': 0},
    'Hyperlane': {'address': '0x904550e0D182cd4aEe0D305891c666a212EC8F01', 'count': 0}
}

def get_eth_balance(wallet_address):
    url = f"{BASE_URL}?module=account&action=balance&address={wallet_address}&apikey={API_KEY}"
    response = requests.get(url)
    response.raise_for_status()  # Проверка на ошибку запроса
    balance = response.json()
    eth_balance = int(balance['result']) / 10**18  # Переводим значение в эфир
    return eth_balance

def get_token_balance(wallet_address, token_address):
    url = f"{BASE_URL}?module=account&action=tokenbalance&contractaddress={token_address}&address={wallet_address}&tag=latest&apikey={API_KEY}"
    response = requests.get(url)
    response.raise_for_status()  # Проверка на ошибку запроса
    balance = response.json()
    token_balance = int(balance['result']) / 10**6  # Переводим значение в токены (предполагая 18 знаков после запятой)
    return token_balance

def parse_data(wallet_address):
    url = f"https://kx58j6x5me.execute-api.us-east-1.amazonaws.com/scroll/wallet-points?walletAddress={wallet_address}"
    try:
        response = requests.get(url)
        data = response.json()
        points_sum = sum(item.get("points", 0) for item in data)  # Суммируем значения points из каждого объекта
        return points_sum
    except Exception as e:
        return f"Error: {e}"

def get_transactions(wallet_address):
    url = f"{BASE_URL}?module=account&action=txlist&address={wallet_address}&startblock=0&endblock=99999999&sort=asc&apikey={API_KEY}"
    response = requests.get(url)
    response.raise_for_status()  # Проверка на ошибку запроса
    transactions = response.json()
    unique_contracts = set()  # Множество уникальных контрактов
    total_contracts = 0
    activity_by_month = defaultdict(int)
    activity_by_week = defaultdict(int)
    activity_by_day = defaultdict(int)
    total_eth_volume = 0

    if 'result' in transactions and transactions['result']:
        for tx in transactions['result']:
            unique_contracts.add(tx['to'].lower())
            total_contracts += 1
            total_eth_volume += int(tx['value']) / 10**18  # Переводим значение в эфир
            # Получаем дату транзакции
            timestamp = int(tx['timeStamp'])
            tx_date = datetime.utcfromtimestamp(timestamp)
            # Считаем активность по месяцам
            activity_by_month[(tx_date.year, tx_date.month)] += 1
            # Считаем активность по неделям
            activity_by_week[(tx_date.year, tx_date.isocalendar()[1])] += 1
            # Считаем активность по дням
            activity_by_day[(tx_date.year, tx_date.month, tx_date.day)] += 1
            # Проверяем взаимодействие с контрактами из словаря
            for contract_name, contract_info in contract_interactions.items():
                if tx['to'].lower() == contract_info['address'].lower():
                    contract_interactions[contract_name]['count'] += 1

    # Получаем баланс ETH, USDT и USDC для текущего кошелька
    eth_balance = get_eth_balance(wallet_address)
    usdt_balance = get_token_balance(wallet_address, '0xf55BEC9cafDbE8730f096Aa55dad6D22d44099Df')
    usdc_balance = get_token_balance(wallet_address, '0x06eFdBFf2a14a7c8E15944D1F4A48F9F95F663A4')


    return eth_balance, usdt_balance, usdc_balance, total_contracts, total_eth_volume, len(unique_contracts), len(activity_by_month), len(activity_by_week), len(activity_by_day), list(contract_interactions.values())

# Чтение адресов кошельков из файла
with open('wallets.txt', 'r') as file:
    wallet_addresses = [line.strip() for line in file]

wb = Workbook()
ws = wb.active
ws.append(['Number', 'Wallet', 'ETH Balance', 'USDT Balance', 'USDC Balance', 'Total TX', 'Total USD Volume', 'Unique Contracts', 'Active Months', 'Active Weeks', 'Active Days', 'Points'])

progress_bar = tqdm(total=len(wallet_addresses), desc='Processing wallets', position=0, leave=True)

for idx, wallet_address in enumerate(wallet_addresses, start=1):
    try:
        points_sum = parse_data(wallet_address)
        eth_balance, usdt_balance, usdc_balance, total_tx, total_eth_volume, unique_contracts, active_months, active_weeks, active_days, contract_counts = get_transactions(wallet_address)
        row_data = [idx, wallet_address, eth_balance, usdt_balance, usdc_balance, total_tx, total_eth_volume * ETHER_PRICE, unique_contracts, active_months, active_weeks, active_days, points_sum]
        ws.append(row_data)
    except Exception as e:
        print(f"Ошибка при обработке кошелька {wallet_address}: {str(e)}")
    finally:
        progress_bar.update(1)

progress_bar.close()
wb.save(EXCEL_FILE)
