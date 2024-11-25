from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Alumno
from matricula.models import AlumnoXHorario,InformacionMatricula,TEstadoMatricula
from cursos.models import Curso, Horario, TNivel,PeriodoAcademico  # Asumimos que tienes estos modelos
import random
from django.db.models import Max,Sum


#Asginar horarios automaticamente
@receiver(post_save, sender=Alumno)
def asignar_cursos_y_horarios(sender, instance, created, **kwargs):
    if created:  # Solo ejecutamos cuando el alumno es creado
        print(f"Alumno creado: {instance.nombre}")

        # Obtener todos los cursos disponibles en el nivel y periodo especificado
        cursos_disponibles = Curso.objects.filter(nivel=TNivel.UNO)
        periodo_a_asignar= PeriodoAcademico.objects.filter(periodo='Base')
    
        for curso in cursos_disponibles:
            horarios_disponibles = list(curso.horarios.all())  # Convertir a lista para poder hacer shuffle
            random.shuffle(horarios_disponibles)  # Orden aleatorio de horarios

            horario_asignado = None  # Variable para controlar si se asignó un horario exitosamente

            # Iterar sobre los horarios hasta encontrar uno con espacio
            for horario in horarios_disponibles:
                if horario.numMatriculados < horario.numVacantes:  # Hay espacio en este horario
                    # Crear la relación AlumnoXHorario para este horario
                    AlumnoXHorario.objects.create(
                        alumno=instance,
                        horario=horario,
                        periodo=periodo_a_asignar,
                        vez=1,  # Primera vez inscripto
                        promedioPcs=0.0,
                        promedioFinal=0.0,
                        retirado=False
                    )

                    # Incrementar el número de matriculados en el horario
                    horario.numMatriculados += 1
                    horario.save()

                    # Marcar el horario como asignado y salir del loop
                    horario_asignado = horario
                    break
            
            # Si después de recorrer todos los horarios no se asignó ninguno, mostrar mensaje de error
            if not horario_asignado:
                print(f"No se pudo inscribir al alumno {instance.nombre} en el curso {curso.nombre}: todos los horarios están ocupados.")
                # Opcionalmente, puedes lanzar una excepción o manejar el caso según la lógica de negocio


## Actualizar factor de desempeño
def calcular_factor_desempeno(alumno):
    # Inicializamos variables para acumular los créditos y el total ponderado de notas
    total_creditos = 0
    suma_ponderada_notas = 0

    # Obtenemos todos los periodos de los cursos donde el alumno tiene notas
    periodos = AlumnoXHorario.objects.filter(
        alumno=alumno,
        promedioFinal__gte=10.5  # Considerar solo las notas aprobadas
    ).values_list('periodo', flat=True).distinct()
    
    for periodo in periodos:
        # Obtener los AlumnoXHorario del alumno en el periodo actual
        alumnoxhorarios = AlumnoXHorario.objects.filter(
            alumno=alumno,
            periodo=periodo,
            retirado=False  # Notas aprobadas
        )

        # Calcular el total de créditos y la suma ponderada de notas del periodo
        total_creditos_periodo = alumnoxhorarios.aggregate(
            total_creditos=Sum('horario__idCurso__creditos')
        )['total_creditos'] or 0

        suma_ponderada_periodo = alumnoxhorarios.aggregate(
            suma_ponderada=Sum('promedioFinal')  # Supone que promedioFinal ya es ponderado
        )['suma_ponderada'] or 0

        # Acumular los créditos y la suma ponderada
        total_creditos += total_creditos_periodo
        suma_ponderada_notas += suma_ponderada_periodo

        # Detener si hemos alcanzado los 40 créditos aprobados
        if total_creditos >= 40:
            break

    # Calcular el factor de desempeño final como promedio ponderado
    if total_creditos > 0:
        return round(suma_ponderada_notas / total_creditos,2)
    return 0  # Retorna 0 si no tiene créditos aprobados


@receiver(post_save, sender=InformacionMatricula)
def actualizar_factores_y_turnos(sender, instance, **kwargs):
    # Verificar si el estado ha cambiado a FINDECICLO
    if instance.estadoMatricula == TEstadoMatricula.FINDECICLO:
        # Obtener todos los alumnos activos
        alumnos = Alumno.objects.filter(activo=True)
        
        # Actualizar el factor de desempeño para cada alumno
        for alumno in alumnos:
            factor_desempeno = calcular_factor_desempeno(alumno)
            alumno.factorDeDesempeno = factor_desempeno
            alumno.save()
        
        # Ordenar los alumnos por `factorDeDesempeno` y `codigo`
        alumnos_ordenados = Alumno.objects.filter(activo=True,habilitado=True).order_by(
            '-factorDeDesempeno', 'codigo'
        )
        
        # Asignar el turno de matrícula en función del orden
        for turno, alumno in enumerate(alumnos_ordenados, start=1):
            alumno.turnoOrdenMatricula = turno
            alumno.save()
            
        print(f"Los datos de los alumnos han sido actualizados")
        
    