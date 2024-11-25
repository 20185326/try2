from rest_framework import serializers
from .models import Usuario, Alumno, Profesor, Administrador, TRol
from cursos.models import PeriodoAcademico
from matricula.models import AlumnoXHorario,InformacionMatricula

class UsuarioSerializer(serializers.ModelSerializer):
    tipo_usuario = serializers.SerializerMethodField()
    tipo_profesor = serializers.SerializerMethodField()
    estado = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = '__all__'

    def get_tipo_usuario(self, obj):
        # Verificar si el usuario es una instancia de Alumno o Profesor
        if hasattr(obj, 'alumno'):
            return 'alumno'
        elif hasattr(obj, 'profesor'):
            return 'profesor'
        return 'usuario'

    def get_tipo_profesor(self, obj):
        # Devolver el tipo si el usuario es un profesor
        if hasattr(obj, 'profesor'):
            return obj.profesor.tipo
        return None

    def get_estado(self, obj):
        # Obtener el estado global de la matrícula
        return InformacionMatricula.obtener_estado_actual()
    

class AlumnoSerializer(serializers.ModelSerializer):
    cursosPermitidos = 'cursos.serializer.CursoSSerializar(many=True, read_only=True)'
    class Meta:
        model = Alumno
        fields = '__all__'

class ProfesorSerializer(serializers.ModelSerializer):
    horarios= 'cursos.serializer.HorarioSSerializar(many=True, read_only=True)'
    class Meta:
        model = Profesor
        fields = '__all__'

class AdministradorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Administrador
        fields = '__all__'

class AlumnoSimpleSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Alumno
        fields = ['id', 'nombre', 'primerApellido','segundoApellido','correo','codigo']

class PeriodosAlumnoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PeriodoAcademico
        fields = ['id', 'periodo', 'fechaInicio', 'fechaFin', 'activo']

##Trayectoria Academica
class TrayectoriaAcademicaSerializer(serializers.ModelSerializer):
    # Campos de usuario y alumno
    nombre = serializers.CharField()
    primerApellido = serializers.CharField()
    segundoApellido = serializers.CharField()
    codigo = serializers.CharField()
    
    # Campo calculado: CrÃ©ditos Totales
    creditos_totales = serializers.SerializerMethodField()
    
    # Campo calculado: Asignaciones con Nota > 10.5
    asignaciones_con_nota_mayor_10_5 = serializers.SerializerMethodField()
    
    class Meta:
        model = Alumno
        fields = [
            'nombre', 'primerApellido', 'segundoApellido', 'codigo', 'factorDeDesempeno',
            'creditosPrimera','creditosSegunda','creditosTercera','puntajeTotalPorCompetencias','numeroSemestres',
            'turnoOrdenMatricula',
            'creditos_totales', 'asignaciones_con_nota_mayor_10_5'
        ]
    
    def get_creditos_totales(self, obj):
        return obj.creditosPrimera + obj.creditosSegunda + obj.creditosTercera
    
    def get_asignaciones_con_nota_mayor_10_5(self, obj):
        # Filtramos los AlumnoXHorario que tengan nota > 10.5
        return AlumnoXHorario.objects.filter(
            alumno=obj, promedioFinal__gt=10.5
        ).count()
