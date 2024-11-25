# Create your views here.
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework import status
from django.db.models import Count  # Agrega esta línea
from django.db import transaction
from .serializer import *
from .models import *
from rest_framework import generics
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
# Create your views here.

class LineaInscripcionView(viewsets.ModelViewSet):
    serializer_class= LineaInscripcionSerializar
    queryset =LineaInscripcion.objects.all()

class InscripcionView(viewsets.ModelViewSet):
    queryset = Inscripcion.objects.all()
    serializer_class = InscripcionSerializar



class AlumnoXHorarioView(viewsets.ModelViewSet):
    queryset = AlumnoXHorario.objects.all()
    serializer_class = AlumnoXHorarioSerializar



##Vista profesor-Información del curso ------- James y Fernando##
class AlumnosHorarioViewSet(viewsets.ModelViewSet):
    queryset = Horario.objects.all()

    @action(detail=False, methods=['get'], url_path=r'horario/(?P<horario_id>\d+)') #http://127.0.0.1:8000/matricula/alumnos_horario/horario/1/
    def alumnos_por_horario(self, request, horario_id=None):
        # Obtener los parámetros de búsqueda (opcional)
        codigo = request.query_params.get('codigo', None)
        periodo = request.query_params.get('periodo', None)

        # Obtener el horario en base al ID
        try:
            horario = Horario.objects.get(id=horario_id)
        except Horario.DoesNotExist:
            return Response({"error": "Horario no encontrado"}, status=404)

        # Filtrar las inscripciones relacionadas con este horario
        inscripciones = AlumnoXHorario.objects.filter(horario=horario)

        # Si se proporciona un parámetro de periodo, aplicar filtro adicional
        if periodo:
            inscripciones = inscripciones.filter(periodo_id=periodo)

        # Si se proporciona un código parcial, aplicar filtro adicional
        if codigo:
            inscripciones = inscripciones.filter(alumno__codigo__icontains=codigo)

        # Serializar las inscripciones
        serializer = AlumnoXIdHorarioSerializar(inscripciones, many=True, context={'horario_id': horario_id})
        
        # Devolver la respuesta serializada
        return Response(serializer.data)

