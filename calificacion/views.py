from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from cursos.models import Horario
from .models import *
from .serializer import *
from rest_framework import generics
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
import csv
from io import StringIO
from django.db import transaction

# Create your views here.

class SubCompetenciaView(viewsets.ModelViewSet):
    serializer_class= SubCompetenciaSerializar
    queryset =SubCompetencia.objects.all()
    
class CompetenciaView(viewsets.ModelViewSet):
    serializer_class= CompetenciaSerializar
    
    def get_queryset(self):
        # Obtener el parámetro idCurso de la URL
        id_curso = self.request.query_params.get('idCurso', None)
        if id_curso is not None:
            return Competencia.objects.filter(idCurso=id_curso)
        return Competencia.objects.all()
    
class CompetenciaXHorarioView(viewsets.ModelViewSet):
    serializer_class= CompetenciaXHorarioSerializar
    queryset =CompetenciaXHorario.objects.all()
    
class NotaDisponibleView(viewsets.ModelViewSet):
    serializer_class = NotaDisponibleSerializar
    queryset = NotaDisponible.objects.all()
    
class NotaNumericaView(viewsets.ModelViewSet):
    serializer_class = NotaNumericaSerializer
    queryset = NotaNumerica.objects.all()
    
class NotaAlfabeticaSubView(viewsets.ModelViewSet):
    serializer_class = NotaAlfabeticaSubSerializar
    queryset = NotaAlfabeticaSub.objects.all()
    
class NotaAlfabeticaView(viewsets.ModelViewSet):
    serializer_class = NotaAlfabeticaSerializar
    queryset = NotaAlfabetica.objects.all()
    
class NotaXCompetenciaView(viewsets.ModelViewSet):
    serializer_class = NotaXCompetenciaSerializar
    queryset = NotaXCompetencia.objects.all()


##Guardar notas 
class GuardarNotasViewset(viewsets.ModelViewSet):
    serializer_class = GuardarNotasSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Notas guardadas exitosamente"}, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
##Mostrar notas

class NotasCursoViewSet(viewsets.ModelViewSet):
    
    serializer_class = VisualizarNotasSerializer # El serializador a utilizar

    # Sobrescribir el método get_queryset para filtrar por TipoDeNota, Indice y Horario
     
    def get_queryset(self):
        # Obtener los parámetros de la query string
        tipoDeNota = self.request.query_params.get('tipoDeNota')
        indice = self.request.query_params.get('indice')
        horario_id = self.request.query_params.get('horario_id')
        periodo_id = self.request.query_params.get('periodo_id')

        # Asegurarse de que todos los parámetros están presentes
        if not (tipoDeNota and indice and horario_id):
            return AlumnoXHorario.objects.none()  # Devolver queryset vacío si faltan parámetros

        # Filtrar las relaciones AlumnoXHorario por el horario
        print(f"{periodo_id}")
        return AlumnoXHorario.objects.filter(horario_id=horario_id,periodo__id=periodo_id)
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()  # Obtener los resultados filtrados

        # Pasar los parámetros tipoDeNota e indice al contexto del serializador
        serializer = self.get_serializer(queryset, many=True, context={
            'tipoDeNota': request.query_params.get('tipoDeNota'),
            'indice': request.query_params.get('indice')
        })

        # Devolver los datos serializados
        return Response(serializer.data)
    

class CursoEvaluacionesListView(generics.ListAPIView):

    def get(self, request, *args, **kwargs):
        alumno_id = self.kwargs.get('alumno_id')
        periodo_id = self.request.query_params.get('periodo_id')
        
        # Filtrar las relaciones AlumnoXHorario según alumno y periodo
        cursos = AlumnoXHorario.objects.filter(
            alumno_id=alumno_id,
            periodo_id=periodo_id
        ).select_related('horario__idCurso', 'horario__idCurso__formula')
        
        resultado = []
        
        for curso_horario in cursos:
            curso = curso_horario.horario.idCurso
            formula = curso.formula
            
            # Filtrar las notas numéricas
            notas = curso_horario.notasNumericas.all() 
            
            # Estructurar datos para el serializer, asignando -1 en caso de valor None
            resultado.append({
                "curso_nombre": curso.nombre,
                "curso_clave": curso.clave,
                "formula": {
                    "pesoParciales": formula.pesoParciales,
                    "pesoFinales": formula.pesoFinales,
                    "pesoPracticas": formula.pesoPracticas,
                },
                "evaluaciones": [
                    {
                        "tipo": nota.tipoDeNota,
                        "indice": nota.indice,
                        "valor": nota.valor if nota.valor is not None else -1,
                    }
                    for nota in notas
                ],
                "promedioPcs": curso_horario.promedioPcs,
                "promedioFinal": curso_horario.promedioFinal
            })

        # Serializar los resultados
        serializer = AlumnoCursoEvaluacionesSerializer({'cursos': resultado})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class CursosConNotasCompetenciasView(generics.ListAPIView):
    serializer_class = CursoConNotasCompetenciasSerializer

    def get_queryset(self):
        alumno_id = self.kwargs['alumno_id']
        periodo_id = self.request.query_params.get('periodo_id')  # Obtener el periodo_id de los parámetros de consulta
        queryset = AlumnoXHorario.objects.filter(alumno_id=alumno_id)

        # Filtrar por el periodo si está presente en la URL
        if periodo_id:
            queryset = queryset.filter(periodo_id=periodo_id)

        return queryset

    
