from django.urls import path, include
from rest_framework import routers
from cursos import views
from .views import PeriodoAcademicoAPIView
from .views import MostrarCursosAlumno
from .views import CursosFiltradosView
from .views import CompetenciasPorCursoView
############################################

router = routers.DefaultRouter()
router.register(r'formulas', views.FormulaView, 'formulas')
router.register(r'cursos', views.CursoView, 'cursos')
router.register(r'horarios', views.HorarioView, 'horarios')
router.register(r'periodo', views.PeriodoView, 'periodo')
router.register(r"periodo_actual",views.PeriodoActualView,'periodo_actual')
router.register(r'cursos_profesor', views.CursoProfesorViewSet, 'cursos_profesor')
router.register(r'evaluaciones_horario', views.HorarioEvaluacionesViewSet, 'evaluaciones_horario')
router.register(r'cursos_gestor',views.CursosConHorariosViewSet,'cursos_gestor')

# Combine router URLs with additional paths
urlpatterns = [
    path('', include(router.urls)),  # Includes all the registered routes from the router
    path('api/periodo/<int:pk>/', PeriodoAcademicoAPIView.as_view(), name='periodo-academico-detail'),  # For getting a specific periodo
    path('alumno/<int:alumno_id>/cursos/', MostrarCursosAlumno.as_view(), name='alumno_cursos'),
    path('cursosfiltro/', CursosFiltradosView.as_view(), name='curso-list'),
    path('cursos/<int:id>/competencias/', CompetenciasPorCursoView.as_view(), name='competencias-por-curso'),
    path('cargar-cursos/', views.CargarCursosDesdeCSVView.as_view(), name='cargar_cursos'),
    path('cargar-horarios/',views.CargarHorariosDesdeCSVView.as_view(),name='cargar-horarios'),
    path('demanda-alumnos/', views.CursosConCantidadDeAlumnosViewSet.as_view({'get': 'list'}), name='demanda-alumnos')
]

