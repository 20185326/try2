from django.urls import path, include
from rest_framework import routers
from .views import *

router = routers.DefaultRouter()
router.register(r'usuarios', UsuarioViewSet)
router.register(r'alumnos', AlumnoViewSet)
router.register(r'profesores', ProfesorViewSet)
router.register(r'administradores', AdministradorViewSet)

urlpatterns = router.urls

urlpatterns = [
    path('', include(router.urls)),  # Includes all the registered routes from the router
    path('periodos/alumno/<int:alumno_id>/', PeriodosConRegistrosAlumnoView.as_view(), name='periodos-con-registros-alumno'),
    path('alumno/<int:alumno_id>/cursos_permitidos/', CursosPermitidosView.as_view(), name='cursos_permitidos'),
    path('trayectoria_academica/<int:alumno_id>/', TrayectoriaAcademicaView.as_view(), name='trayectoria_academica')
]
