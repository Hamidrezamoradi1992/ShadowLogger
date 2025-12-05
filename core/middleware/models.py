from django.db import models



class RequestLog(models.Model):
    method = models.CharField(max_length=10)
    path = models.CharField(max_length=500)
    user = models.CharField(max_length=255, null=True, blank=True)
    user_id = models.CharField(max_length=255, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    query_params = models.JSONField(null=True, blank=True)
    body = models.JSONField(null=True, blank=True)
    status_code = models.IntegerField(null=True, blank=True)
    response_time_ms = models.FloatField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    device_info = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.method} {self.path}"

