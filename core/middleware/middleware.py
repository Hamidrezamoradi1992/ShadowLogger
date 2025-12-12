from .models import RequestLog
import time
import json
from user_agents import parse
from django.http.request import QueryDict
from .tasks import save_request_log

class RequestLogSQLMiddleware:
    """
    Logs all requests:
    - All paths except /admin/ and /static/
    - Captures user device info (OS, browser, mobile/desktop)
    - Logs method, path, user, IP, query_params, body, status_code, response_time, error_message
    """

    def __init__(self, get_response):
        self.get_response = get_response

    @staticmethod
    def get_client_ip(request):
        return (request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('REMOTE_ADDR')).split(',')[0]

    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        duration = (time.time() - start_time) * 1000

        if request.path.startswith("/admin/") or request.path.startswith("/static/"):
            return response


        user = None
        user_id = None
        if hasattr(request, "user") and request.user.is_authenticated:
            user = f"{request.user.username}"
            user_id = request.user.id


        user_agent_str = request.META.get("HTTP_USER_AGENT", "")
        ua = parse(user_agent_str)
        device_info = {
            "os": ua.os.family,
            "os_version": ua.os.version_string,
            "browser": ua.browser.family,
            "browser_version": ua.browser.version_string,
            "device": ua.device.family,
            "is_mobile": ua.is_mobile,
            "is_tablet": ua.is_tablet,
            "is_pc": ua.is_pc,
        }


        body_data = None
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            if hasattr(request, "data"):
                body_data = request.data
            elif hasattr(request, "_body"):
                try:
                    body_data = json.loads(request._body.decode("utf-8"))
                except Exception:
                    body_data = str(request._body[:500])


        error_message = None
        if getattr(response, "status_code", 200) >= 400:
            try:
                if hasattr(response, "content"):
                    error_message = response.content.decode("utf-8")[:1000]
            except Exception:
                error_message = "Cannot decode response content"


        RequestLog.objects.using("logs").create(
            method=request.method,
            path=request.path,
            user=user,
            user_id=user_id,
            ip_address=self.get_client_ip(request),
            query_params=dict(request.GET),
            body=body_data,
            status_code=getattr(response, "status_code", None),
            response_time_ms=round(duration, 2),
            error_message=error_message,
            user_agent=user_agent_str,
            device_info=device_info,
        )

        return response


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

class RequestLogNOSQLMiddleware:

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

            if request.POST:
                request_body_data = safe_json(request.POST)


            elif request.body:
                try:

                    request_body_data = json.loads(request.body.decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError):

                    request_body_data = "Raw Data or File (Not JSON)"
                except Exception:
                    request_body_data = None

        start_time = time.time()

        response = self.get_response(request)

        duration = (time.time() - start_time) * 1000

        if request.path.startswith("/admin/") or request.path.startswith("/static/") or request.path.startswith(
                "/media/"):
            return response

        user_info = None
        user_id = None

        if hasattr(request, "user") and request.user.is_authenticated:
            phone = getattr(request.user, 'phone_number', 'No-Phone')
            full_name = request.user.username
            user_info = f"{full_name} / {phone}"
            user_id = str(request.user.id)


        user_agent_str = request.META.get("HTTP_USER_AGENT", "")
        ua = parse(user_agent_str)

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
            "user_agent": user_agent_str,
            "device_info": device_info,
            "created_at": time.time(),
        }

        try:

            save_request_log.delay(log_data)
        except Exception as e:
            print(f"Error sending log to Celery: {e}")

        return response
