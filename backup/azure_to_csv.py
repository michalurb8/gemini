from matplotlib.axis import YAxis
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from azure.cosmosdb.table import TableService
from datetime import datetime, date, timedelta
from keys import ConnectionString

tableName = "balances"

tableServiceClient = TableService(endpoint_suffix = "table.cosmos.azure.com", connection_string= ConnectionString)
if not tableServiceClient.exists(tableName):
    print()
    print("The table does not exist")
    exit()


result = tableServiceClient.query_entities(tableName)

dates = [datetime.strptime(res["RowKey"], '%Y%m%d') for res in result]
eur = [res["EUR"] for res in result]
eth = [res["ETH"] for res in result]
btc = [res["BTC"] for res in result]
eureth = [res["EURETH"] for res in result]
eurbtc = [res["EURBTC"] for res in result]

fileName = datetime.now().strftime('%Y%m%d')

with open(f'backup{fileName}', 'w') as file:
    file.write("DateKey, EUR, ETH, BTC, EURETH, EURBTC\n")
    for r in result:
        file.write(f'{r["EUR"]}, {r["ETH"]}, {r["BTC"]}, {r["EURETH"]}, {r["EURBTC"]}\n')

