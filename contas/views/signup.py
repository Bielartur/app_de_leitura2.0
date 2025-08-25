from rest_framework.response import Response
from rest_framework.views import APIView

from contas.auth import Authentication
from contas.serializers import UserSerializer


class Signup(APIView):
    def post(self, request):
        name = request.data.get('name')
        email = request.data.get('email')
        password = request.data.get('password')

        user = Authentication.signup(self, name=name, email=email, password=password)

        serializer = UserSerializer(user)

        return Response({"user": serializer.data})