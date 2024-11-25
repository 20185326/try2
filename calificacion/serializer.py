from rest_framework import serializers
from .models import *
from usuarios.models import Alumno, Usuario
from matricula.models import AlumnoXHorario
from cursos.models import Horario
from cursos.models import Formula
from cursos.models import Curso

class SubCompetenciaSerializar(serializers.ModelSerializer):
    class Meta:
        model= SubCompetencia
        fields = '__all__'

class CompetenciaSerializar(serializers.ModelSerializer):
    class Meta:
        model= Competencia
        fields = '__all__'
        
class CompetenciaXHorarioSerializar(serializers.ModelSerializer):
    class Meta:
        model = CompetenciaXHorario
        fields = '__all__'
        
class NotaDisponibleSerializar(serializers.ModelSerializer):
    class Meta:
        model = NotaDisponible
        fields = '__all__'
        
class NotaAlfabeticaSubSerializar(serializers.ModelSerializer):
    class Meta:
        model = NotaAlfabeticaSub
        fields = '__all__'
        
class NotaAlfabeticaSerializar(serializers.ModelSerializer):
    notasAlfabeticasSub = NotaAlfabeticaSubSerializar(many=True)
    class Meta:
        model = NotaAlfabetica
        fields = '__all__'
        
class NotaXCompetenciaSerializar(serializers.ModelSerializer):
    notasAlfabeticas = NotaAlfabeticaSerializar(many=True)
    class Meta:
        model = NotaXCompetencia
        fields = '__all__' 
        

##Vista profesor-Información del curso ------- James y Fernando##
class EvaluacionSerializer(serializers.Serializer):
    tipo = serializers.CharField(max_length=100)
    indice = serializers.IntegerField()
    
    
 ##Vista de insercion de notas ------- Carlos y Renato##   
 
 #Nota generica##
 
class AlumnoNotaSerializer(serializers.Serializer):
    alumno_x_horario = serializers.IntegerField()  # ID de AlumnoXHorario
    valor = serializers.FloatField()

class GuardarNotasSerializer(serializers.Serializer):
    tipoDeNota = serializers.CharField(max_length=20)
    indice = serializers.IntegerField()
    horario = serializers.IntegerField()  # ID del horario
    alumnos = AlumnoNotaSerializer(many=True)
    
    def validate_tipoDeNota(self, value):
        # Validar que el tipo de nota sea uno de los valores permitidos en el Enum TNota
        if value not in TNota.values:
            raise serializers.ValidationError(f"Tipo de nota no válido: {value}. Debe ser 'Practica', 'Parcial' o 'Final'.")
        return value

    def create(self, validated_data):
        tipoDeNota = validated_data['tipoDeNota']
        indice = validated_data['indice']
        horario_id = validated_data['horario']
        alumnos_data = validated_data['alumnos']

        # Verificar si existe el horario
        try:
            horario = Horario.objects.get(id=horario_id)
        except Horario.DoesNotExist:
            raise serializers.ValidationError(f"Horario con id {horario_id} no existe.")

        # Procesar las notas de cada alumno
        for alumno_data in alumnos_data:
            alumno_x_horario_id = alumno_data['alumno_x_horario']
            valor = alumno_data['valor']

            # Verificar si existe el AlumnoXHorario
            try:
                alumno_x_horario = AlumnoXHorario.objects.get(id=alumno_x_horario_id)
            except AlumnoXHorario.DoesNotExist:
                raise serializers.ValidationError(f"AlumnoXHorario con id {alumno_x_horario_id} no existe.")

            # Crear la nota numérica para el AlumnoXHorario
            NotaNumerica.objects.create(
                idAlumnoXHorario=alumno_x_horario,
                tipoDeNota=tipoDeNota,
                indice=indice,
                valor=valor
            )

        return validated_data

##Mostrar notas de alumnos
class AlumnoDetalleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alumno
        fields = ['codigo', 'nombre', 'primerApellido']
        
class NotaNumericaSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotaNumerica
        fields = ['valor']

