# from celery import shared_task
# from pymongo import MongoClient
# import os
# from datetime import datetime
# import logging
# from django.conf import settings
# logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO)
#
# # MONGO_URI = settings.MONGO_URI
# MONGO_URI ='mongodb://mongouser:mongopass@mongo:27017/admin?authSource=admin'
# MONGO_DB_NAME = "sedo_logs"
# MONGO_COLLECTION_NAME = "request_logs"
#
# logger.error(f"hamidsjdhjahsjd;asdaskjdaskdjlaksdaksdas{MONGO_URI}")
# @shared_task(bind=True)
# def save_request_log(self, log_data):
#     print("CELERY TASK EXECUTED!")
#
#     logger.info(
#         f"Task started: Saving log for method: {log_data.get('method')} path: {log_data.get('path')}"
#     )
#
#     try:
#         client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
#         db = client[MONGO_DB_NAME]
#         col = db[MONGO_COLLECTION_NAME]
#
#     except Exception as e:
#         logger.error(f"MONGO_CONNECT_FAIL: {e}")
#         raise self.retry(exc=e, countdown=5)
#
#     try:
#         if isinstance(log_data.get("created_at"), (int, float)):
#             log_data["created_at"] = datetime.fromtimestamp(log_data["created_at"])
#         else:
#             log_data["created_at"] = datetime.now()
#
#         result = col.insert_one(log_data)
#
#         logger.info(f"MONGO_INSERT_SUCCESS: ID = {result.inserted_id}")
#
#     except Exception as e:
#         logger.error(f"MONGO_INSERT_FAIL: {e}")
#
#     finally:
#         client.close()




from celery import shared_task
from pymongo import MongoClient
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://mongo:27017/")
MONGO_DB_NAME = "sedo_logs"
MONGO_COLLECTION_NAME = "request_logs"

logger.error(f"MONGO_URI_CHECK: {MONGO_URI}")
@shared_task(bind=True)
def save_request_log(self, log_data):
    print("CELERY TASK EXECUTED!")

    logger.info(
        f"Task started: Saving log for method: {log_data.get('method')} path: {log_data.get('path')}"
    )

    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client[MONGO_DB_NAME]
        col = db[MONGO_COLLECTION_NAME]

    except Exception as e:
        logger.error(f"MONGO_CONNECT_FAIL: {e}")
        raise self.retry(exc=e, countdown=5)

    try:
        if isinstance(log_data.get("created_at"), (int, float)):
            log_data["created_at"] = datetime.fromtimestamp(log_data["created_at"])
        else:
            log_data["created_at"] = datetime.now()

        result = col.insert_one(log_data)

        logger.info(f"MONGO_INSERT_SUCCESS: ID = {result.inserted_id}")

    except Exception as e:
        logger.error(f"MONGO_INSERT_FAIL: {e}")

    finally:
        client.close()
