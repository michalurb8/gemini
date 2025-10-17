import logging

def setup_logger(log_file: str):
    """
    Configure logging for a script:
    - Writes to a file (appends)
    - Includes timestamp, level, message
    - Adds a separator line for each run
    """
    logging.basicConfig(
        filename=log_file,
        filemode='a',  # append
        format='%(asctime)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    logging.info('----------------- Script started -----------------')

# Optionally suppress verbose library logs
logging.getLogger("azure").setLevel(logging.WARNING)
logging.getLogger("azure.core.pipeline.transport").setLevel(logging.WARNING)
logging.getLogger("azure.cosmosdb.table").setLevel(logging.WARNING)
logging.getLogger("msrest").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
