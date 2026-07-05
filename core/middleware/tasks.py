import os
import boto3
import logging
import json
from celery import shared_task
from datetime import datetime
from decouple import config
from core.mongo import db


logger = logging.getLogger(__name__)


def get_s3_client():
    return boto3.client(
        's3',
        aws_access_key_id=config('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=config('AWS_SECRET_ACCESS_KEY'),
        endpoint_url=config('AWS_S3_ENDPOINT_URL'),
    )

OBJECT_STORAGE_ACTIVE = config("OBJECT_STORAGE_ACTIVE", default=False, cast=bool)
MONGO_ACTIVATE = config("MONGO_ACTIVATE", default=False, cast=bool)
AWS_STORAGE_BUCKET_NAME = config("AWS_STORAGE_BUCKET_NAME", default=None, cast=str)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def save_request_log(self, log_data):


    log_data["created_at"] = (
        datetime.fromtimestamp(log_data["created_at"])
        if isinstance(log_data.get("created_at"), (int, float))
        else datetime.now()
    )

    log_json = json.dumps(log_data, default=str, ensure_ascii=False)

    if MONGO_ACTIVATE:
        try:
            col = db["request_logs"]
            result = col.insert_one(log_data)
            logger.info(f"Inserted log with ID {result.inserted_id} into MongoDB")
            return str(result.inserted_id)

        except Exception as mongo_error:
            logger.error(f"MongoDB failed: {mongo_error}")


    if OBJECT_STORAGE_ACTIVE:
        try:
            s3 = get_s3_client()
            request_path = log_data.get("path", "unknown").strip("/").replace("/", "-")


            timestamp = datetime.now().strftime("%H-%M-%S-%f")
            file_name = f"logs/{datetime.now().strftime('%Y-%m-%d')}/{request_path}_{timestamp}.json"


            s3.put_object(
                Bucket=AWS_STORAGE_BUCKET_NAME,
                Key=file_name,
                Body=log_json + "\n",
            )

            logger.info(f"Log saved to Object Storage: {file_name}")
            return file_name

        except Exception as s3_error:
            logger.error(f"Object Storage failed: {s3_error}")

    else:
        try:
            date_folder = datetime.now().strftime('%Y-%m-%d')
            directory = f"static/logs"
            os.makedirs(directory, exist_ok=True,mode=777)


            file_path = os.path.join(directory, f"{date_folder}.json")

            with open(file_path, "a", encoding="utf-8") as f:
                f.write(log_json + "\n")

            logger.info(f"Log saved locally: {file_path}")
            return file_path

        except Exception as file_error:
             logger.error(f"Local file save failed: {file_error}")


    raise Exception("All logging backends failed.")