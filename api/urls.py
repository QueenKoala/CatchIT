from django.urls import include, path, re_path

from .views import (
    UserViewAPI,
    UserMeAPI,
    UserLoginAPI,
    UserRegisterAPI,
    UserEditAPI, 
    CategoryViewAPI,
    ArticleViewSet,
)

from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'articles', ArticleViewSet, basename='articles')



urlpatterns = [
    path('users/', UserViewAPI.as_view(), name='users'),                # Public user data
    path('auth-register', UserRegisterAPI.as_view(), name='users'),     # Register new user
    path('auth-login', UserLoginAPI.as_view(), name='users'),           # Login existing user
    path('users/me', UserMeAPI.as_view(), name='users'),                # Private Personal User data
    path('users/edit', UserEditAPI.as_view(), name='users'),            # Edit Personal user data
    path('categories/', CategoryViewAPI.as_view(), name='categories'),  # Public Category data
    path('', include(router.urls)),
]