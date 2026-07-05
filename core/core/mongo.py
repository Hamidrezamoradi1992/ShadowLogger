from decouple import config
from pymongo import MongoClient
from urllib.parse import quote_plus


MONGO_USER = config("MONGO_USER", default="mongouser")
MONGO_PASS = config("MONGO_PASS", default="mongopass")
MONGO_HOST = config("MONGO_HOST", default="mongo")
MONGO_PORT = config("MONGO_PORT", default="27017")
MONGO_DB_NAME = config("MONGO_DB_NAME", default="sedo_logs")
MONGO_AUTH_SOURCE = config("MONGO_AUTH_SOURCE", default="admin")


user = quote_plus(MONGO_USER)
password = quote_plus(MONGO_PASS)

MONGO_URI = f"mongodb://{user}:{password}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB_NAME}?authSource={MONGO_AUTH_SOURCE}"


client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]
