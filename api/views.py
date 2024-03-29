from functools import partial
from urllib import request
from rest_framework.views import APIView
from rest_framework.response import Response

from rest_framework import viewsets
from .serializers import UserSerializer, CategorySerializer, ArticleSerializer
from .models import User, Category, Article
from jwt import encode
from config.settings import SECRET_KEY
from requests import post
from config.settings import boto3_client
from time import time

import hashlib, datetime


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_queryset(self):
        if self.request.GET.get('id'):
            return User.objects.filter(id=self.request.GET.get('id'))
        else:
            return None

    def list(self, request, *args, **kwargs):

        queryset = self.filter_queryset(self.get_queryset())

        if queryset is None:
            return Response({"status": 400, "message": "Bad request"}, status=400)
        elif queryset.count() == 0:
            return Response({"status": 404, "message": "Not found"}, status=404)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


    def create(self, request, *args, **kwargs):
        if request.jwt_user:        # If user is logged in, edit his profile
            serializer = self.get_serializer(data=request.data, instance=User.objects.get(id=request.jwt_user['id']), partial=True)
        else:                       # If user is not logged in, create new user
            serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response({"status": 201, "data": serializer.data}, status=201, headers=headers)


class UserLoginAPI(APIView):                # Login user
    def post(self, request):
        email, password = request.data['email'], request.data['password']
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            if user.password == hashlib.sha256(password.encode('utf-8')).hexdigest():
                return Response({"status": 200, "message": "Successfully logged in", 
                    "token": encode(
                        {
                            "id": user.id,
                            "firstname": user.firstname,
                            "lastname": user.lastname,
                            "email": user.email,
                            "phone_number": user.phone_number,
                            "city": user.city,
                            "is_admin": user.is_admin,
                            "exp": datetime.datetime.now() + datetime.timedelta(seconds=7200)
                        }
                        , SECRET_KEY, algorithm='HS256')}, status=200)
            else:
                return Response({"status": 401, "message": "Invalid email or password"}, status=401)
        else:
            return Response({"status": 401, "message": "Invalid email or password"}, status=401)





class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_queryset(self):
        if self.request.GET.get('id'):
            return Category.objects.filter(id=self.request.GET.get('id'))
        else:
            return Category.objects.all()

    def create(self, request):
        if (request.jwt_user and request.jwt_user['is_admin'] == True):
            if 'image' in request.data:
                request.data['image'].name = f"{time()}.{request.data['image'].name}"   # Unique name for each image
            if request.GET.get('id'):       # if id is provided, edit category
                serializer = self.get_serializer(data={'name': request.data['name'], 'created_by': request.jwt_user['id']}, instance=Category.objects.get(id=request.GET.get('id')), partial=True)
            else:                           # if id is not provided, create new category
                serializer = CategorySerializer(data={'name': request.data['name'],'image': request.data['image'] if 'image' in request.data else None , 'created_by': request.jwt_user['id']})
            if serializer.is_valid():
                serializer.save()
                if 'image' in request.data:         # Upload to aws storage server
                    request.data['image'].file.seek(0)  # Reset the file pointer since it was consumed by the serializer
                    boto3_client.put_object(
                        Bucket='catchit',
                        Key=f"categories/{request.data['image'].name}",
                        Body=request.data['image'].file,
                        ACL='public-read'
                    )
                return Response({"status": 200, "message": "Category created successfully"}, status=200)
            else:
                return Response({"status": 400, "message": "Bad request"}, status=400)
        else:
            return Response({"status": 401, "message": "Unauthorized"}, status=401)


class ArticleViewSet(viewsets.ModelViewSet):    # TODO: Add create, edit, delete
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer

    def get_queryset(self):
        if self.request.GET.get('category_id'):
            return Article.objects.filter(category_id=self.request.GET.get('category_id'), is_sold=False)
        elif self.request.GET.get('seller'):
            if self.request.jwt_user:
                if self.request.jwt_user['id'] == int(self.request.GET.get('seller')):
                    return Article.objects.filter(seller=self.request.GET.get('seller'))
            return Article.objects.filter(seller=self.request.GET.get('seller'), is_sold=False)
        elif self.request.GET.get('id'):
            return Article.objects.filter(id=self.request.GET.get('id'), is_sold=False)
        elif self.request.GET.get('title'):
            return Article.objects.filter(title__icontains=self.request.GET.get('title'), is_sold=False)
        elif self.request.GET.get('city'):
            return Article.objects.filter(city=self.request.GET.get('city'), is_sold=False)
        else:
            return None

    def list(self, request, *args, **kwargs):

        queryset = self.filter_queryset(self.get_queryset())

        if queryset is None:
            return Response({"status": 400, "message": "Bad request"}, status=400)
        elif queryset.count() == 0:
            return Response({"status": 404, "message": "Not found"}, status=404)        # Not found or sold

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        if request.jwt_user is None:                                              # Not signed in
            return Response({"status": 401, "message": "Unauthorized"}, status=401)
        if 'image' in request.data:
            request.data['image'].name = f"{time()}.{request.data['image'].name}"   # Unique name for each image
        if 'id' in request.data:    
            if Article.objects.get(id=request.data['id'], seller=request.jwt_user['id']) is None:   # User editing his own article
                return Response({"status": 403, "message": "Forbidden"}, status=403)
            serializer = self.get_serializer(data=request.data, instance=Article.objects.get(id=request.data['id']), partial=True)
        else:
            serializer = self.get_serializer(data={'title': request.data['title'], 'description': request.data['description'], 'category': request.data['category'], 'seller': request.jwt_user['id'], 'condition': request.data['condition'], 'price': request.data['price'], 'quantity': request.data['quantity'], 'city': request.data['city'], 'image': request.data['image'] if 'image' in request.data else None})
        if serializer.is_valid():
            serializer.save()
            if 'image' in request.data:         # Upload to aws storage server
                request.data['image'].file.seek(0)  # Reset the file pointer since it was consumed by the serializer
                boto3_client.put_object(
                    Bucket='catchit',
                    Key=f"articles/{request.data['image'].name}",
                    Body=request.data['image'].file,
                    ACL='public-read'
                )
            return Response({"status": 200, "message": "Article created or updated successfully", "article": serializer.data}, status=200)
        return Response({"status": 400, "message": "Bad request"}, status=400)
        



