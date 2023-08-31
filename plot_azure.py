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

dates = [datetime.strptime(res["RowKey"], '%Y-%m-%d') for res in result]
eur = [res["eur"] for res in result]
eth = [res["eth"] for res in result]
btc = [res["btc"] for res in result]
eureth = [res["eureth"] for res in result]
eurbtc = [res["eurbtc"] for res in result]

deposit = 0
deposit += (7.23 + 8) / 4.65 # 17.11.2021 pierwszy
deposit += (50.0 + 8) / 4.70 # 31.07.2022 z Wojtkiem
deposit += (808. + 8) / 4.70 # 28.11.2022 glowny

yrange = int(1.05 * max(max([eur[i]+eureth[i]+eurbtc[i] for i, _ in enumerate(eur)]), deposit))
step = 10

plt.figure(figsize=(15,8), dpi=100)
ax = plt.gca()
plt.margins(x=0)
plt.stackplot(dates, eurbtc, eureth, eur, labels = ['EUR/BTC', 'EUR/ETH', 'EUR'],colors=[(0.94,0.55,0.05), (0.22, 0.21, 0.5), (0.5,0.5,0.5)], edgecolor='black')

for index, day in enumerate(dates):
    plt.vlines(day, 0, (eureth[index] + eurbtc[index] + eur[index]), color=(0,0,0,0.05), linewidth=1)
    plt.scatter(day, (eureth[index] + eurbtc[index] + eur[index]), c='black', s=8)
plt.scatter(date(2022,9,15), 11.6, c='red', s=30)
plt.axhline(y=deposit, color=(0.9,0,0,0.15), linewidth=10)

plt.grid(axis='y',alpha=0.3,color='black')
plt.yticks(range(step, yrange+step, step), size=12)

ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.tick_params(axis='x', which='major', width = 2, length = 7, labelsize = 20, colors=(0.2, 0, 0), labelrotation= 0)

ax.xaxis.set_minor_locator(mdates.MonthLocator())
ax.xaxis.set_minor_formatter(mdates.DateFormatter('%b'))
ax.tick_params(axis='x', which='minor', width = 1, length = 5, labelsize = 15, colors='black', labelrotation= 0)

ax.yaxis.set_major_formatter('€{x:1.2f}')
ax.tick_params(axis='y', labelrotation= 0)


plt.legend(fontsize=15, loc='upper left')
plt.tight_layout()
plt.show()