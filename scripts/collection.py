import os

from pypgstac.load import Loader, Methods
from pypgstac.db import PgstacDB

from .utils import args_handler, data_files, DATA_PATH, get_secret


collections_path = os.path.join(DATA_PATH, 'collections')


def get_dsn_string(secret: dict, localhost: bool = False) -> str:
    """Form database connection string from a dictionary of connection secrets

    Args:
        secret (dict): dictionary containing connection secrets including username, database name, host, and password

    Returns:
        dsn (str): full database data source name
    """
    try:
        if localhost:
            host = "localhost"
            port = 9999
        else:
            host = secret["host"]
            port = secret["port"]

        return f"postgres://{secret['username']}:{secret['password']}@{host}:{port}/{secret.get('dbname', 'postgis')}"

    except Exception as e:
        raise e


def insert_collection(collection_ndjson):
    secret_name = os.environ.get("SECRET_NAME")
    con_secrets = get_secret(secret_name)
    dsn = get_dsn_string(con_secrets)

    with PgstacDB(dsn=dsn, debug=False) as db:
        loader = Loader(db=db)
        loader.load_collections(collection_ndjson, Methods.upsert)


def insert_collections(files):
    print("Inserting collections:")
    for file in files:
        print(file)
        try:
            insert_collection(file)
            print("Inserted")
        except Exception as e:
            print("Error inserting collection.", str(e))


@args_handler
def insert(collections):
    files = data_files(collections, collections_path)
    insert_collections(files)


@args_handler
def delete(collections):
    print("Function not implemented")


@args_handler
def update(collections):
    print("Function not implemented")