## Competencias de un horario de profesor 
class CompetenciaXHorarioxProfeViewSet(viewsets.ModelViewSet):
    
    @action(detail=False, methods=['get'], url_path='competencias')
    def listar_competencias(self, request):
        # Obtener los parámetros de la query string
        idprofesor = request.query_params.get('idprofesor')
        idhorario = request.query_params.get('idhorario')
        filtro_competencia = request.query_params.get('competencia', None)

        # Validar que los parámetros idprofesor e idhorario existan
        if not idprofesor or not idhorario:
            return Response(
                {"error": "Se requieren los parámetros 'idprofesor' e 'idhorario'."},
                status=400
            )

        # Verificar si el horario existe y corresponde al profesor
        horario = get_object_or_404(Horario, id=idhorario, idprofesor_id=idprofesor)

        # Obtener las competencias asociadas al horario
        competencias_x_horario = CompetenciaXHorario.objects.filter(idHorario=horario)

        # Si se proporcionó el parámetro 'competencia', filtrar por nombre de competencia
        if filtro_competencia:
            competencias_x_horario = competencias_x_horario.filter(
                idCompetencia__nombre__icontains=filtro_competencia
            )

        # Serializar las competencias junto con su cantidad de evaluaciones
        serializer = CompetenciasxHorariosXProfeserializer(competencias_x_horario, many=True)

        # Devolver la respuesta
        return Response(serializer.data)
    
    ## Actualizar la cantidad de evaluaciones
    @action(detail=False, methods=['post'], url_path='actualizar-cantidad')
    def actualizar_cantidad_evaluaciones(self, request):
        # Extraer los parámetros del JSON
        horarioxcomp = request.data.get('horarioxcomp')
        cantidad = request.data.get('cantidad')

        # Validar que los parámetros existan
        if not (horarioxcomp and cantidad):
            return Response(
                {"error": "Se requieren los parámetros 'horarioxcomp'y 'cantidad'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Buscar la instancia de CompetenciaXHorario
        competencia_x_horario = get_object_or_404(
            CompetenciaXHorario, id=horarioxcomp
        )

        # Serializar y actualizar los datos
        serializer = ActualizarCantidadEvaluacionesSerializer(
            competencia_x_horario, data=request.data
        )
        if serializer.is_valid():
            serializer.save()
            return Response({"mensaje": "Cantidad de evaluaciones actualizada correctamente."}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    
## Ver calificacion de competencias en un horario
class ProfAlumnoXHorarioxCalificacionViewSet(viewsets.ViewSet):
    
    ##Guardar las notas
    @action(detail=False, methods=['post'], url_path='guardar')
    def guardar_notas(self, request):
        # Obtener los parámetros de la query string
        indice = request.data.get('indice')
        idhorario = request.data.get('horario')
        idcompetencia = request.data.get('competencia')

        # Validar los parámetros
        if not indice or not idhorario or not idcompetencia:
            return Response(
                {"error": "Se requieren los parámetros 'indice', 'horario' y 'competencia'."},
                status=400
            )

        # Verificar que el horario y la competencia existan
        horario = get_object_or_404(Horario, id=idhorario)
        competencia = get_object_or_404(Competencia, id=idcompetencia)

        # Iterar sobre cada alumno enviado en la request
        alumnos_data = request.data.get('alumnos', [])

        for alumno_data in alumnos_data:
            alumno_x_horario_id = alumno_data.get('alumno_x_horario_id')
            #print(f"{alumno_x_horario_id}")
            # Buscar al alumno en el horario correspondiente
            alumno_horario = AlumnoXHorario.objects.filter(
                id = alumno_x_horario_id
            ).first()

            if not alumno_horario:
                return Response(
                    {"error": f"AlumnoxHorario con código {alumno_x_horario_id} no encontrado."},
                    status=404
                )

            # Iterar sobre las notas por competencia del alumno
            for nota_competencia_data in alumno_data.get('notas_de_competencia', []):
                nota_x_competencia, _ = NotaXCompetencia.objects.get_or_create(
                    idAlumnoXHorario=alumno_horario, idCompetencia=competencia,
                    defaults={'notaFinal': ".", 'retroalimentacionFinal': "."}
                )

                # Iterar sobre las notas alfabéticas
                for nota_alfabetica_data in nota_competencia_data.get('notas_alfabeticas', []):
                    valor_alfabetico = nota_alfabetica_data.get('valor', ".")
                    retroalimentacion = nota_alfabetica_data.get('retroalimentacion', ".")
                    
                    
                    #print(f"Valor: {valor_alfabetico}  +  Retro: {retroalimentacion}" )
                    #print(f"IdNotaxComp: {nota_x_competencia.id} + Indice: {indice}")
                    # Crear o actualizar la nota alfabética
                    nota_alfabetica, created = NotaAlfabetica.objects.update_or_create(
                        idNotaXCompetencia=nota_x_competencia.id,
                        indice=indice,
                        defaults={
                            'valor': valor_alfabetico,
                            'retroalimentacion': retroalimentacion
                        }
                    )

                    # Iterar sobre las sub-notas alfabéticas
                    for sub_nota_data in nota_alfabetica_data.get('sub_notas', []):
                        clave_subcompetencia = sub_nota_data.get('clave')
                        valor_sub_nota = sub_nota_data.get('valor', ".")

                        # Buscar la subcompetencia correspondiente
                        subcompetencia = SubCompetencia.objects.filter(
                            idCompetencia=competencia, clave=clave_subcompetencia
                        ).first()

                        if not subcompetencia:
                            return Response(
                                {"error": f"Subcompetencia con clave {clave_subcompetencia} no encontrada."},
                                status=404
                            )

                        # Crear o actualizar la sub-nota alfabética
                        NotaAlfabeticaSub.objects.update_or_create(
                            idNotaAlfabetica=nota_alfabetica.id, idSubCompetencia=subcompetencia.id,
                            defaults={'valor': valor_sub_nota}
                        )

        # Serializar la información actualizada
        alumnos_x_horario = AlumnoXHorario.objects.filter(horario=horario)
        serializer = ProfAlumnoXHorarioSerializer(alumnos_x_horario, many=True)

        # Devolver la respuesta completa
        return Response(serializer.data)


## 
class ProfCalifiacionCompetenciasXIndice(viewsets.ViewSet):

    @action(detail=False, methods=['get'], url_path='alumnos')
    def listar_alumnos(self, request):
        # Obtener los parámetros de la query string
        idhorario = request.query_params.get('idhorario')
        idcompetencia = request.query_params.get('idcompetencia')
        indice = request.query_params.get('indice')

        # Validar los parámetros
        if not idhorario or not idcompetencia or not indice:
            return Response(
                {"error": "Se requieren los parámetros 'idhorario', 'idcompetencia' e 'indice'."},
                status=400
            )

        # Verificar que el horario y la competencia existan
        horario = get_object_or_404(Horario, id=idhorario)
        competencia = get_object_or_404(Competencia, id=idcompetencia)

        # Filtrar los alumnos por horario
        alumnos_x_horario = AlumnoXHorario.objects.filter(horario=horario)

        # Iterar sobre cada alumno y verificar si ya tiene notas para el índice especificado
        for alumno_x_horario in alumnos_x_horario:
            nota_x_competencia, created = NotaXCompetencia.objects.get_or_create(
                idAlumnoXHorario=alumno_x_horario, 
                idCompetencia=competencia,
                defaults={'notaFinal': ".", 'retroalimentacionFinal': "."}
            )

            # Crear o verificar la existencia de una nota alfabética para el índice dado
            nota_alfabetica, created = NotaAlfabetica.objects.get_or_create(
                idNotaXCompetencia=nota_x_competencia,
                indice=indice,
                defaults={'valor': ".", 'retroalimentacion': "."}
            )

            # Obtener las subcompetencias de la competencia
            subcompetencias = SubCompetencia.objects.filter(idCompetencia=competencia)
            for subcompetencia in subcompetencias:
                # Crear o verificar la existencia de una nota alfabética sub para cada subcompetencia
                NotaAlfabeticaSub.objects.get_or_create(
                    idNotaAlfabetica=nota_alfabetica,
                    idSubCompetencia=subcompetencia,
                    defaults={'valor': "."}
                )

        # Serializar los datos de alumnos con sus notas y enviar el índice en el contexto
        serializer = ProfAlumnoXHorarioSerializer(
            alumnos_x_horario, 
            many=True, 
            context={'indice': int(indice)}
        )

        # Devolver la respuesta en JSON
        return Response(serializer.data)
    
## http://127.0.0.1:8000/calificacion/alumnosxhorario/alumnos/?idhorario=1&idcompetencia=2
    
    
##Nota finales

class NotaFinalViewSet(viewsets.ViewSet):

    @action(detail=False, methods=['post'], url_path='guardar')
    def guardar_notas_finales(self, request):
        # Extraer el ID de la competencia
        id_competencia = request.data.get('competencia')
        if not id_competencia:
            return Response(
                {"error": "Se requiere el parámetro 'competencia'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Obtener la lista de alumnos del JSON
        alumnos_data = request.data.get('alumnos', [])
        errores = []

        for alumno_data in alumnos_data:
            # Agregar el ID de la competencia al contexto

            serializer = NotaFinalSerializer(
                data=alumno_data,
                context={'competencia': id_competencia})
            if serializer.is_valid():
                serializer.save()
            else:
                errores.append(serializer.errors)

        if errores:
            return Response(errores, status=status.HTTP_400_BAD_REQUEST)

        return Response({"mensaje": "Notas finales guardadas correctamente."}, status=status.HTTP_201_CREATED)

##Lista de subcomp de competencia
class CompetenciaDetailView(generics.RetrieveAPIView):
    queryset = Competencia.objects
    serializer_class = CompetenciaDetailSerializer
    lookup_field = 'id'

    def get(self, request, *args, **kwargs):
        competencia = self.get_object()
        serializer = self.get_serializer(competencia)
        return Response(serializer.data, status=status.HTTP_200_OK)
    


##CARGAR COMPETENCIAS
class CargarCompetenciasDesdeCSVView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        # Verificar si el archivo está presente en la solicitud
        archivo_csv = request.FILES.get('file')
        if not archivo_csv:
            return JsonResponse({"error": "No se proporcionó un archivo"}, status=400)

        # Leer el archivo CSV
        archivo_decodificado = archivo_csv.read().decode('utf-8')
        lector_csv = csv.DictReader(StringIO(archivo_decodificado))

        # Verificar la estructura del archivo CSV
        columnas_requeridas = [
            'idcompetencia', 'nombre_competencia', 'descripcion_competencia',
            'idsubcompetencia', 'nombre_subcompetencia', 'descripción_subcompetencia',
            'criterio_inicial', 'criterio_en_proceso', 'criterio_satisfactorio', 'criterio_sobresaliente'
        ]
        if not all(col in lector_csv.fieldnames for col in columnas_requeridas):
            return JsonResponse(
                {"error": "El archivo CSV no tiene las columnas requeridas"},
                status=400
            )

        # Procesar cada fila del archivo CSV
        competencias_creadas = []
        subcompetencias_creadas = []
        errores = []

        with transaction.atomic():
            competencia_actual = None
            clave_anterior = None

            for idx, fila in enumerate(lector_csv, start=1):
                try:
                    clave_actual = fila['idcompetencia']

                    # Verificar si la competencia debe ser creada o si es la misma que la fila anterior
                    if clave_actual != clave_anterior:
                        competencia_actual, creada = Competencia.objects.get_or_create(
                            clave=clave_actual,
                            defaults={
                                'nombre': fila['nombre_competencia'],
                                'descripcion': fila['descripcion_competencia'],
                                'activo': True
                            }
                        )
                        if creada:
                            competencias_creadas.append(competencia_actual.clave)

                        # Actualizar la clave anterior
                        clave_anterior = clave_actual

                    # Crear la SubCompetencia para la competencia actual
                    subcompetencia = SubCompetencia.objects.create(
                        idCompetencia=competencia_actual,
                        nombre=fila['nombre_subcompetencia'],
                        clave=fila['idsubcompetencia'],
                        descripcion=fila['descripción_subcompetencia'],
                        nivelInicial=fila['criterio_inicial'],
                        nivelEnProceso=fila['criterio_en_proceso'],
                        nivelSatisfactorio=fila['criterio_satisfactorio'],
                        nivelSobresaliente=fila['criterio_sobresaliente'],
                        activo=True
                    )
                    subcompetencias_creadas.append(subcompetencia.clave)

                except Exception as e:
                    errores.append(f"Error en la fila {idx}: {str(e)}")

        # Responder con los resultados del procesamiento
        return JsonResponse({
            "competencias_creadas": competencias_creadas,
            "subcompetencias_creadas": subcompetencias_creadas,
            "errores": errores,
        })