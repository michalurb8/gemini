import requests
import datetime

def get_daily_price(coin="bitcoin", currency="eur"):
    url = f"https://api.coingecko.com/api/v3/coins/{coin}/market_chart"
    params = {"vs_currency": currency, "days": 1, "interval": "daily"}
    r = requests.get(url, params=params)
    data = r.json()

    # API zwraca listę [timestamp, price]
    prices = data["prices"]
    avg_price = sum([p[1] for p in prices]) / len(prices)

    return avg_price

print("BTC avg EUR:", get_daily_price("bitcoin", "eur"))
print("ETH avg EUR:", get_daily_price("ethereum", "eur"))


import requests
 
def get_btc_balance(address = "bc1q63ry55nmpmgzg3j3t9dy67e2z2y323x8pdey8p"):
    url = f"https://blockchain.info/rawaddr/{address}"
    response = requests.get(url)
    data = response.json()
    balance_satoshi = data['final_balance']
    balance_btc = balance_satoshi / 100000000  # konwersja na BTC
    print(url)
    return balance_btc

balance = get_btc_balance()
print(f"Saldo BTC: {balance} BTC")


# API Key to infura: 84343e58571d4bf9951a6efb068cc0cb
# HTTPS Infura: https://mainnet.infura.io/v3/84343e58571d4bf9951a6efb068cc0cb



from web3 import Web3

# Replace YOUR_PROJECT_ID with your Infura project ID
INFURA_URL = "https://mainnet.infura.io/v3/84343e58571d4bf9951a6efb068cc0cb"

# Connect to Ethereum via Infura
w3 = Web3(Web3.HTTPProvider(INFURA_URL))

# Your Ethereum address (from Metamask)
eth_address = "0x8dfc02280559B33c8af2C8517d8D0Ee4B1d2Fa34"

# Get balance in wei
balance_wei = w3.eth.get_balance(eth_address)

# Convert wei to ETH
balance_eth = w3.from_wei(balance_wei, "ether")

print(f"ETH balance: {balance_eth} ETH")
