from django.contrib.auth import authenticate, login
from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class LoginView(APIView):
    def post(self, request, format=None):
        data = request.data

        username = data.get('username', None)
        password = data.get('password', None)

        user = authenticate(username=username, password=password)

        data = {}

        if user is not None:
            if user.is_active:
                login(request, user)
                data = {'success': 'User logged in'}
                return Response(data, status=status.HTTP_200_OK)
            else:
                data = {'failure': 'User not active'}
                return Response(data, status=status.HTTP_404_NOT_FOUND)
        else:
            data = {'failure': 'User not found'}
            return Response(data, status=status.HTTP_404_NOT_FOUND)