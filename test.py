import requests
import logging

url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
params = {"vs_currency": "pln", "days": 1, "interval": "daily"}

try:
    resp = requests.get(url, params=params, timeout=10)  # set a timeout in seconds
    print("Status code:", resp.status_code)
    print("Response text (first 200 chars):", resp.text[:200])

    resp.raise_for_status()  # will raise HTTPError for 4xx/5xx
    data = resp.json()
    print("Keys in response:", data.keys())
except requests.exceptions.Timeout:
    print("Timeout occurred!")
except requests.exceptions.HTTPError as e:
    print("HTTP error occurred:", e)
except requests.exceptions.RequestException as e:
    print("Other request exception:", e)
