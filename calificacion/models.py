from django.db import models

# Enum para los tipos de nota
class TNota(models.TextChoices):
    PRACTICA = 'Practica', 'Practica'
    PARCIAL = 'Parcial', 'Parcial'
    FINAL = 'Final', 'Final'
    UNICA = 'Unica', 'Unica'

# Modelo para Competencia
class Competencia(models.Model):
    nombre = models.CharField(max_length=255,blank=True)
    clave = models.CharField(max_length=50)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.clave
    
# Modelo para SubCompetencia
class SubCompetencia(models.Model):
    idCompetencia = models.ForeignKey(Competencia, on_delete= models.CASCADE,related_name='subcompetencias')
    nombre = models.CharField(max_length=255, blank=True)
    clave = models.CharField(max_length=50)
    descripcion = models.TextField(blank=True)
    nivelInicial = models.CharField(max_length=255,blank=True)
    nivelEnProceso = models.CharField(max_length=255,blank=True)
    nivelSatisfactorio = models.CharField(max_length=255,blank=True)
    nivelSobresaliente = models.CharField(max_length=255,blank=True)
    activo = models.BooleanField(default=True)
    def __str__(self):
        return self.clave


# Modelo para CompetenciaXHorario
class CompetenciaXHorario(models.Model):
    idCompetencia = models.ForeignKey(Competencia, on_delete= models.CASCADE)
    idHorario = models.ForeignKey('cursos.Horario', on_delete= models.CASCADE)
    cantidadEvaluaciones = models.IntegerField()
    activo = models.BooleanField(default=True)
    def __str__(self):
        return f"Competencia {self.idCompetencia} - Horario {self.idHorario}"
    
# Modelo para NotaDisponible
class NotaDisponible(models.Model):
    idHorario = models.ForeignKey('cursos.Horario',on_delete=models.CASCADE,related_name='notasDisponibles')
    indice = models.IntegerField()
    tipoNota = models.CharField(max_length=20, choices=TNota.choices)
    activo = models.BooleanField(default=True)
    def __str__(self):
        return f"Nota Disponible {self.tipoNota} - Índice {self.indice}"


# Modelo para NotaNumerica
class NotaNumerica(models.Model):
    idAlumnoXHorario = models.ForeignKey('matricula.AlumnoXHorario',on_delete=models.CASCADE,related_name='notasNumericas')
    tipoDeNota = models.CharField(max_length=20, choices=TNota.choices)
    indice = models.IntegerField()
    valor = models.FloatField(default=-1)
    activo = models.BooleanField(default=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['idAlumnoXHorario', 'tipoDeNota', 'indice'],
                name='unique_nota_constraint'
            )
        ]
    
    def __str__(self):
        return f"Nota {self.valor} - Tipo {self.tipoDeNota}"

# Modelo para NotaXCompetencia
class NotaXCompetencia(models.Model):
    idAlumnoXHorario = models.ForeignKey('matricula.AlumnoXHorario',on_delete=models.CASCADE,related_name='notasXCompetencia')
    idCompetencia = models.ForeignKey(Competencia, on_delete=models.CASCADE,null=True)
    notaFinal = models.CharField(max_length=2,null=True)
    retroalimentacionFinal = models.TextField(null=True)
    activo = models.BooleanField(default=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['idAlumnoXHorario', 'idCompetencia'],
                name='unique_nota_x_competencia_constraint'
            )
        ]
    
    def __str__(self):
        return f"Nota por Competencia {self.idAlumnoXHorario} + {self.idCompetencia}"


# Modelo para NotaAlfabetica
class NotaAlfabetica(models.Model):
    idNotaXCompetencia = models.ForeignKey(NotaXCompetencia,on_delete=models.CASCADE,related_name='notasAlfabeticas')
    valor = models.CharField(max_length=2,null=True)
    indice = models.IntegerField()
    retroalimentacion = models.TextField()
    activo = models.BooleanField(default=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['idNotaXCompetencia', 'indice'],
                name='unique_nota_alfabetica_constraint'
            )
        ]
    def __str__(self):
        return f"NotaAlfabetica {self.valor} + indice:{self.indice} + idNxC:{self.idNotaXCompetencia.id}"

# Modelo para NotaAlfabeticaSub
class NotaAlfabeticaSub(models.Model):
    idNotaAlfabetica = models.ForeignKey(NotaAlfabetica, on_delete=models.CASCADE,related_name='notasAlfabeticasSub')
    idSubCompetencia = models.ForeignKey(SubCompetencia,on_delete=models.CASCADE,related_name='NotaAlfabeticaSub')
    valor = models.CharField(max_length=2,null=True)
    activo = models.BooleanField(default=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['idNotaAlfabetica', 'idSubCompetencia'],
                name='unique_nota_alfabetica_sub_constraint'
            )
        ]
    def __str__(self):
        return f"Sub Competencia {self.idSubCompetencia} - Valor {self.valor}"
