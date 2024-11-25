from django.db.models.signals import post_save
from django.dispatch import receiver
from cursos.models import PeriodoAcademico,Horario
from usuarios.models import Alumno
from matricula.models import Inscripcion,InformacionMatricula,TEstadoMatricula,LineaInscripcion,AlumnoXHorario
from django.db import transaction


@receiver(post_save, sender=PeriodoAcademico)
def crear_inscripciones_para_periodo(sender, instance, created, **kwargs):
    """
    Signal que crea inscripciones para todos los alumnos habilitados
    cada vez que se crea un nuevo periodo académico.
    """
    if created:  # Solo cuando el periodo es creado, no al actualizarlo
        # Obtener todos los alumnos habilitados
        alumnos_habilitados = Alumno.objects.filter(habilitado=True)

        # Crear inscripciones para cada alumno habilitado
        inscripciones = []
        for alumno in alumnos_habilitados:
            inscripciones.append(Inscripcion(
                periodo=instance,
                alumno=alumno,
                totalCreditos=0,
                activo=True,
                extemporanea=False
            ))

        # Usar bulk_create para optimizar la creación de inscripciones
        Inscripcion.objects.bulk_create(inscripciones)
    
    print(f"Nuevas inscripciones creadas!!")
    
    
    
@receiver(post_save, sender=InformacionMatricula)
def asginar_alummno_x_horario(sender, instance, **kwargs):
    # Verificar si el estado ha cambiado a FINDECICLO
    if instance.estadoMatricula == TEstadoMatricula.CICLOLECTIVO:
        # Obtener el periodo académico actual
        actual = PeriodoAcademico.objects.filter(actual=True).first()
        if not actual:
            print("No se encontró un periodo académico actual activo.")
            return

        # Obtener las inscripciones activas del periodo actual
        inscripciones = Inscripcion.objects.filter(periodo=actual)
        Horario.objects.all().update(numMatriculados=0,numAprobados=0,numDesaprobados=0)
        
        # Procesar cada inscripción
        with transaction.atomic():
            for inscripcion in inscripciones:
                lineas = LineaInscripcion.objects.filter(
                    inscripcion=inscripcion,
                    seleccionado=True,
                    activo=True
                )
                
                for linea in lineas:
                    # Verificar cuántas veces el alumno ya llevó un horario del mismo curso
                    curso = linea.horario.idCurso
                    num_veces = AlumnoXHorario.objects.filter(
                        alumno=inscripcion.alumno,
                        horario__idCurso=curso,
                        retirado=False
                    ).count()
                    
                    # Crear la nueva entrada de AlumnoXHorario
                    AlumnoXHorario.objects.create(
                        alumno=inscripcion.alumno,
                        horario=linea.horario,
                        periodo=actual,
                        vez=num_veces + 1,  # Incrementamos en 1
                        promedioPcs=0.0,
                        promedioFinal=0.0,
                        retirado=False
                    )
                    
                    # Incrementar el número de matriculados en el horario
                    linea.horario.numMatriculados += 1
                    linea.horario.save()
            
            print("Los alumnos se han asginado a sus horarios correctamente")