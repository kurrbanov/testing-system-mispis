from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from euk.views import (
    RegisterView,
    LoginView,
    MainPage,
    LogoutView,
    SectionView,
    TopicView,
    RunTestView,
    BuildMapView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', MainPage.as_view(), name="main-page"),
    path('login', LoginView.as_view(), name="login"),
    path('register', RegisterView.as_view(), name="register"),
    path('logout', LogoutView.as_view(), name="logout"),
    path('section/<int:pk>', SectionView.as_view(), name="section"),
    path('topic/<int:pk>', TopicView.as_view(), name="topic"),
    path('test/<int:pk>', RunTestView.as_view(), name="run-test"),
    path('map', BuildMapView.as_view(), name="build-map"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
