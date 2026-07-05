import json
import re
import time
from bson import ObjectId
from datetime import datetime

from django.core.exceptions import PermissionDenied
from django.http.request import QueryDict
from user_agents import parse

from acl.messages import Messages
from .tasks import save_request_log


def safe_json(value):
    if isinstance(value, QueryDict):
        return dict(value)
    if isinstance(value, bytes):
        return "<bytes>"
    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        return str(value)


def serialize_for_celery(data):
    """Convert anything non‑JSON‑serializable (ObjectId, datetime, etc.) into safe types."""
    if isinstance(data, ObjectId):
        return str(data)
    if isinstance(data, datetime):
        return data.timestamp()
    if isinstance(data, dict):
        return {k: serialize_for_celery(v) for k, v in data.items()}
    if isinstance(data, list):
        return [serialize_for_celery(v) for v in data]
    return data


class RequestLogMiddleware:

    @staticmethod
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_body_data = None

        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            content_type = request.META.get("CONTENT_TYPE", "")

            if "multipart/form-data" in content_type:
                # فایل آپلود - body رو نخون
                request_body_data = safe_json(request.POST) if request.POST else None
                if request.FILES:
                    files_info = {
                        key: {
                            "name": f.name,
                            "size": f.size,
                            "content_type": f.content_type,
                        }
                        for key, f in request.FILES.items()
                    }
                    if request_body_data:
                        request_body_data["_files"] = files_info
                    else:
                        request_body_data = {"_files": files_info}

            elif request.POST:
                request_body_data = safe_json(request.POST)

            else:
                try:
                    request_body_data = json.loads(request.body.decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    request_body_data = "Raw Data or File (Not JSON)"
                except Exception:
                    request_body_data = None

        start_time = time.time()
        response = self.get_response(request)
        duration = (time.time() - start_time) * 1000

        if any(request.path.startswith(prefix) for prefix in ("/admin/", "/static/", "/media/")):
            return response

        user_info = None
        user_id = None
        if hasattr(request, "user") and request.user.is_authenticated:
            phone = getattr(request.user, 'phone_number', 'No-Phone')
            full_name = request.user.username
            user_info = f"{full_name} / {phone}"
            user_id = str(request.user.id)

        ua = parse(request.META.get("HTTP_USER_AGENT", ""))
        device_info = {
            "browser": ua.browser.family,
            "browser_version": ua.browser.version_string,
            "os": ua.os.family,
            "os_version": ua.os.version_string,
            "device": ua.device.family,
            "is_mobile": ua.is_mobile,
            "is_pc": ua.is_pc,
            "is_tablet": ua.is_tablet,
        }

        error_message = None
        if getattr(response, "status_code", 200) >= 400:
            try:
                if hasattr(response, "data"):
                    error_message = safe_json(response.data)
                elif hasattr(response, "content"):
                    error_message = response.content.decode("utf-8")[:1000]
            except Exception:
                error_message = "Could not parse error content"

        log_data = {
            "method": request.method,
            "path": request.path,
            "user": user_info,
            "user_id": user_id,
            "ip_address": self.get_client_ip(request),
            "query_params": safe_json(request.GET),
            "body": request_body_data,
            "status_code": getattr(response, "status_code", None),
            "response_time_ms": round(duration, 2),
            "error_message": error_message,
            "user_agent": request.META.get("HTTP_USER_AGENT", ""),
            "device_info": device_info,
            "created_at": time.time(),
        }

        try:
            safe_log = serialize_for_celery(log_data)
            save_request_log.delay(safe_log)
        except Exception as e:
            print(f"Error sending log to Celery: {e}")

        return response