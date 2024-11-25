from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Count  # Agrega esta línea
from django.db.utils import IntegrityError
from django.utils import timezone
from .serializer import *
from .models import *
from calificacion.serializer import EvaluacionSerializer
from matricula.models import LineaInscripcion
from usuarios.models import TRol
from rest_framework import status
from django.db import connection
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
import csv
import re
from io import StringIO
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.parsers import MultiPartParser   
from faker import Faker 
import random
from datetime import date
from django.db import transaction
# Create your views here.

class FormulaView(viewsets.ModelViewSet):
    serializer_class= FormulaSerializar
    queryset =Formula.objects.all()
    
class CursoPagination(PageNumberPagination):
    page_size = 20  # Número de elementos por página
    page_size_query_param = 'page_size'  # Permite al cliente cambiar el tamaño
    max_page_size = 50  # Límite máximo de elementos por página
    
class CursoView(viewsets.ModelViewSet):
    serializer_class = CursoSerializar
    queryset = Curso.objects.all()
    pagination_class = CursoPagination  # Aquí aplicas la paginación personalizada
    
class HorarioView(viewsets.ModelViewSet):
    serializer_class = HorarioSSerializar
    queryset = Horario.objects.filter(activo=True)
    pagination_class = CursoPagination
    
class PeriodoView(viewsets.ModelViewSet):
    serializer_class = PeriodoAcademicoSerializar
    queryset = PeriodoAcademico.objects.all().order_by('fechaInicio')
    
class PeriodoActualView(viewsets.ModelViewSet):
    serializer_class = PeriodoAcademicoSerializar
    queryset = PeriodoAcademico.objects.filter(actual=1)
    

