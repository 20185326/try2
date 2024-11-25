from django.db import models
from usuarios.models import Alumno, Usuario
from cursos.models import Horario, PeriodoAcademico

# Modelo para AlumnoXHorario
class AlumnoXHorario(models.Model):
    #idAlumnoXHorario = models.AutoField(primary_key=True)
    periodo = models.ForeignKey('cursos.PeriodoAcademico',on_delete=models.CASCADE,related_name='alumnoXhorarios')
    alumno = models.ForeignKey('usuarios.Alumno',on_delete=models.CASCADE,related_name='alumnoXhorarios')
    horario = models.ForeignKey('cursos.Horario',on_delete=models.CASCADE,related_name='alumnoXhorarios')
    vez = models.IntegerField()
    promedioPcs = models.FloatField(default=-1)
    promedioFinal = models.FloatField(default=-1)
    retirado = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Alumno {self.alumno} - Horario {self.horario}"
    
    class Meta:
        unique_together = ('alumno','horario','periodo') ##Evita duplicados
        
        
class VistaAlumnoXHorario(models.Model):
    id_alumnoxhorario=models.BigIntegerField()
    vez=models.IntegerField()
    promedioPcs=models.FloatField()
    promedioFinal=models.FloatField()
    retirado=models.BooleanField()
    alumnoxhorario_activo=models.BooleanField()
    id_alumno=models.BigIntegerField()
    alumno_nombre=models.CharField(max_length=100)
    alumno_primerApellido=models.CharField(max_length=100)
    alumno_segundoApellido=models.CharField(max_length=100)
    codigo_alumno=models.CharField(max_length=28)
    id_horario=models.BigIntegerField()
    claveHorario=models.CharField(max_length=5)
    numVacantes=models.IntegerField()
    numMatriculados=models.IntegerField()
    numAprobados=models.IntegerField()
    numDesaprobados=models.IntegerField()
    id_curso=models.BigIntegerField()
    curso_clave=models.CharField(max_length=50)
    curso_nombre=models.CharField(max_length=100)
    curso_creditos=models.FloatField()
    id_periodo=models.BigIntegerField()
    periodo_academico=models.CharField(max_length=50)
    fechaInicio=models.DateField()
    fechaFin=models.DateField()
    id_inscripcion=models.BigIntegerField()
    inscripcion_creditos=models.FloatField()
    inscripcion_activa=models.BooleanField()
    class Meta:
        managed= False
        db_table='vista_alumnoxhorario_completa'
    
# Modelo para Inscripcion
class Inscripcion(models.Model):
    #idInscripcion = models.AutoField(primary_key=True)
    periodo = models.ForeignKey('cursos.PeriodoAcademico',null=True, on_delete=models.CASCADE,related_name='inscripciones')
    alumno = models.ForeignKey('usuarios.Alumno',on_delete=models.CASCADE,related_name='inscripcion')
    #lineasDeInscripcion = models.ManyToManyField(LineaInscripcion)
    totalCreditos = models.FloatField(default=0)
    activo = models.BooleanField(default=True)
    

    def __str__(self):
        return f"Inscripción {self.idInscripcion} - Alumno {self.idAlumno}"

# Modelo para LineaInscripcion
class LineaInscripcion(models.Model):
    #idLineaInscripcion = models.AutoField(primary_key=True)
    horario = models.ForeignKey('cursos.Horario',on_delete=models.CASCADE,related_name='lineasDeInscripcion')
    inscripcion = models.ForeignKey(Inscripcion,on_delete=models.CASCADE,related_name='lineasDeInscripcion')
    posicionRelativa = models.IntegerField()
    seleccionado = models.BooleanField(default=False)
    permitido = models.BooleanField(default=True)
    extemporanea = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    def matricular(self):
        # Lógica de matriculación
        pass

    def __str__(self):
        return f"Inscripcion {self.idInscripcion} - Horario {self.idHorario}"
    
# Modelo para AlumnoRetiro

class AlumnoRetiro(models.Model):
    idAlumnoXHorario= models.OneToOneField(AlumnoXHorario, on_delete=models.CASCADE,related_name='retiroHorarios')
    justificacion= models.TextField(null=True)
    #documento=models.FileField(null=True),
    estadoSolicitud= models.BooleanField(default=True)
    estadoRetiro= models.BooleanField(default=False)
    
class TEstadoMatricula(models.TextChoices):
    PREMATRICULA = 'Prematricula', 'Prematricula'
    MATRICULA = 'Matricula', 'Matricula'
    PUBLICACIONMATRICULA = 'Publicacion Matricula', 'Publicacion Matricula'
    MATRICULAEXTEMPORANEA= 'Matricula Extemporanea', 'Matricula Extemporanea'
    PUBLICACIONMATEXTEMPORANEA = 'Publicación Mat. Ext', 'Publicación Mat. Ext'
    CICLOLECTIVO = 'Ciclo Lectivo', 'Ciclo Lectivo'
    FINDECICLO = 'Fin de Ciclo', 'Fin de Ciclo'

class InformacionMatricula(models.Model):
    publicacionDeCursos=models.DateField(default="2000-01-01")
    inicioPreMatricula=models.DateField(default="2000-01-01")
    cierrePreMatricula=models.DateField(default="2000-01-01")
    publicacionCursosMatInicio=models.DateField(default="2000-01-01")
    publicacionCursosMatFin=models.DateField(default="2000-01-01")
    inicioMatExtemporanea=models.DateField(default="2000-01-01")
    finMatExtemporanea=models.DateField(default="2000-01-01")
    publicacionMatExtemporanea=models.DateField(default="2000-01-01")
    fin=models.DateField(default="2000-01-01")
    estadoMatricula=models.CharField(max_length=30, choices=TEstadoMatricula.choices,default=TEstadoMatricula.CICLOLECTIVO)

    @classmethod
    def obtener_estado_actual(cls):
        # Obtener el último registro de InformacionMatricula y retornar el estado
        ultima_matricula = cls.objects.last()
        if ultima_matricula:
            return ultima_matricula.estadoMatricula
        return TEstadoMatricula.CICLOLECTIVO