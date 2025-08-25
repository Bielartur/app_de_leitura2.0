from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from contas.auth import Authentication
from contas.serializers import UserSerializer


class Signup(APIView):
    def post(self, request):
        name = request.data.get('name')
        email = request.data.get('email')
        password = request.data.get('password')

        auth = Authentication()
        user = auth.signup(name=name, email=email, password=password)

        serializer = UserSerializer(user)
        return Response({"user": serializer.data}, status=status.HTTP_201_CREATED)
