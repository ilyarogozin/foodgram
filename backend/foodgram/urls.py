from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('api/', include('users.urls', namespace='users')),
    path('api/', include('recipes.urls', namespace='recipes')),
    path('admin/', admin.site.urls),
]
