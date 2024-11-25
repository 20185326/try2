from usuarios.models import *
from rest_framework import viewsets
from .serializers import *
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import generics,status,generics
from matricula.models import AlumnoXHorario
from django.db.models import Subquery, Max
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView

class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.select_related('alumno', 'profesor').all()  # Optimiza la consulta
    serializer_class = UsuarioSerializer

    @action(detail=False, methods=['post'], url_path='login')
    def login(self, request):
        codigo_usuario = request.data.get('codigo_usuario')

        if not codigo_usuario:
            return Response({'error': 'Se requiere el código de usuario'}, status=400)

        usuario = get_object_or_404(self.queryset, codigo=codigo_usuario)
        serializer = self.get_serializer(usuario, context={'request': request})
        return Response(serializer.data)

class AlumnoViewSet(viewsets.ModelViewSet):
    queryset = Alumno.objects.all()
    serializer_class = AlumnoSerializer

class ProfesorViewSet(viewsets.ModelViewSet):
    queryset = Profesor.objects.all()
    serializer_class = ProfesorSerializer

class AdministradorViewSet(viewsets.ModelViewSet):
    queryset = Administrador.objects.all()
    serializer_class = AdministradorSerializer

class PeriodosConRegistrosAlumnoView(generics.ListAPIView):
    serializer_class = PeriodosAlumnoSerializer

    def get_queryset(self):
        alumno_id = self.kwargs['alumno_id']  # Obtener el ID del alumno de la URL

        # Subconsulta para obtener los períodos relacionados a AlumnoXHorario del alumno
        cursos_con_alumno = AlumnoXHorario.objects.filter(alumno_id=alumno_id).values('periodo_id')

        # Filtrar los períodos en los que el alumno tiene registros en AlumnoXHorario
        return PeriodoAcademico.objects.filter(id__in=Subquery(cursos_con_alumno)).distinct()
    

## Cursos permitidos    
class CursosPermitidosView(APIView):
    def get(self, request, alumno_id):
        try:
            # Obtener el alumno por su ID
            alumno = Alumno.objects.get(id=alumno_id, activo=True)
        except Alumno.DoesNotExist:
            return Response(
                {"error": "Alumno no encontrado o inactivo."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Obtener cursos permitidos
        cursos_permitidos = alumno.cursosPermitidos.filter(activo=True)
        alumnos=Alumno.objects.filter(habilitado=True).count()
        # Serializar datos
        cursos_data = []
        cursos_data.append({  # Agregar información general del alumno al inicio
            "factorDesempeno": alumno.factorDeDesempeno,
            "turnoDeMatricula": alumno.turnoOrdenMatricula,
            "totalAlumnos": alumnos
        })
        
        for curso in cursos_permitidos:
            # Obtener la fórmula del curso
            formula = curso.formula
            formula_data = {
                "pesoParciales": formula.pesoParciales if formula else None,
                "pesoFinales": formula.pesoFinales if formula else None,
                "pesoPracticas": formula.pesoPracticas if formula else None,
                "numPracticas": formula.numPracticas if formula else None
            }

            # Calcular la vez que le tocaría al alumno tomar el curso
            ultima_vez = AlumnoXHorario.objects.filter(
                alumno=alumno,
                horario__idCurso=curso,
                retirado=False
            ).aggregate(Max('vez'))['vez__max'] or 0  # Si no hay registros, vez = 0
            siguiente_vez = ultima_vez + 1
            # Agregar datos al JSON de respuesta
            cursos_data.append({
                "clave": curso.clave,
                "nombre": curso.nombre,
                "creditos": curso.creditos,
                "nivel": curso.nivel,
                "formula": formula_data,
                "vez": siguiente_vez
            })

        return Response(cursos_data, status=status.HTTP_200_OK)
    
##Trayectoria Academica
class TrayectoriaAcademicaView(APIView):
    def get(self, request, alumno_id):
        try:
            # Obtener el alumno por ID
            alumno = Alumno.objects.get(id=alumno_id)
        except Alumno.DoesNotExist:
            return Response(
                {"error": "Alumno no encontrado."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Serializar los datos del alumno
        serializer = TrayectoriaAcademicaSerializer(alumno)
        return Response(serializer.data, status=status.HTTP_200_OK)


