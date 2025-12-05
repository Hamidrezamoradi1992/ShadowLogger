from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class TestView(APIView):
    def get(self, request):
        return Response(
            {"message": "API is working!", "method": "GET"},
            status=status.HTTP_200_OK
        )

    def post(self, request):
        data = request.data
        return Response(
            {"message": "POST received", "data": data},
            status=status.HTTP_200_OK
        )