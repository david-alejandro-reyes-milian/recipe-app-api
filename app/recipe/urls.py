from django.urls import path, include
from rest_framework.routers import DefaultRouter

from recipe import views
from user.views import CreateUserView, CreateTokenView, ManageUserView

app_name = 'recipe'

router = DefaultRouter()
router.register('tags', views.TagViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
