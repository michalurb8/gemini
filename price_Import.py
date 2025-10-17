import requests
import datetime, time
import logging
from azure.cosmosdb.table import TableService
from keys import ConnectionString
from logger_util import setup_logger; setup_logger('price_Import.log')

# -----------------------------
# CONSTANTS
# -----------------------------
TABLE_NAME = "exchangeRate"
CURRENCY = "pln"
coin_map = {
    "bitcoin": "BTCPLN",
    "ethereum": "ETHPLN"
}

def get_latest_date_in_table(table_service: TableService, table_name="exchangeRate"):
    """
    Returns the latest date (datetime.date) present in the table,
    checking the current month and previous month partitions.
    """
    
    today = datetime.date.today()
    # current month and previous month
    months_to_check = [
        today.strftime("%Y%m"),
        (today.replace(day=1) - datetime.timedelta(days=1)).strftime("%Y%m")
    ]

    latest_date = None

    for partition_key in months_to_check:
        try:
            entities = table_service.query_entities(
                table_name,
                filter=f"PartitionKey eq '{partition_key}'"
            )
            for e in entities:
                # RowKey is YYYYMMDD as string
                row_date = datetime.datetime.strptime(e.RowKey, "%Y%m%d").date()
                if latest_date is None or row_date > latest_date:
                    latest_date = row_date
        except Exception as ex:
            # If partition doesn't exist or table missing, skip
            continue

    return latest_date

# -----------------------------
# FUNCTION TO FETCH DAILY AVERAGE PRICE
# -----------------------------
def get_avg_price(coin, currency="pln", target_date: datetime.date = None, max_retries=5, backoff_coef=1.5):
    """
    Fetch daily average price for a coin from CoinGecko for a specific date.
    Retries on network errors, timeouts, or HTTP 429 (rate limit).
    """

    if target_date is None:
        target_date = datetime.date.today()

    logging.info(f'trying to get prices for {target_date}')

    # Convert date to UNIX timestamps (seconds)
    start_ts = int(datetime.datetime.combine(target_date, datetime.time.min).timestamp())
    end_ts = int(datetime.datetime.combine(target_date, datetime.time.max).timestamp())

    wait = 5  # initial wait in seconds

    for attempt in range(1, max_retries + 1):
        try:
            url = f"https://api.coingecko.com/api/v3/coins/{coin}/market_chart/range"
            resp = requests.get(
                url,
                params={"vs_currency": currency, "from": start_ts, "to": end_ts},
                timeout=10
            )

            if resp.status_code == 429:
                print('429 :C')
                raise requests.exceptions.RequestException("Rate limit hit (429)")

            resp.raise_for_status()  # raise HTTPError for other 4xx/5xx

            prices = resp.json().get("prices", [])
            if not prices:
                logging.warning(f"No price data returned for {coin} on {target_date}")
                return None

            avg_price = sum(p[1] for p in prices) / len(prices)
            logging.info(f"{coin.upper()} avg {currency.upper()} for {target_date}: {avg_price:.2f}")
            return avg_price

        except (requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
            logging.warning(f"Attempt {attempt} for {coin} on {target_date} failed: {e}. Retrying in {wait:.1f}s...")
            time.sleep(wait)
            wait *= backoff_coef

    logging.error(f"Failed to fetch {coin} price for {target_date} after {max_retries} attempts")
    return None

# -----------------------------
# FUNCTION TO UPSERT PRICES FOR A GIVEN DATE WITH RETRY
# -----------------------------
def upsert_prices_for_date(target_date: datetime.date, table_service: TableService):
    """
    Fetch BTC/ETH prices for the given date and upsert into Azure Table.
    Assumes get_avg_price handles retries/backoff.
    Returns True if successful, False otherwise.
    """
    logging.info(f'trying to upsert for {target_date}')
    # -----------------------------
    # FETCH PRICES
    # -----------------------------
    prices = {}
    for coin, col_name in coin_map.items():
        avg = get_avg_price(coin, CURRENCY, target_date)
        if avg is None:
            logging.error(f"Skipping upsert due to missing price for {coin} on {target_date}")
            return False
        prices[col_name] = avg

    # -----------------------------
    # BUILD ENTITY
    # -----------------------------
    partition_key = target_date.strftime("%Y%m")
    row_key = target_date.strftime("%Y%m%d")
    entity = {"PartitionKey": partition_key, "RowKey": row_key}
    entity.update(prices)

    # -----------------------------
    # UPSERT ENTITY
    # -----------------------------
    try:
        table_service.insert_or_replace_entity(TABLE_NAME, entity, timeout=None)
        logging.info(f"Successfully upserted prices for {target_date}")
        return True
    except Exception as e:
        logging.error(f"Failed to upsert entity for {target_date}: {e}")
        return False

if __name__ == "__main__":

    table_service = TableService(endpoint_suffix="table.cosmos.azure.com", connection_string=ConnectionString)

    if not table_service.exists(TABLE_NAME):
        logging.error(f"Table {TABLE_NAME} does not exist")
        exit(1)

    upsert_prices_for_date(datetime.datetime(2024, 9, 1), table_service)
    exit()

    latest = get_latest_date_in_table(table_service)
    logging.info(f'got latest date: {latest}')
    
    if latest is None:
        start_date = datetime.date.today() - datetime.timedelta(days=7)
    else:
        start_date = latest + datetime.timedelta(days=1)

    end_date = datetime.date.today()

    logging.info(f'got both dates: {start_date, end_date}')

    for n in range((end_date - start_date).days + 1):
        current_date = start_date + datetime.timedelta(days=n)
        logging.info(f'got current_date: {current_date}')
        upsert_prices_for_date(current_date, table_service)
    
# handle backfilling data from 2024 and 2025
# schedule daily
# fix other scripts as well