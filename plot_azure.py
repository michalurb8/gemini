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

deposit = 1/4.6884 + 1/4.7399 + 1/4.6652
deposit *= 8
deposit += 1.50 + 10.20 + 165.12

yrange = int(1.05 * max(max([eur[i]+eureth[i]+eurbtc[i] for i, _ in enumerate(eur)]), deposit))
step = 10

plt.figure(figsize=(15,8), dpi=100)
ax = plt.gca()
plt.margins(x=0)
plt.stackplot(dates, eurbtc, eureth, eur, labels = ['EUR/BTC', 'EUR/ETH', 'EUR'],colors=[(0.94,0.55,0.05), (0.22, 0.21, 0.5), (0.5,0.5,0.5)], edgecolor='black')

xticksep = 4
plt.xticks([date.today() - timedelta(days=x) for x in range(0, (datetime.today() - dates[0]).days, xticksep)])
for index, day in enumerate(dates):
    plt.vlines(day, 0, (eureth[index] + eurbtc[index] + eur[index]), color=(0,0,0,0.1), linewidth=1)
    plt.scatter(day, (eureth[index] + eurbtc[index] + eur[index]), c='black', s=8)
plt.scatter(date(2022,9,15), 11.6, c='red', s=30)
plt.axhline(y=deposit, color=(0.9,0,0,0.15), linewidth=10)

plt.grid(axis='y',alpha=0.3,color='black')
plt.yticks(range(step, yrange+step, step), size=12)
ax.xaxis.set_major_locator(mdates.DayLocator(bymonthday=[6,12,18,24]))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m.%Y'))
ax.tick_params(axis='x', which='major', width = 1, length = 3, labelsize = 10, colors='black', labelrotation= 90)

ax.xaxis.set_minor_locator(mdates.MonthLocator())
ax.xaxis.set_minor_formatter(mdates.DateFormatter('%b'))
ax.tick_params(axis='x', which='minor', width = 2, length = 7, labelsize = 20, colors=(0.5,0,0), labelrotation= 80)

ax.yaxis.set_major_formatter('€{x:1.2f}')
ax.tick_params(axis='y', labelrotation= 0)


plt.legend(fontsize=15, loc='upper left')
plt.tight_layout()
plt.show()