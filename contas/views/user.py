from rest_framework.views import APIView
from contas.models import User
from contas.serializers import UserSerializer

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

class GetUser(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = User.objects.filter(id=request.user.id).first()

        serializer = UserSerializer(user)

        return Response({
            "user": serializer.data,
        })