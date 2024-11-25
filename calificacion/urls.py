from django.urls import path, include
from rest_framework.documentation import include_docs_urls
from rest_framework import routers
from calificacion import views
from .views import CursoEvaluacionesListView
from .views import CursosConNotasCompetenciasView

############################################

##genericos
router = routers.DefaultRouter()
router.register(r'subcompetencias',views.SubCompetenciaView,'subcompetencia')
router.register(r'competencias',views.CompetenciaView,'competencias')
router.register(r'competenciaxhorario',views.CompetenciaXHorarioView,'competenciaxhorario')
router.register(r'notadisponible',views.NotaDisponibleView,'notadisponible')
router.register(r'notanumerica',views.NotaNumericaView,'notanumerica')
router.register(r'notaalfabeticasub',views.NotaAlfabeticaSubView,'notaalfabeticasub')
router.register(r'notaalfabetica',views.NotaAlfabeticaView,'notaalfabetica')
router.register(r'notaxcompetencia',views.NotaXCompetenciaView,'notaxcompetencia')
router.register(r'guardarnotashorario', views.GuardarNotasViewset,'guardarnotashorario')
router.register(r'vernotashorario', views.NotasCursoViewSet, 'vernotashorario')

##pantallas
router.register(r'competenciasxhorarioxprof', views.CompetenciaXHorarioxProfeViewSet, basename='competenciaxhorarioxprof')
router.register(r'alumnosxhorario', views.ProfAlumnoXHorarioxCalificacionViewSet, basename='alumnosxhorario')
#router.register(r'guardarcalificacionesxindice', views.GuardarCalificacionesViewSet, basename='guardarcalificacionesxindice')
router.register(r'notasfinales', views.NotaFinalViewSet, basename='notasfinales')
router.register(r'vercalificacioncompetencias',views.ProfCalifiacionCompetenciasXIndice, basename='vercalificacioncompetencias')
urlpatterns = router.urls




urlpatterns = [
    path('', include(router.urls)),  # Includes all the registered routes from the router
    path('alumno/<int:alumno_id>/notas/', CursoEvaluacionesListView.as_view(), name='cursos-evaluaciones-list'),
    path('alumno/<int:alumno_id>/notas-competencias/', CursosConNotasCompetenciasView.as_view(), name='cursos-competencias-list'),
    path('subcomp_de_competencia/<int:id>/', views.CompetenciaDetailView.as_view(), name='competencia_detail'),
    path('cargar-competencias/', views.CargarCompetenciasDesdeCSVView.as_view(), name='cargar_competencias')
]