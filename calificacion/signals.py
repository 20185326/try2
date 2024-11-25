from django.db.models.signals import post_save
from django.dispatch import receiver
from cursos.models import Horario, Curso
from .models import CompetenciaXHorario

@receiver(post_save, sender=Horario)
def crear_competencias_para_horario(sender, instance, created, **kwargs):
    if created:  # Solo ejecutar la lógica cuando el Horario se cree por primera vez
        
        print(f"Horario creado: {instance.claveHorario}")
        curso = instance.idCurso  # Obtener el curso asociado al horario

        # Iterar sobre las competencias del curso
        competencias = curso.competencias.all()  # Asumiendo que hay una relación Competencia -> Curso

        for competencia in competencias:
            # Crear una entrada en CompetenciaXHorario para cada competencia
            CompetenciaXHorario.objects.create(
                idCompetencia=competencia,
                idHorario=instance,
                cantidadEvaluaciones=0  # Inicializar en 0 o como prefieras
            )