## /cursos/cursos_profesor/profesor/4/?periodo_academico_id=2
class CursoProfesorViewSet(viewsets.ModelViewSet):
    queryset = Curso.objects.all()
    serializer_class = CursoPSerializer

    @action(detail=False, methods=['get'], url_path=r'profesor/(?P<profesor_id>\d+)')
    def list_by_profesor(self, request, profesor_id=None):
        # Obtener el parámetro de periodo académico de la query string (si está presente)
        periodo_academico_id = request.query_params.get('periodo_academico_id')
        
        # Si no se especifica un periodo_academico_id, usar el periodo académico por defecto (según la fecha actual)
        if not periodo_academico_id:
            # Obtener la fecha actual
            fecha_actual = timezone.now().date()

            # Buscar el periodo académico que esté activo según la fecha actual
            periodo_academico = PeriodoAcademico.objects.filter(
                fechaInicio__lte=fecha_actual, 
                fechaFin__gte=fecha_actual
            ).first()  # Usamos `first()` para obtener el primer resultado que coincida

            if periodo_academico:
                periodo_academico_id = periodo_academico.id
            else:
                return Response({"error": "No hay un periodo académico activo para la fecha actual."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Filtrar cursos por el profesor y el periodo académico en AlumnoXHorario
        cursos = Curso.objects.filter(
            horarios__idprofesor_id=profesor_id,
            horarios__alumnoXhorarios__periodo_id=periodo_academico_id
        ).distinct()

        # Serializar los datos, pasando también el profesor_id en el contexto
        serializer = CursoPSerializer(cursos, many=True, context={'profesor_id': profesor_id})
        return Response(serializer.data)
    
## http://127.0.0.1:8000/cursos/cursos_profesor/profesor/3/?periodo_academico_id=4

    

class HorarioEvaluacionesViewSet(viewsets.ModelViewSet):
    queryset = Horario.objects.all()

    @action(detail=False, methods=['get'], url_path=r'horario/(?P<horario_id>\d+)') #http://127.0.0.1:8000/cursos/evaluaciones_horario/horario/1/

    def listar_evaluaciones(self, request, horario_id=None):
        try:
            # Obtener el horario y el curso asociado
            horario = Horario.objects.get(id=horario_id)
            curso = horario.idCurso
        except Horario.DoesNotExist:
            return Response({"error": "Horario no encontrado"}, status=404)

        # Lista para almacenar las evaluaciones
        evaluaciones = []

        # Agregar parciales
        for i in range(1, curso.numParciales + 1):
            evaluaciones.append({"tipo": "Parcial", "indice": i})

        # Agregar finales
        for i in range(1, curso.numFinales + 1):
            evaluaciones.append({"tipo": "Final", "indice": i})

        # Agregar prácticas
        for i in range(1, curso.numPracticas + 1):
            evaluaciones.append({"tipo": "Practica", "indice": i})

        # Serializar la lista de evaluaciones
        serializer = EvaluacionSerializer(evaluaciones, many=True)

        # Devolver la respuesta serializada
        return Response(serializer.data)
    
    
class PeriodoAcademicoAPIView(APIView):
    def get(self, request, pk=None):
        """Obtener un periodo académico por ID."""
        if pk is None:
            return Response({'detail': 'ID no proporcionado.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with connection.cursor() as cursor:
                cursor.callproc('GetPeriodoPorID', [pk])  # Call the procedure with the provided ID
                row = cursor.fetchone()  # Fetch the result
                
                if row:
                    # Create a dictionary to hold the result
                    periodo_data = {
                        'periodo': row[0]
                    }
                    serializer = PeriodoSerializer(data=periodo_data)
                    
                    if serializer.is_valid():
                        return Response(serializer.data, status=status.HTTP_200_OK)
                    else:
                        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({'detail': 'Periodo académico no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Alumno a)
class MostrarCursosAlumno(generics.ListAPIView):
    serializer_class = AlumnoXHorarioAlumnoSerializer

    def get_queryset(self):
        alumno_id = self.kwargs['alumno_id']  # Suponiendo que pasas el id del alumno en la URL
        periodo_id = self.request.query_params.get('periodo_id')

        queryset = AlumnoXHorario.objects.filter(alumno_id=alumno_id)
        if periodo_id:
            # Filtrar por el periodo a través de la relación Curso -> PeriodoAcademico
            queryset = queryset.filter(periodo_id=periodo_id)
        return queryset


#PARA EL GESTOR
class CursosConHorariosViewSet(viewsets.ModelViewSet):
    serializer_class = CursoConHorariosGestorSerializer
    pagination_class = CursoPagination

    def get_queryset(self):
        # Si el cliente proporciona un periodo, filtramos
        periodo_id = self.request.query_params.get('periodo_id', None)
        if periodo_id:
            try:
                periodo = PeriodoAcademico.objects.get(id=periodo_id, activo=True)
            except PeriodoAcademico.DoesNotExist:
                return Curso.objects.none()  # No cursos si el periodo no existe

            # Filtrar cursos cuyos horarios estén en el periodo
            return (
                Curso.objects.all().order_by('id')
                .select_related()  # Optimizamos las relaciones hacia adelante
                .prefetch_related(
                    'horarios',                       # Prefetch horarios relacionados al curso
                    'horarios__idprofesor',           # Optimizar la carga del profesor en cada horario
                )
                .distinct()
            )

        # Retornar todos los cursos con horarios y profesores
        return (
            Curso.objects.prefetch_related(
                'horarios',                      # Prefetch horarios relacionados al curso
                'horarios__idprofesor',          # Optimizar la carga del profesor en cada horario
            )
        )
    
class CursosFiltradosView(generics.ListAPIView):
    serializer_class = CursoSSerializar

    def get_queryset(self):
        queryset = Curso.objects.all()
        clave = self.request.query_params.get('clave', None)

        # Filtrar por 'clave' si se proporciona
        if clave is not None:
            queryset = queryset.filter(clave__icontains=clave)

        return queryset


class CompetenciasPorCursoView(generics.RetrieveAPIView):
    queryset = Curso.objects.all()
    serializer_class = CursoCompetenciaSerializer
    lookup_field = 'id'

    def get_queryset(self):
        curso_id = self.kwargs['id']
        return Curso.objects.filter(id=curso_id).prefetch_related('competencias')
    
 
    
##Leer CSV
# Función para extraer el número de horas desde la celda
def extraer_numero(celda):
    if isinstance(celda, str):
        return int(''.join(filter(str.isdigit, celda)))
    return celda  # En caso de que no sea un string

def mapear_nivel(nivel):
    nivel_str = str(nivel).strip()  # Convertir el nivel a string y eliminar espacios

    # Verificar si el nivel es un número entre 1 y 10
    if nivel_str.isdigit() and nivel_str in dict(TNivel.choices):
        return nivel_str  # Retornar el nivel como string
    print(f"NivelStr: {nivel_str} y Nivel: {nivel}")
    
    # Verificar si es 'E' o cualquier otra opción válida
    if int(nivel_str) == 0:
        return TNivel.ELECTIVO

    # Si no coincide con ningún valor válido, lanzar un error
    raise ValueError(f"Nivel '{nivel}' no es válido.")

# Función para procesar el campo 'requisitos' de cada curso
def procesar_requisitos(requisito, curso):
    requisito = requisito.strip().lower()

    # Caso 1: Si es un requisito de créditos (ejemplo: "44 créditos")
    if re.match(r"^\d+\s*créditos?$", requisito):
        total_creditos = float(re.search(r"\d+", requisito).group())
        requisito_creditos, _ = RequisitoCreditos.objects.get_or_create(total_creditos=total_creditos)
        curso.requisitos = requisito_creditos

    # Caso 2: Si no tiene requisitos ("no tiene")
    elif requisito == "no tiene":
        requisito_creditos, _ = RequisitoCreditos.objects.get_or_create(total_creditos=0)
        curso.requisitos = requisito_creditos

    # Caso 3: Si tiene una lista de cursos como requisito (ejemplo: "1MAT09, 1MAT10")
    else:
        # Separar las claves y buscar los cursos correspondientes
        claves_cursos = [clave.strip() for clave in requisito.split(',')]
        cursos_requisito = Curso.objects.filter(clave__in=claves_cursos)

        if cursos_requisito.exists():
            # **Crear un nuevo RequisitoCursos cada vez que se detecta una combinación de cursos**
            requisito_cursos = RequisitoCursos.objects.create()
            requisito_cursos.cursos.add(*cursos_requisito)  # Agregar los cursos
            requisito_cursos.save()  # Guardar la instancia en la base de datos

            # Asignar el requisito creado al curso actual
            curso.requisitos = requisito_cursos
        else:
            print(f"Advertencia: No se encontraron cursos para las claves: {claves_cursos}")

    # Guardar el curso con el requisito asignado
    curso.save()


class CargarCursosDesdeCSVView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        # Verificar si el archivo está presente en la solicitud
        archivo_csv = request.FILES.get('file')
        if not archivo_csv:
            return JsonResponse({"error": "No se proporcionó un archivo"}, status=400)

        # Leer el archivo CSV
        archivo_decodificado = archivo_csv.read().decode('utf-8')
        lector_csv = csv.DictReader(StringIO(archivo_decodificado))

        # Obtener dinámicamente las columnas de competencias desde la base de datos
        competencias_existentes = Competencia.objects.all().order_by('id')
        columnas_competencias = [f'competencia{idx + 1}' for idx, _ in enumerate(competencias_existentes)]

        # Definir las columnas requeridas
        columnas_requeridas = [
            'clave', 'nombre', 'nivel', 'creditos', 'tipo', 'sesiones', 'ME', 'requisitos'
        ] + columnas_competencias

        # Verificar que las columnas del CSV coincidan con las requeridas
        if not all(col in lector_csv.fieldnames for col in columnas_requeridas):
            return JsonResponse(
                {"error": "El archivo CSV no tiene las columnas requeridas"},
                status=400
            )

        # Procesar cada fila del archivo CSV
        cursos_cargados = []
        errores = []

        with transaction.atomic():
            for idx, fila in enumerate(lector_csv, start=1):
                try:
                    # Extraer y procesar los datos principales del curso
                    clave = fila['clave'].strip()
                    if not clave:
                        continue

                    curso = Curso.objects.create(
                        clave=clave,
                        nombre=fila['nombre'].strip(),
                        nivel=mapear_nivel(fila['nivel']),
                        creditos=float(fila['creditos']),
                        obligatorio=fila['tipo'].strip().startswith("01"),
                        numHoras=extraer_numero(fila['sesiones']),
                        formula=Formula.objects.get(id=fila['ME']),
                        activo=True
                    )

                    # Asignar competencias relacionadas
                    for idx_comp, valor_comp in enumerate(
                            [fila[col] for col in columnas_competencias], start=1):
                        if valor_comp.strip().lower() == 'x':
                            competencia = competencias_existentes[idx_comp - 1]
                            curso.competencias.add(competencia)

                    # Procesar los requisitos
                    procesar_requisitos(fila['requisitos'], curso)

                    cursos_cargados.append(curso.clave)
                except Exception as e:
                    errores.append(f"Error en la fila {idx}: {str(e)}")

        # Responder con los resultados del procesamiento
        return JsonResponse({
            "cursos_cargados": cursos_cargados,
            "errores": errores,
        })
        
        
## Cargar horarios
def generar_telefono_formateado():
    # Generar las tres partes del número
    parte1 = random.randint(900, 999)  # Ej: 987
    parte2 = random.randint(100, 999)  # Ej: 654
    parte3 = random.randint(100, 999)  # Ej: 321

    # Formatear como '987 654 321'
    telefono = f"{parte1} {parte2} {parte3}"
    return telefono


def crear_profesor_si_no_existe(clave_profesor):
    fake = Faker()
    try:
        profesor = Profesor.objects.get(codigo=clave_profesor)
    except ObjectDoesNotExist:
        # Crear un nuevo usuario usando Faker
        nombre = fake.first_name()
        primer_apellido = fake.last_name()
        segundo_apellido = fake.last_name()
        base_correo = f"{nombre.lower()}.{primer_apellido.lower()}@example.com"
        codigo = f"{clave_profesor}"  # Código único del profesor

        # Intentar crear el profesor y manejar duplicados de correo
        profesor = None
        intentos = 0
        while profesor is None and intentos < 5:
            correo = base_correo if intentos == 0 else f"{nombre.lower()}.{primer_apellido.lower()}{random.randint(1, 100)}@example.com"
            try:
                profesor = Profesor.objects.create(
                    nombre=nombre,
                    primerApellido=primer_apellido,
                    segundoApellido=segundo_apellido,
                    correo=correo,
                    codigo=codigo,
                    fechaRegistro=date.today(),
                    telefono=generar_telefono_formateado(),
                    activo=True,
                    tipo=TRol.REGULAR
                )
                print(f"Profesor {clave_profesor} creado con el usuario {profesor.nombre} y correo {correo}")
            except IntegrityError:
                print(f"El correo {correo} ya existe. Intentando con una variante...")
                intentos += 1

        if profesor is None:
            raise Exception(f"No se pudo crear el profesor {clave_profesor} después de varios intentos.")

    return profesor


class CargarHorariosDesdeCSVView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        # Verificar si el archivo está presente en la solicitud
        archivo_csv = request.FILES.get('file')
        if not archivo_csv:
            return JsonResponse({"error": "No se proporcionó un archivo"}, status=400)

        # Leer el archivo CSV
        archivo_decodificado = archivo_csv.read().decode('utf-8')
        lector_csv = csv.reader(StringIO(archivo_decodificado))

        # Variables para manejar valores previos
        horarios_previos = 0
        vacantes_previas = 0

        # Resultados
        horarios_cargados = []
        errores = []
        Horario.objects.all().update(activo=False)
        with transaction.atomic():
            # Procesar cada fila del archivo CSV
            for idx, fila in enumerate(lector_csv, start=1):
                try:
                    # Ignorar encabezados
                    if idx == 1:
                        continue

                    # Extraer valores principales
                    clave_curso = fila[0]
                    if not clave_curso:
                        continue  # Si la clave del curso está vacía, saltar la fila

                    # Buscar el curso por clave
                    try:
                        curso = Curso.objects.get(clave=clave_curso)
                    except ObjectDoesNotExist:
                        errores.append(f"Fila {idx}: Curso con clave {clave_curso} no existe.")
                        continue

                    # Obtener el número de horarios y vacantes
                    horarios = int(fila[1]) if fila[1] else horarios_previos
                    vacantes = int(fila[2]) if fila[2] else vacantes_previas

                    horarios_previos = horarios
                    vacantes_previas = vacantes

                    # Procesar pares clave_horario y clave_profesor
                    for col_horario, col_profesor in zip(range(3, len(fila), 2), range(4, len(fila), 2)):
                        clave_horario = fila[col_horario]
                        clave_profesor = fila[col_profesor]

                        if not clave_horario or not clave_profesor:
                            continue  # Si alguno de los dos está vacío, saltar

                        if clave_horario == '---':
                            continue  # Ignorar claves de horario vacías

                        # Crear o buscar el horario
                        horario, _ = Horario.objects.get_or_create(
                            claveHorario=clave_horario,
                            idCurso=curso,
                            defaults={
                                'numVacantes': vacantes,
                                'numMatriculados': 0,
                                'numAprobados': 0,
                                'numDesaprobados': 0
                            }
                        )

                        # Crear el profesor si no existe
                        profesor = crear_profesor_si_no_existe(clave_profesor)

                        # Asignar el profesor al horario
                        horario.idprofesor = profesor
                        horario.activo=True
                        horario.save()

                        # Agregar al listado de cargados
                        horarios_cargados.append(horario.claveHorario)

                except Exception as e:
                    errores.append(f"Fila {idx}: {str(e)}")

        # Responder con los resultados
        return JsonResponse({
            "horarios_cargados": horarios_cargados,
            "errores": errores
        })
        
        
##DEMANDA DE CURSOS
class CursosConCantidadDeAlumnosViewSet(viewsets.ViewSet):
    """
    Endpoint para listar los cursos junto con la cantidad de alumnos que los tienen como curso permitido.
    """
    def list(self, request):
        # Consultar los cursos y contar los alumnos permitidos
        cursos = Curso.objects.annotate(
            num_alumnos=Count('alumnos_permitidos', distinct=True)  # Conteo de alumnos relacionados
        ).filter(activo=True)

        # Serializar los datos manualmente
        cursos_data = [
            {
                "id": curso.id,
                "clave": curso.clave,
                "nombre": curso.nombre,
                "numHoras":curso.numHoras,
                "demanda_alumnos": curso.num_alumnos
            }
            for curso in cursos
        ]

        return Response(cursos_data)