class CursosRetiradosViewSet(viewsets.ViewSet):

    @action(detail=False, methods=['post'], url_path='solicitar-retiro')
    def solicitar_retiro(self, request):
        """Crea un registro de solicitud de retiro en la tabla RetiroAlumno"""
        id_alumnoxhorarios = request.data.get('idAlumnoXHorarios', [])
        justificacion = request.data.get('justificacion', '')

        if not id_alumnoxhorarios:
            return Response({'error': 'Faltan los registros de AlumnoXHorario para procesar la solicitud'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                retiro_records = [
                    AlumnoRetiro(idAlumnoXHorario_id=id_alumnoxhorario, justificacion=justificacion)
                    for id_alumnoxhorario in id_alumnoxhorarios
                ]
                AlumnoRetiro.objects.bulk_create(retiro_records)

            return Response({'message': 'La solicitud de retiro ha sido registrada exitosamente'}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='aprobar-retiro')
    def aprobar_retiro(self, request):
        """Aprueba el retiro del alumno, actualizando las tablas RetiroAlumno y AlumnoXHorario"""
        id_retiros = request.data.get('idRetiros', [])

        if not id_retiros:
            return Response({'error': 'Faltan los registros de retiro para aprobar'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # Actualizar los retiros aprobados
                AlumnoRetiro.objects.filter(id__in=id_retiros).update(estadoSolicitud=True, estadoRetiro=True)

                # Actualizar AlumnoXHorario: marcar como retirado
                AlumnoXHorario.objects.filter(retiroHorarios__id__in=id_retiros).update(retirado=True)

            return Response({'message': 'Los retiros han sido aprobados exitosamente'}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='rechazar-retiro')
    def rechazar_retiro(self, request):
        """Rechaza la solicitud de retiro, actualizando el estado en RetiroAlumno"""
        id_retiros = request.data.get('idRetiros', [])

        if not id_retiros:
            return Response({'error': 'Faltan los registros de retiro para rechazar'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # Actualizar el estado de la solicitud como rechazada
                AlumnoRetiro.objects.filter(id__in=id_retiros).update(estadoSolicitud=False)

            return Response({'message': 'Las solicitudes de retiro han sido rechazadas'}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
##Vista de Cursos Matriculados/ Inscritos

    
# Datos de matrícula


# Mostrar línea de inscripción de cursos
class InscripcionDetailView(APIView):
    def get(self, request, alumno_id):
        # Obtener la inscripción activa del alumno
        try:
            inscripcion = Inscripcion.objects.get(alumno_id=alumno_id, activo=True)
        except Inscripcion.DoesNotExist:
            return Response(
                {"error": "Inscripción activa no encontrada para el alumno especificado."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Estructura básica de respuesta
        response_data = {
            "id": inscripcion.id,
            "lineas": []
        }

        # Obtener todas las líneas de inscripción asociadas a esta inscripción
        lineas_inscripcion = LineaInscripcion.objects.filter(inscripcion=inscripcion)

        for linea in lineas_inscripcion:
            curso = linea.horario.idCurso
            profesor = linea.horario.idprofesor

            # Agregar los datos de cada línea de inscripción al JSON
            linea_data = {
                "idLinea": linea.id,
                "clave": curso.clave,
                "nombre": curso.nombre,
                "creditos": curso.creditos,
                "horario": linea.horario.claveHorario,
                "posicionrelativa": linea.posicionRelativa,
                "numVacantes": linea.horario.numVacantes,
                "profesor": f"{profesor.nombre} {profesor.primerApellido}" if profesor else "Sin asignar",
                "numHoras": curso.numHoras,
                "extemporanea":linea.extemporanea,
                "seleccionado":linea.seleccionado
            }
            response_data["lineas"].append(linea_data)

        return Response(response_data, status=status.HTTP_200_OK)
    
    
## Guardar cursos seleccionados en linea inscripcion
class GuardarLineasDeInscripcionView(APIView):
    def post(self, request):
        data = request.data

        # Extraer ID del Alumno y las líneas de inscripción
        id_alumno = data.get("idAlumno")
        lineas_data = data.get("lineas", [])

        if not id_alumno or not lineas_data:
            return Response(
                {"error": "El JSON debe contener 'idAlumno' y una lista de 'lineas'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar que el alumno exista y esté asociado a una inscripción
        periodo_actual = PeriodoAcademico.objects.filter(actual=True).first()
        print(f"Periodo: {periodo_actual}")
        try:
            alumno = Alumno.objects.get(id=id_alumno)
            inscripcion = Inscripcion.objects.get(alumno=alumno, periodo=periodo_actual, activo=True)
        except Alumno.DoesNotExist:
            return Response({"error": "Alumno no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        except Inscripcion.DoesNotExist:
            return Response({"error": "No se encontró una inscripción activa para el alumno"}, status=status.HTTP_404_NOT_FOUND)

        # Validar y guardar líneas de inscripción
        with transaction.atomic():
            cursos_inscritos = set()  # Mantiene un registro de cursos inscritos en este periodo
            # Obtener cursos ya inscritos en otros horarios
            lineas_existentes = LineaInscripcion.objects.filter(inscripcion=inscripcion)
            for linea in lineas_existentes:
                cursos_inscritos.add(linea.horario.idCurso.id)

            for linea in lineas_data:
                id_horario = linea.get("idHorario")

                if not id_horario:
                    return Response(
                        {"error": "Cada línea debe contener un 'idHorario'"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                try:
                    horario = Horario.objects.get(id=id_horario)
                except Horario.DoesNotExist:
                    return Response({"error": f"Horario con id {id_horario} no encontrado"}, status=status.HTTP_404_NOT_FOUND)

                # Validar que el curso del horario esté en los cursos permitidos del alumno
                if horario.idCurso not in alumno.cursosPermitidos.all():
                    return Response(
                        {"error": f"El curso '{horario.idCurso.nombre}' no está permitido para el alumno."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Validar que no se inscriba en otro horario del mismo curso
                if horario.idCurso.id in cursos_inscritos:
                    return Response(
                        {"error": f"El alumno ya está inscrito en un horario del curso '{horario.idCurso.nombre}'."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Registrar el curso en el set de cursos inscritos
                cursos_inscritos.add(horario.idCurso.id)

                # Crear una nueva línea de inscripción
                info= InformacionMatricula.objects.first()
                if(info.estadoMatricula == TEstadoMatricula.MATRICULAEXTEMPORANEA):
                    LineaInscripcion.objects.create(
                        horario=horario,
                        inscripcion=inscripcion,
                        posicionRelativa=0,  # Será actualizado después si es necesario
                        seleccionado=False,
                        permitido=True,
                        extemporanea=True
                    )
                else:
                    LineaInscripcion.objects.create(
                        horario=horario,
                        inscripcion=inscripcion,
                        posicionRelativa=0,  # Será actualizado después si es necesario
                        seleccionado=False,
                        permitido=True,
                        extemporanea=False
                    )
                
                self.actualizar_posiciones_relativas(periodo_actual)

            # Opcional: Actualizar posiciones relativas si tienes esa lógica
            

        return Response({"success": "Líneas de inscripción guardadas correctamente"}, status=status.HTTP_201_CREATED)

    def actualizar_posiciones_relativas(self, periodo_actual):
    #"""
    #Actualiza las posiciones relativas de todas las líneas de inscripción 
    #agrupándolas por horario, en función del turno de matrícula de los alumnos.
    #"""
    # Filtrar las líneas activas del periodo actual
        lineas = LineaInscripcion.objects.filter(
            inscripcion__periodo=periodo_actual,
            activo=True
        ).select_related('horario', 'inscripcion__alumno')

        # Agrupar por horario
        from itertools import groupby
        lineas_ordenadas = lineas.order_by('horario', 'inscripcion__alumno__turnoOrdenMatricula')

        # Agrupamos las líneas por cada horario
        for horario, grupo in groupby(lineas_ordenadas, key=lambda x: x.horario):
            # Enumerar las posiciones dentro de cada grupo
            for posicion, linea in enumerate(grupo, start=1):
                linea.posicionRelativa = posicion
                linea.save()
            
            
#Eliminar linea de inscripción
class EliminarLineasDeInscripcionView(APIView):
    def post(self, request):
        data = request.data

        # Extraer datos del JSON
        id_alumno = data.get("idAlumno")
        lineas_data = data.get("lineas", [])

        # Validar que el JSON contenga los campos necesarios
        if not id_alumno or not lineas_data:
            return Response(
                {"error": "El JSON debe contener 'idAlumno' y una lista de 'lineas'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar que el alumno exista y esté habilitado
        try:
            alumno = Alumno.objects.get(id=id_alumno, habilitado=True)
        except Alumno.DoesNotExist:
            return Response(
                {"error": "Alumno no encontrado o no habilitado"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Filtrar el periodo actual
        periodo_actual = PeriodoAcademico.objects.filter(actual=True).first()
        if not periodo_actual:
            return Response({"error": "No hay un periodo académico activo"}, status=status.HTTP_404_NOT_FOUND)

        # Verificar que el alumno tenga una inscripción activa
        try:
            inscripcion = Inscripcion.objects.get(alumno=alumno, periodo=periodo_actual, activo=True)
        except Inscripcion.DoesNotExist:
            return Response(
                {"error": "No se encontró una inscripción activa para el alumno en el periodo actual"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Eliminar las líneas de inscripción indicadas
        for linea in lineas_data:
            id_linea = linea.get("idLinea")
            if not id_linea:
                return Response(
                    {"error": "Cada entrada en 'lineas' debe contener 'idLinea'"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                linea_inscripcion = LineaInscripcion.objects.get(id=id_linea, inscripcion=inscripcion)
                linea_inscripcion.delete()
            except LineaInscripcion.DoesNotExist:
                return Response(
                    {"error": f"No se encontró una línea de inscripción con id {id_linea} para el alumno"},
                    status=status.HTTP_404_NOT_FOUND
                )
            self.actualizar_posiciones_relativas(periodo_actual)

        # Actualizar posiciones relativas después de eliminar
        

        return Response({"success": "Líneas de inscripción eliminadas y posiciones actualizadas"}, status=status.HTTP_200_OK)

    def actualizar_posiciones_relativas(self, periodo_actual):
        """
        Actualiza las posiciones relativas de las líneas de inscripción
        agrupadas por horario en función del turno de matrícula de los alumnos.
        """
        # Filtrar las líneas activas del periodo actual
        lineas = LineaInscripcion.objects.filter(
            inscripcion__periodo=periodo_actual,
            activo=True
        ).select_related('horario', 'inscripcion__alumno')

        # Agrupar por horario
        from itertools import groupby
        lineas_ordenadas = lineas.order_by('horario', 'inscripcion__alumno__turnoOrdenMatricula')

        # Agrupamos las líneas por cada horario
        for horario, grupo in groupby(lineas_ordenadas, key=lambda x: x.horario):
            # Enumerar las posiciones dentro de cada grupo
            for posicion, linea in enumerate(grupo, start=1):
                linea.posicionRelativa = posicion
                linea.save()
                 


##Guarda retiros
class GuardarRetirosView(APIView):

    def post(self, request):
        data = request.data

        # Validar que los datos necesarios están presentes
        justificacion = data.get("justificacion")
        lista_cursos = data.get("lista_cursos")

        if not justificacion or not lista_cursos:
            return Response(
                {"error": "El JSON debe contener 'justificacion' y una lista de 'lista_cursos'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Procesar cada curso en la lista de cursos
        for curso in lista_cursos:
            id_alumnoxhorario = curso.get("idAlumnoxHorario")
            estado_solicitud = curso.get("estadoSolicitud")
            estado_retiro = curso.get("estadoRetiro")

            if id_alumnoxhorario is None or estado_solicitud is None or estado_retiro is None:
                return Response(
                    {"error": "Cada entrada en 'lista_cursos' debe contener 'idAlumnoxHorario', 'estadoSolicitud', y 'estadoRetiro'"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Verificar que el AlumnoXHorario existe
            alumnoxhorario = get_object_or_404(AlumnoXHorario, id=id_alumnoxhorario)

            # Crear una nueva instancia de AlumnoRetiro
            AlumnoRetiro.objects.create(
                idAlumnoXHorario=alumnoxhorario,
                justificacion=justificacion,
                estadoSolicitud=estado_solicitud,
                estadoRetiro=estado_retiro
            )

        # Respuesta exitosa
        return Response({"success": "Datos de retiros guardados correctamente"}, status=status.HTTP_201_CREATED)

## Ver retiros de alumno
class RetiroAlumnoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AlumnoRetiro.objects.all()
    serializer_class = RetiroAlumnoSerializer

    #Listar todas las solicitudes de retiro
    def list(self, request):
        retiros = self.get_queryset()
        serializer = self.get_serializer(retiros, many=True)
        return Response(serializer.data)
    
    #Obtener las solicitudes de un alumno
    #Default Router ya tiene el nuevo endpoint generado por decorator @action
    #URL -> http://127.0.0.1:8000/matricula/retiros_alumno/alumno/<alumno_id>/
    @action(detail=False, methods=['get'], url_path='alumno/(?P<alumno_id>[^/.]+)')
    def get_retiros_por_alumno(self, request, alumno_id=None):
        # Filtrar las solicitudes de retiro por el ID del alumno
        retiros = AlumnoRetiro.objects.filter(idAlumnoXHorario__alumno__id=alumno_id)
        
        # Serializar los datos y devolver la respuesta
        serializer = self.get_serializer(retiros, many=True)
        return Response(serializer.data)
    

## Ver informacion del estado del campus
class InformacionMatriculaView(viewsets.ModelViewSet):
    serializer_class=InformacionMatriculaSerializer
    queryset=InformacionMatricula.objects.all()
    
## Cambiar de estado de campus
class CambiarEstadoCampusView(viewsets.GenericViewSet):
    @action(detail=False, methods=['get'], url_path='prematricula')
    def cambiar_a_prematricula(self, request):
        # Obtener el registro de InformacionMatricula (asumiendo que hay solo uno)
        info = InformacionMatricula.objects.first()

        if not info:
            return Response(
                {"error": "No se encontró ningún registro de Información de Matrícula."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Cambiar el estado
        info.estadoMatricula = TEstadoMatricula.PREMATRICULA
        info.save()

        return Response(
            {"message": f"Estado cambiado a {TEstadoMatricula.PREMATRICULA}."},
            status=status.HTTP_200_OK
        )
        
    @action(detail=False, methods=['get'], url_path='matricula')
    def cambiar_a_matricula(self, request):
        # Obtener el registro de InformacionMatricula (asumiendo que hay solo uno)
        info = InformacionMatricula.objects.first()

        if not info:
            return Response(
                {"error": "No se encontró ningún registro de Información de Matrícula."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Cambiar el estado
        info.estadoMatricula = TEstadoMatricula.MATRICULA
        info.save()

        return Response(
            {"message": f"Estado cambiado a {TEstadoMatricula.MATRICULA}."},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'], url_path='publicacion_matricula')
    def cambiar_a_publicacion_matricula(self, request):
        # Obtener el registro de InformacionMatricula (asumiendo que hay solo uno)
        info = InformacionMatricula.objects.first()

        if not info:
            return Response(
                {"error": "No se encontró ningún registro de Información de Matrícula."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Cambiar el estado
        info.estadoMatricula = TEstadoMatricula.PUBLICACIONMATRICULA
        info.save()

        return Response(
            {"message": f"Estado cambiado a {TEstadoMatricula.PUBLICACIONMATRICULA}."},
            status=status.HTTP_200_OK
        )
        
    @action(detail=False, methods=['get'], url_path='matricula_extemp')
    def cambiar_a_matricula_extemp(self, request):
        # Obtener el registro de InformacionMatricula (asumiendo que hay solo uno)
        info = InformacionMatricula.objects.first()

        if not info:
            return Response(
                {"error": "No se encontró ningún registro de Información de Matrícula."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Cambiar el estado
        info.estadoMatricula = TEstadoMatricula.MATRICULAEXTEMPORANEA
        info.save()

        return Response(
            {"message": f"Estado cambiado a {TEstadoMatricula.MATRICULAEXTEMPORANEA}."},
            status=status.HTTP_200_OK
        )
        
    @action(detail=False, methods=['get'], url_path='publicacion_extemp')
    def cambiar_a_publicacion_extemp(self, request):
        # Obtener el registro de InformacionMatricula (asumiendo que hay solo uno)
        info = InformacionMatricula.objects.first()

        if not info:
            return Response(
                {"error": "No se encontró ningún registro de Información de Matrícula."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Cambiar el estado
        info.estadoMatricula = TEstadoMatricula.PUBLICACIONMATEXTEMPORANEA
        info.save()

        return Response(
            {"message": f"Estado cambiado a {TEstadoMatricula.PUBLICACIONMATEXTEMPORANEA}."},
            status=status.HTTP_200_OK
        )
        
    @action(detail=False, methods=['get'], url_path='ciclo_lectivo')
    def cambiar_a_ciclo_lectivo(self, request):
        # Obtener el registro de InformacionMatricula (asumiendo que hay solo uno)
        info = InformacionMatricula.objects.first()

        if not info:
            return Response(
                {"error": "No se encontró ningún registro de Información de Matrícula."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Cambiar el estado
        info.estadoMatricula = TEstadoMatricula.CICLOLECTIVO
        info.save()

        return Response(
            {"message": f"Estado cambiado a {TEstadoMatricula.CICLOLECTIVO}."},
            status=status.HTTP_200_OK
        )
        
    @action(detail=False, methods=['get'], url_path='fin_de_ciclo')
    def cambiar_a_fin_de_cilo(self, request):
        # Obtener el registro de InformacionMatricula (asumiendo que hay solo uno)
        info = InformacionMatricula.objects.first()

        if not info:
            return Response(
                {"error": "No se encontró ningún registro de Información de Matrícula."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Cambiar el estado
        info.estadoMatricula = TEstadoMatricula.FINDECICLO
        info.save()

        return Response(
            {"message": f"Estado cambiado a {TEstadoMatricula.FINDECICLO}."},
            status=status.HTTP_200_OK
        )
    
    
## Ver retiros de alumno
class RetiroAlumnoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AlumnoRetiro.objects.all()
    serializer_class = RetiroAlumnoSerializer

    #Listar todas las solicitudes de retiro
    def list(self, request):
        retiros = self.get_queryset()
        serializer = self.get_serializer(retiros, many=True)
        return Response(serializer.data)
    
    #Obtener las solicitudes de un alumno
    #Default Router ya tiene el nuevo endpoint generado por decorator @action
    #URL -> http://127.0.0.1:8000/matricula/retiros_alumno/alumno/<alumno_id>/
    @action(detail=False, methods=['get'], url_path='alumno/(?P<alumno_id>[^/.]+)')
    def get_retiros_por_alumno(self, request, alumno_id=None):
        # Filtrar las solicitudes de retiro por el ID del alumno
        retiros = AlumnoRetiro.objects.filter(idAlumnoXHorario__alumno__id=alumno_id)
        
        # Serializar los datos y devolver la respuesta
        serializer = self.get_serializer(retiros, many=True)
        return Response(serializer.data)
    
