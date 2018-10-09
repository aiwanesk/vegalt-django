from django.urls import path

from . import views

app_name = "altproduct"

urlpatterns = [
    path('', views.index, name='index'),
    path('mentions-legales/', views.legal, name='legal'),
    path('creer-compte/', views.account_creation, name='account_creation'),
    path('mon-compte/', views.account, name='account'),
]
