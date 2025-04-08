
from unicodedata import name
from django.contrib import admin
from django.urls import path, include
from . import views 

app_name = 'diplom'

urlpatterns = [
    path('journal/', views.get_journal, name='journal'),
    path('',views.main, name='main'),
    path('createjournal/<int:page>',views.create_journal, name='create'),
    path('update/<int:pas_id>/<int:numberpunkt>/<int:page>/',views.update_journal, name='update'),
    path('analytics',views.analytics, name='analytics'),

]
