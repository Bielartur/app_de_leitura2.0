from rest_framework.views import APIView
from contas.auth import Authentication
from contas.serializers import UserSerializer

from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

class Signin(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        user = Authentication.signin(self, email=email, password=password)
        
        token = RefreshToken.for_user(user)

        serializer = UserSerializer(user)

        return Response({
            "user": serializer.data,
            "refresh": str(token),
            "access": str(token.access_token)
        })