from rest_framework import serializers
from .models import *
from calificacion.serializer import *
from matricula.models import AlumnoRetiro

class FormulaSerializar(serializers.ModelSerializer):
    class Meta:
        model= Formula
        fields = '__all__'

class CursoSSerializar(serializers.ModelSerializer):
    class Meta:
        model= Curso
        fields = '__all__'


class HorarioSSerializar(serializers.ModelSerializer):
    class Meta:
        model = Horario
        fields = '__all__'

class HorarioSerializar(serializers.ModelSerializer):
    idprofesor = 'usuarios.serializers.ProfesorSerializer()'
    class Meta:
        model = Horario
        fields = '__all__'
        
class CursoSerializar(serializers.ModelSerializer):
    class Meta:
        model= Curso
        fields = '__all__'

class PeriodoSerializer(serializers.Serializer):
    periodo = serializers.CharField()

class PeriodoAcademicoSerializar(serializers.ModelSerializer):
    class Meta:
        model = PeriodoAcademico
        fields = '__all__'  
        
class TNivelSerializar(serializers.ModelSerializer):
    class Meta:
        model = TNivel
        fields = '__all__' 
        

class HorarioPSerializer(serializers.ModelSerializer):
    numero_inscritos = serializers.SerializerMethodField()

    class Meta:
        model = Horario
        fields = '__all__' 
        
    def get_numero_inscritos(self, obj):
        return obj.lineasDeInscripcion.count()

class CursoPSerializer(serializers.ModelSerializer):
    horarios = serializers.SerializerMethodField()
    
    class Meta:
        model = Curso
        fields = '__all__' 
    
    def get_horarios(self, obj):
        # Obtener el id del profesor de la request
        profesor_id = self.context['profesor_id']
        
        # Filtrar los horarios relacionados con el profesor
        horarios = obj.horarios.filter(idprofesor_id=profesor_id, activo=1)
        
        # Serializar los horarios
        return HorarioPSerializer(horarios, many=True).data
    
class CursoAlumnoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Curso
        fields = ['clave', 'nombre', 'creditos','numHoras']  # Asegúrate de que estos campos existan en tu modelo

# Serializador para el estado de retiro de AlumnoRetiro
class RetiroAlumnoxHorarioVerSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlumnoRetiro
        fields = ['estadoSolicitud', 'estadoRetiro']

# Serializador para AlumnoXHorario
class AlumnoXHorarioAlumnoSerializer(serializers.ModelSerializer):
    curso = CursoAlumnoSerializer(source='horario.idCurso')  # Suponiendo que 'horario' es la relación en AlumnoXHorario
    profesor_nombre = serializers.CharField(source='horario.idprofesor.nombre')  # Suponiendo que idprofesor tiene una relación con un modelo Profesor
    apellido_profesorP = serializers.CharField(source='horario.idprofesor.primerApellido')
    apellido_profesorM = serializers.CharField(source='horario.idprofesor.segundoApellido')
    numHorario = serializers.CharField(source='horario.claveHorario')
    
    # Relación con AlumnoRetiro para obtener el estado de retiro
    retiroHorarios = RetiroAlumnoxHorarioVerSerializer(read_only=True)

    class Meta:
        model = AlumnoXHorario
        fields = [
            'id', 'curso', 'numHorario', 'vez', 
            'profesor_nombre', 'apellido_profesorP', 'apellido_profesorM', 
            'retiroHorarios'
        ]

class CompetenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Competencia
        fields = ['id', 'clave', 'nombre', 'descripcion']

class CursoCompetenciaSerializer(serializers.ModelSerializer):
    competencias = CompetenciaSerializer(many=True)

    class Meta:
        model = Curso
        fields = ['id', 'clave', 'nombre', 'competencias']
        
##Mostrar todo
class ProfesorGestorSerialzer(serializers.ModelSerializer):
    class Meta:
        model=Profesor
        fields=['nombre','primerApellido']

class HorarioGestorSerializer(serializers.ModelSerializer):
    profesor = ProfesorGestorSerialzer(source='idprofesor', read_only=True)

    class Meta:
        model = Horario
        fields = [
            'id', 
            'claveHorario', 
            'numVacantes', 
            'numMatriculados',
            'profesor'  # Este es el campo del profesor serializado
        ]
        
class CursoConHorariosGestorSerializer(serializers.ModelSerializer):
    horarios = HorarioGestorSerializer(many=True)

    class Meta:
        model = Curso
        fields = [
            'id',
            'clave',
            'nombre',
            'creditos',
            'numHoras',
            'horarios',
        ]