class VisualizarNotasSerializer(serializers.ModelSerializer):
    idAlumnoXHorario=serializers.IntegerField(source='id')
    alumno_codigo = serializers.CharField(source='alumno.codigo')  # Campo código del alumno
    alumno_nombre = serializers.CharField(source='alumno.nombre')  # Campo nombre del alumno
    alumno_primer_apellido= serializers.CharField(source='alumno.primerApellido')
    alumno_segundo_apellido =serializers.CharField(source='alumno.segundoApellido')
    notas = serializers.SerializerMethodField()
    class Meta:
        model = AlumnoXHorario
        fields = ['idAlumnoXHorario','alumno_codigo', 'alumno_nombre','alumno_primer_apellido',
                  'alumno_segundo_apellido', 'retirado','notas']

    def get_notas(self, obj):
        # Obtener el tipo de nota y el índice desde el contexto
        tipo_nota = self.context.get('tipoDeNota')
        indice_nota = self.context.get('indice')

        # Filtrar las notas por tipoDeNota e índice
        notas = obj.notasNumericas.filter(tipoDeNota=tipo_nota, indice=indice_nota)
        
        if not notas.exists():
            return [{'valor': -1}]
        
        return NotaNumericaSerializer(notas, many=True).data
    
############################    

class FormulaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Formula
        fields = ['pesoParciales', 'pesoFinales', 'pesoPracticas']


class NotasEvaluacionesSerializer(serializers.Serializer):
    tipo = serializers.CharField()
    indice = serializers.IntegerField()
    valor = serializers.FloatField()


class CursoEvaluacionesSerializer(serializers.Serializer):
    curso_nombre = serializers.CharField()
    curso_clave = serializers.CharField()
    formula = FormulaSerializer()
    evaluaciones = NotasEvaluacionesSerializer(many=True)
    promedioPcs = serializers.FloatField(allow_null=True)
    promedioFinal = serializers.FloatField(allow_null=True)


class AlumnoCursoEvaluacionesSerializer(serializers.Serializer):
    cursos = CursoEvaluacionesSerializer(many=True)

#Serializers para mostrar notas de competencias y sub competencias
class SubCompetenciaSerializer(serializers.ModelSerializer):

    class Meta:
        model = SubCompetencia  # Asumiendo que SubCompetencia es el modelo de las subcompetencias
        fields = [
            'id', 'nombre', 'clave', 'nivelInicial', 
            'nivelEnProceso', 'nivelSatisfactorio', 
            'nivelSobresaliente'
        ]
class SubCompetenciaNotaSerializer(serializers.ModelSerializer):
    # Este serializer incluirá la información de las subcompetencias
    subcompetencia_info = SubCompetenciaSerializer(source='idSubCompetencia') 
    class Meta:
        model = NotaAlfabeticaSub
        fields = [
            'idSubCompetencia', 'valor','subcompetencia_info'
        ]


class NotaAlfabeticaSerializer(serializers.ModelSerializer):
    # Usamos SubCompetenciaNotaSerializer para obtener información detallada de las subcompetencias
    subcompetencias = SubCompetenciaNotaSerializer(source='notasAlfabeticasSub', many=True)

    class Meta:
        model = NotaAlfabetica
        fields = ['valor', 'indice', 'retroalimentacion', 'subcompetencias']


class CompetenciaSerializer(serializers.ModelSerializer):
    # Información de la competencia
    nombre = serializers.CharField(source='idCompetencia.nombre')
    descripcion = serializers.CharField(source='idCompetencia.descripcion')
    clave = serializers.CharField(source='idCompetencia.clave')
    notasAlfabeticas = NotaAlfabeticaSerializer(many=True)

    class Meta:
        model = NotaXCompetencia
        fields = [
            'idCompetencia', 'nombre', 'descripcion', 'clave', 
            'notaFinal', 'retroalimentacionFinal', 'notasAlfabeticas'
        ]


class CursoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Curso
        fields = ['clave', 'nombre', 'creditos']


class CursoConNotasCompetenciasSerializer(serializers.ModelSerializer):
    curso = CursoSerializer(source='horario.idCurso')
    competencias = CompetenciaSerializer(source='notasXCompetencia', many=True)

    class Meta:
        model = AlumnoXHorario
        fields = ['curso', 'competencias']
    
#Competencias de un horario

class SubCompetenciaClaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCompetencia
        fields = ['clave']

class CompetenciasxHorariosXProfeserializer(serializers.ModelSerializer):
    idCompetenciaxHorario= serializers.CharField(source='id')
    idCompetencia= serializers.CharField(source='idCompetencia.id')
    clave = serializers.CharField(source='idCompetencia.clave')
    nombre = serializers.CharField(source='idCompetencia.nombre')
    descripcion = serializers.CharField(source='idCompetencia.descripcion')
    cantidadEvaluaciones = serializers.IntegerField()

    subcompetencias = SubCompetenciaClaveSerializer(
        many=True, 
        source='idCompetencia.subcompetencias'
    )

    class Meta:
        model = CompetenciaXHorario
        fields = ['idCompetenciaxHorario', 'idCompetencia','clave', 'nombre', 'descripcion', 'cantidadEvaluaciones', 'subcompetencias']
        
        
