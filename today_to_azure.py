from azure.cosmosdb.table import TableService
from datetime import date
from gemini_today_to_json import get_balance
from keys import ConnectionString

tableName = "balances"

tableServiceClient = TableService(endpoint_suffix = "table.cosmos.azure.com", connection_string= ConnectionString)
if not tableServiceClient.exists(tableName):
    print()
    print("The table does not exist")
    exit()

entity = get_balance()
entity["PartitionKey"] = str( date.today().year*100 + date.today().month)
entity["RowKey"] = str( date.today().year*10000 + date.today().month*100 + date.today().day)

tableServiceClient.insert_or_replace_entity(tableName, entity, timeout=None)