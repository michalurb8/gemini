import requests
import datetime, time
import logging
from azure.cosmosdb.table import TableService
from keys import ConnectionString, coinbase_api_key
from logger_util import setup_logger

setup_logger('backfill_prices.log')

# -----------------------------
# CONSTANTS
# -----------------------------
TABLE_NAME = "exchangeRate"
CURRENCY = "pln"
coin_map = {
    "bitcoin": "BTCPLN",
    "ethereum": "ETHPLN"
}

# -----------------------------
# TABLE HELPERS
# -----------------------------
def get_latest_date_in_table(table_service: TableService, table_name=TABLE_NAME):
    """
    Returns the latest date (datetime.date) present in the table,
    checking the current month and previous month partitions.
    """
    today = datetime.date.today()
    months_to_check = [
        today.strftime("%Y%m"),
        (today.replace(day=1) - datetime.timedelta(days=1)).strftime("%Y%m")
    ]

    latest_date = None
    for partition_key in months_to_check:
        try:
            entities = table_service.query_entities(
                table_name,
#                filter=f"PartitionKey eq '{partition_key}'"
                filter=f"PartitionKey eq '202411'"
            )
            for e in entities:
                row_date = datetime.datetime.strptime(e.RowKey, "%Y%m%d").date()
                if latest_date is None or row_date > latest_date:
                    latest_date = row_date
        except Exception:
            continue
    return latest_date

def upsert_entity(table_service: TableService, target_date: datetime.date, prices: dict):
    try:
        partition_key = target_date.strftime("%Y%m")
        row_key = target_date.strftime("%Y%m%d")
        entity = {"PartitionKey": partition_key, "RowKey": row_key}
        entity.update(prices)
        table_service.insert_or_replace_entity(TABLE_NAME, entity, timeout=None)
        logging.info(f"Successfully upserted prices for {target_date}")
        return True
    except Exception as e:
        logging.exception(f"Failed to upsert entity for {target_date}: {e}")
        return False

# -----------------------------
# COINGECKO FETCHING
# -----------------------------
def fetch_coin_history(coin='bitcoin', currency='pln', target_date=None, max_retries=5, backoff_coef=1.1):
    wait = 20
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(
                f"https://api.coingecko.com/api/v3/coins/{coin}/history",
                headers={"X-CoinGecko-Api-Key": coinbase_api_key},
                params={"date": target_date, "localization": "false"},
                timeout=10
            )
            response.raise_for_status()
            price = response.json()["market_data"]["current_price"].get(currency)
            if price is None:
                logging.warning(f"No price data returned for {coin} for {target_date}")
                return None
            logging.info(f"Fetched price for {coin} on {target_date}: {price} {currency.upper()}")
            return price
        except Exception as e:
            logging.warning(f"Attempt {attempt} failed for {coin} for {target_date}: {e}. Retrying in {wait}s...")
            print(f"Attempt {attempt} failed for {coin} for {target_date}:\n{e}.\nRetrying in {wait}s...\n")
            time.sleep(wait)
            wait *= backoff_coef
    logging.error(f"Failed to fetch {coin} price for {target_date} after {max_retries} attempts")
    return None

# -----------------------------
# MAIN BACKFILL FUNCTION
# -----------------------------
def backfill_prices(table_service: TableService):
    try:
        latest = get_latest_date_in_table(table_service)
        logging.info(f"Latest date in table: {latest}")
        today_utc = datetime.datetime.now(datetime.timezone.utc).date()
        current_date = latest if latest else datetime.datetime(2024, 10, 18).date()

        end_date = today_utc

        logging.info(f"current_date: {current_date}, today_UTC: {today_utc}")
        while current_date <= end_date:

            try:
                coin_daily_data = {}
                for coin, col_name in coin_map.items():
                    raw_price = fetch_coin_history(coin, CURRENCY, current_date.strftime("%d-%m-%Y"))
                    if raw_price is None:
                        logging.error(f"Skipping {coin} due to missing data on {current_date}")
                        continue
                    coin_daily_data[col_name] = raw_price

                logging.info(f"{current_date}: {coin_daily_data}")
                if coin_daily_data:
                    upsert_entity(table_service, current_date, coin_daily_data)
            except Exception as e:
                logging.exception(f"Error processing {current_date}: {e}")
            current_date += datetime.timedelta(days=1)
    except Exception as e:
        logging.exception(f"Error in backfill_prices: {e}")
# -----------------------------
# ENTRY POINT
# -----------------------------
if __name__ == "__main__":
    table_service = TableService(endpoint_suffix="table.cosmos.azure.com", connection_string=ConnectionString)
    if not table_service.exists(TABLE_NAME):
        logging.error(f"Table {TABLE_NAME} does not exist")
        exit(1)
    backfill_prices(table_service)