#Actualizar numero de evaluaciones
class ActualizarCantidadEvaluacionesSerializer(serializers.ModelSerializer):
    cantidad = serializers.IntegerField()  # Nueva cantidad de evaluaciones

    class Meta:
        model = CompetenciaXHorario
        fields = ['cantidad']

    def update(self, instance, validated_data):
        # Actualizar la cantidad de evaluaciones
        instance.cantidadEvaluaciones = validated_data.get('cantidad', instance.cantidadEvaluaciones)
        instance.save()
        return instance
        
## Ver calificacion de competencias

class ProfNotaAlfabeticaSubSerializer(serializers.ModelSerializer):
    subcompetencia = serializers.CharField(source='idSubCompetencia.clave')  # Mostrar la clave de la subcompetencia

    class Meta:
        model = NotaAlfabeticaSub
        fields = ['valor', 'subcompetencia']

class ProfNotaAlfabeticaSerializer(serializers.ModelSerializer):
    notas_alfabeticas_sub = ProfNotaAlfabeticaSubSerializer(many=True, source='notasAlfabeticasSub')

    class Meta:
        model = NotaAlfabetica
        fields = ['valor', 'retroalimentacion', 'indice', 'notas_alfabeticas_sub']

class ProfNotaXCompetenciaSerializer(serializers.ModelSerializer):
    notas_alfabeticas = serializers.SerializerMethodField()

    class Meta:
        model = NotaXCompetencia
        fields = ['notaFinal', 'retroalimentacionFinal', 'notas_alfabeticas']

    def get_notas_alfabeticas(self, obj):
        indice = self.context.get('indice')
        notas_alfabeticas = obj.notasAlfabeticas.filter(indice=indice)
        return ProfNotaAlfabeticaSerializer(notas_alfabeticas, many=True).data
        
class ProfAlumnoXHorarioSerializer(serializers.ModelSerializer):
    notas_de_competencia = serializers.SerializerMethodField()
    alumno = AlumnoDetalleSerializer()  # Asegúrate de que este serializer está correctamente configurado para mostrar la información del alumno
    
    class Meta:
        model = AlumnoXHorario
        fields = ['id', 'alumno', 'notas_de_competencia']
    
    def get_notas_de_competencia(self, obj):
        indice = self.context.get('indice')
        return ProfNotaXCompetenciaSerializer(
            obj.notasXCompetencia.all(), 
            many=True,
            context={'indice': indice}
        ).data
        
        
#########################Guardar calificacion de las competencias

    
    
##Guardar notas finales

class NotaFinalSerializer(serializers.ModelSerializer):

    idalumnoxhorario = serializers.IntegerField(write_only=True)  # ID para buscar

    class Meta:
        model = NotaXCompetencia
        fields = ['idalumnoxhorario', 'notaFinal', 'retroalimentacionFinal']

    def create(self, validated_data):
        id_alumno_x_horario = validated_data.pop('idalumnoxhorario')
        competencia = self.context['competencia']
        
        # Buscar la instancia de NotaXCompetencia
        try:
            nota_x_competencia = NotaXCompetencia.objects.get(
                idAlumnoXHorario_id=id_alumno_x_horario,
                idCompetencia_id=competencia
            )
        except NotaXCompetencia.DoesNotExist:
            raise serializers.ValidationError(
                f"No se encontró una nota para AlumnoXHorario {id_alumno_x_horario} y Competencia {competencia}."
            )
        
        
        # Verificar si los valores han cambiado antes de actualizar
        nota_x_competencia.notaFinal = validated_data.get('notaFinal', nota_x_competencia.notaFinal)
        nota_x_competencia.retroalimentacionFinal = validated_data.get(
            'retroalimentacionFinal', nota_x_competencia.retroalimentacionFinal
        )
        
       #print(f"Nota final creado: {validated_data.get('notaFinal', nota_x_competencia.notaFinal)}")
        #print(f"Retroalimentacion final creado: {validated_data.get('retroalimentacionFinal', nota_x_competencia.retroalimentacionFinal)}")

        # Guardar explícitamente la instancia en la base de datos
        nota_x_competencia.save()
        
        return nota_x_competencia
    
## Listar subcomp de una comp
class ListaSubCompetenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCompetencia
        fields = ['id', 'nombre', 'clave', 'descripcion']

# Serializador para Competencia que incluye sus SubCompetencias
class CompetenciaDetailSerializer(serializers.ModelSerializer):
    subcompetencias = ListaSubCompetenciaSerializer(many=True, read_only=True)

    class Meta:
        model = Competencia
        fields = ['id', 'nombre', 'clave', 'descripcion', 'subcompetencias']

