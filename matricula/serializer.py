from rest_framework import serializers
from .models import *
from calificacion.models import NotaNumerica
from usuarios.serializers import AlumnoSimpleSerializer
from usuarios.models import Profesor
from cursos.models import Curso

class AlumnoXHorarioSerializar(serializers.ModelSerializer):
    class Meta:
        model= AlumnoXHorario
        fields = '__all__'

class LineaInscripcionSerializar(serializers.ModelSerializer):
    horarios = 'cursos.serializer.HorarioSerializar()'
    class Meta:
        model= LineaInscripcion
        fields = '__all__'

class InscripcionSerializar(serializers.ModelSerializer):
    lineasDeInscripcion = LineaInscripcionSerializar(many=True, read_only=True) 
    class Meta:
        model= Inscripcion
        fields = '__all__'

##Vista profesor-Información del curso ------- James y Fernando##
class AlumnoXIdHorarioSerializar(serializers.ModelSerializer):
    alumno = AlumnoSimpleSerializer(read_only=True)
    class Meta:
        model= AlumnoXHorario
        fields = ['id', 'alumno', 'retirado']
        
##Vista Profesor-Notas de evaluación 
class AlumnoXIdHorarioNotasSerializar(serializers.ModelSerializer):
    alumno_codigo=serializers.CharField(source='usuario.codigo')
    alumno_nombre=serializers.CharField(source='usuario.nombre')
    
    notas= serializers.SerializerMethodField()
    
    class Meta:
        model = AlumnoXHorario
        fields = ['alumno_codigo', 'alumno_nombre','notas']
        
    def get_notas(self,obj):
        tipo_nota= self.context.get('tipoDeNota')
        indice_nota=self.context.get('indice')
        
        notas= obj.notasNumericas.filter(tipoDeNota=tipo_nota, indice=indice_nota)
        
##Vista de Cursos Matriculados/ Inscritos

    
## Serializer para retiro    
    
# Serializer para el modelo Usuario (heredado por Alumno)
class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alumno  # Alumno hereda de Usuario
        fields = ['id','codigo', 'nombre', 'primerApellido', 'segundoApellido']

# Serializer para el modelo Curso
class CursoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Curso
        fields = ['clave', 'nombre', 'creditos', 'nivel']

# Serializer para el modelo Horario
class HorarioSerializer(serializers.ModelSerializer):
    curso = CursoSerializer(source='idCurso')

    class Meta:
        model = Horario
        fields = ['id', 'curso', 'claveHorario']

# Serializer para el modelo AlumnoXHorario
class RetiroAlumnoXHorarioSerializer(serializers.ModelSerializer):
    alumno = UsuarioSerializer()
    horario = HorarioSerializer()

    class Meta:
        model = AlumnoXHorario
        fields = ['id', 'alumno', 'horario', 'vez']

# Serializer para el modelo RetiroAlumno
class RetiroAlumnoSerializer(serializers.ModelSerializer):
    idAlumnoXHorario = RetiroAlumnoXHorarioSerializer()
    class Meta:
        model = AlumnoRetiro
        fields = ['id', 'idAlumnoXHorario', 'justificacion', 'estadoSolicitud', 'estadoRetiro']


##Estado del campus
class InformacionMatriculaSerializer(serializers.ModelSerializer):
    class Meta:
        model = InformacionMatricula
        fields= '__all__'        