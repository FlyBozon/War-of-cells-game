DEFAULT_CONNECTION_STRING = "mongodb://localhost:27017/"
DATABASE_NAME = "war_of_cells"
COLLECTION_NAME = "game_history"

def check_connection(connection_string=None):
    try:
        import pymongo
        client = pymongo.MongoClient(connection_string or DEFAULT_CONNECTION_STRING,
                                    serverSelectionTimeoutMS=2000)
        client.server_info()
        return True, client
    except ImportError:
        return False, "Biblioteka pymongo nie jest zainstalowana"
    except Exception as e:
        return False, str(e)