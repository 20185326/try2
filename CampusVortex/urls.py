from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('cursos/', include('cursos.urls')),
    path('matricula/', include('matricula.urls')),
    path('usuarios/', include('usuarios.urls')),
    path('calificacion/',include('calificacion.urls'))
]