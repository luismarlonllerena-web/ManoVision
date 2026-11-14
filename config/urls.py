from django.contrib import admin
from django.urls import path
from vision import views
urlpatterns = [path('',views.home,name='home'),path('api/frame/',views.frame,name='frame'),path('api/history/',views.history,name='history'),path('exportar/',views.export_csv,name='export'),path('admin/',admin.site.urls)]
