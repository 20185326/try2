from django.db import models
from django.utils import timezone

# Enumeración para el tipo de rol del profesor
class TRol(models.TextChoices):
    REGULAR = 'Regular', 'Regular'
    DIRECTOR_CARRERA = 'Director de Carrera', 'Director de Carrera'
    GESTOR = 'Gestor de Carrera', 'Gestor de Carrera'
    
def get_current_date():
    return timezone.now().date()

# Clase Usuario (heredada por Alumno, Profesor, Administrador)
class Usuario(models.Model):
    nombre = models.CharField(max_length=100)
    segundoApellido = models.CharField(max_length=100)
    primerApellido = models.CharField(max_length=100)
    correo = models.EmailField(unique=True)
    codigo = models.CharField(max_length=28)
    fechaRegistro = models.DateField(default=get_current_date)
    telefono = models.CharField(max_length=15)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

# Clase Alumno (hereda de Usuario)
class Alumno(Usuario):
    factorDeDesempeno = models.FloatField()
    creditosPrimera = models.IntegerField()
    creditosSegunda = models.IntegerField()
    creditosTercera = models.IntegerField()
    puntajeTotalPorCompetencias = models.CharField(max_length=1)
    numeroSemestres = models.IntegerField()
    turnoOrdenMatricula = models.IntegerField()
    cursosPermitidos = models.ManyToManyField(
        'cursos.Curso',
        through='AlumnoXCursosPermitidos',  # Tabla intermedia personalizada
        related_name='alumnos_permitidos',
        blank=True
    )
    anioIngreso = models.DateField()
    habilitado= models.BooleanField(default=True)

# Clase Profesor (hereda de Usuario)
class Profesor(Usuario):
    tipo = models.CharField(max_length=30, choices=TRol.choices)

# Clase Administrador (hereda de Usuario)
class Administrador(Usuario):
    actual = models.BooleanField(default=False)

## AHHHH
class AlumnoXCursosPermitidos(models.Model):
    #idAlumnoXHorario = models.AutoField(primary_key=True)
    alumno = models.ForeignKey(Alumno,on_delete=models.CASCADE,related_name='alumnoXcursosperm')
    curso = models.ForeignKey('cursos.Curso',on_delete=models.CASCADE,related_name='alumnoXcursosperm')
    activo = models.BooleanField(default=True)
    
    
    class Meta:
        unique_together = ('alumno','curso') ##Evita duplicado