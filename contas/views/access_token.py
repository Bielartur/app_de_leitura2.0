# contas/views/access_key.py (continuação)
from django.contrib.auth.hashers import check_password
from contas.models import generate_access_key
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

class RotateAccessKeyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        password = request.data.get("password")
        if not check_password(password or "", request.user.password):
            raise AuthenticationFailed("Senha inválida.")
        request.user.access_key = generate_access_key()
        request.user.save(update_fields=["access_key"])
        return Response({"access_key": request.user.access_key}, status=status.HTTP_200_OK)
