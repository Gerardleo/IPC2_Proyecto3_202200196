"""
URL configuration for djangoProject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from djangoProject.view import getInfo, reporte, index,cargar_archivo_mensajes,cargar_archivo_config,limpiar_datos,peticiones,buscarMenciones,buscarHastaghs,buscarSentimientos,guardarDatos

urlpatterns = [
    path('admin/', admin.site.urls),
    path('getInfo/', getInfo),
    path('reporte/', reporte),
    path('', index, name='index'),
    path('guardarDatos/', guardarDatos, name='guardarDatos'),
    path('leerArchivoMensajes/', cargar_archivo_mensajes, name='cargar_archivo_mensajes'),
    path('leerArchivoConfig/', cargar_archivo_config, name='cargar_archivo_config'),
    path('limpiarDatos/', limpiar_datos, name='limpiarDatos'),
    path('peticiones/', peticiones, name='peticiones'),
    path('buscarMenciones/', buscarMenciones, name='buscarMenciones'),
    path('buscarHashtag/', buscarHastaghs, name='buscarHastaghs'),
    path('buscarSentimientos/', buscarSentimientos, name='buscarSentimientos')



]
