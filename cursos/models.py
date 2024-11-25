# Create your models here.
from django.db import models

from usuarios.models import Profesor,Alumno
from calificacion.models import Competencia
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class Formula(models.Model):
    pesoParciales = models.FloatField()
    pesoFinales = models.FloatField()
    pesoPracticas = models.FloatField()
    numPracticas = models.IntegerField(default=0)
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return f"PesoParcial: {self.pesoParciales} - PesoFinal: {self.pesoFinales}"

class TNivel(models.TextChoices):
    UNO = '1', 'Uno'
    DOS = '2', 'Dos'
    TRES = '3', 'Tres'
    CUATRO = '4', 'Cuatro'
    CINCO = '5', 'Cinco'
    SEIS = '6', 'Seis'
    SIETE = '7', 'Siete'
    OCHO = '8', 'Ocho'
    NUEVE = '9', 'Nueve'
    DIEZ = '10', 'Diez'
    ELECTIVO = 'E', 'Electivo'
    
class PeriodoAcademico(models.Model):
    periodo = models.CharField(max_length=50)
    fechaInicio = models.DateField()
    fechaFin = models.DateField()
    actual = models.BooleanField(default=False)  # Campo para identificar el ciclo actual
    activo = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        # Si este periodo es el actual, asegurarse de que ningún otro periodo esté marcado como actual
        if self.actual:
            # Desactivar el campo `actual` en todos los demás periodos
            PeriodoAcademico.objects.filter(actual=True).update(actual=False)
        
        # Guardar el periodo académico
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.periodo}'
    
    
class RequisitoBase(models.Model):
    # Campos comunes para los tipos de requisito
    activo= models.BooleanField(default=True)  
    

class Curso(models.Model):
    formula = models.ForeignKey(Formula, blank=True, on_delete=models.CASCADE, related_name='cursos')

    competencias = models.ManyToManyField(Competencia, blank=True, related_name='cursos')
    clave = models.CharField(max_length=50)
    nombre = models.CharField(max_length=100)
    creditos = models.FloatField()
    
    nivel = models.CharField(max_length=2, choices=TNivel.choices)
    activo = models.BooleanField(default=True)
    descripcion = models.TextField(blank=True, null=True)
    numHoras = models.IntegerField(blank=True)
    obligatorio = models.BooleanField(default=True)
    silabo = models.TextField(blank=True, null=True)
    requisitos = models.ForeignKey(RequisitoBase,blank=True,null=True, on_delete=models.CASCADE,related_name='cursos')
    
    def __str__(self):
        return self.nombre
    
    
class RequisitoCursos(RequisitoBase):
    cursos = models.ManyToManyField(Curso, related_name='requisito_para_cursos')

    def __str__(self):
        return f"Requisito: {self.nombre} - Cursos: {', '.join([curso.clave for curso in self.cursos.all()])}"
    
class RequisitoCreditos(RequisitoBase):
    total_creditos = models.FloatField()

    def __str__(self):
        return f"Requisito: {self.nombre} - {self.total_creditos} créditos"
    


class Horario(models.Model):
    idCurso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='horarios')
    idprofesor = models.ForeignKey(Profesor,null=True, on_delete=models.CASCADE, related_name='horarios')  # Podríamos hacer una FK a Profesor si existe en tu sistema
    alumnos = models.ManyToManyField(Alumno,through='matricula.AlumnoXHorario',blank=True, related_name='horarios')
    claveHorario = models.CharField(max_length=5,default="H000")
    numVacantes = models.IntegerField()
    numMatriculados = models.IntegerField()
    numAprobados = models.IntegerField()
    numDesaprobados = models.IntegerField()
    #tipoDeNotas = models.ManyToManyField('calificacion.NotaDisponible', blank=True)
    activo = models.BooleanField(default=True)
    
