from django.contrib.auth import login, logout
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, status, permissions
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import User
from .serializers import EmailAuthTokenSerializer, UserRegistrationWithEmailSerializer


class AuthViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    queryset = User.objects.all()
    serializer_class = UserRegistrationWithEmailSerializer

    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = UserRegistrationWithEmailSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            return Response({
                'token': user.token.key,
                'user_id': user.pk,
                'username': user.username,
                'email': user.email or '',
                'first_name': user.first_name or '',
                'last_name': user.last_name or ''
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @csrf_exempt
    @action(detail=False, methods=['post'])
    def login(self, request):
        request_data = request.data.copy()
        identifier = request_data.pop('identifier', None)
        if identifier:
            request_data['username_email'] = identifier
            
        serializer = EmailAuthTokenSerializer(data=request_data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)
        else:
            return Response(
                serializer.errors, 
                status=status.HTTP_400_BAD_REQUEST
            )

        token, created = Token.objects.get_or_create(user=user)
        first_login = not user.last_login

        return Response({
            'token': token.key,
            'user_id': user.pk,
            'username': user.username,
            'email': user.email or '',
            'first_name': user.first_name or '',
            'last_name': user.last_name or '',
            'firstLogin': first_login
        })

    @action(detail=False, methods=['post'])
    def logout(self, request):
        if request.user.is_authenticated:
            Token.objects.filter(user=request.user).delete()
            logout(request)
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_401_UNAUTHORIZED)
