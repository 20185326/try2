import pandas as pd

from .models import Competencia, SubCompetencia,NotaNumerica,TNota
import random
from cursos.models import Curso,Horario,Formula, PeriodoAcademico
from matricula.models import AlumnoXHorario
from django.db import transaction


file_path = r"E:\DOCUMENTOS\Documentos PUCP\12avo Ciclo\IngeSoft\competencias_subcompetencias_rubrica.xlsx"

# Cargar el archivo Excel en un DataFrame
df = pd.read_excel(file_path)


def importar_competencias_nuevas():
    with transaction.atomic():
        competencia_actual = None  # Variable para guardar la última competencia creada
        clave_anterior = None  # Variable para controlar cambios en la clave de competencia

        for _, row in df.iterrows():
            clave_actual = row['idcompetencia']  # Clave de la competencia actual

            # Verificar si la competencia debe ser creada o si es la misma que la fila anterior
            if clave_actual != clave_anterior:
                # Crear una nueva Competencia porque la clave cambió
                competencia_actual = Competencia.objects.create(
                    nombre=row['nombre_competencia'],
                    clave=row['idcompetencia'],
                    descripcion=row['descripcion_competencia'],
                    activo=True
                )
                # Actualizar la clave anterior
                clave_anterior = clave_actual

            # Crear la SubCompetencia para la competencia actual
            SubCompetencia.objects.create(
                idCompetencia=competencia_actual,
                nombre=row['nombre_subcompetencia'],
                clave=row['idsubcompetencia'],
                descripcion=row['descripción_subcompetencia'],
                nivelInicial=row['criterio_inicial'],
                nivelEnProceso=row['criterio_en_proceso'],
                nivelSatisfactorio=row['criterio_satisfactorio'],
                nivelSobresaliente=row['criterio_sobresaliente'],
                activo=True
            )
            
            
##Crear las notas de los alumnos           
def crear_notas_para_periodo(periodo):
    """
    Crea las notas numéricas para todos los alumnos de los cursos en el periodo especificado.

    Args:
        periodo (PeriodoAcademico): El periodo académico para el cual se crearán las notas.
    """
    # Obtener todos los cursos en el periodo especificado
    cursos = Curso.objects.all()
    periodoActual = PeriodoAcademico.objects.filter(actual=True).first()
    
    # Iniciar una transacción para asegurar consistencia
    with transaction.atomic():
        # Iterar a través de cada curso
        for curso in cursos:
            # Obtener la fórmula del curso
            formula = curso.formula
            
            # Si no hay fórmula asignada, saltar el curso
            if not formula:
                continue
            
            # Recorrer todos los horarios del curso
            horarios = curso.horarios.all()
            for horario in horarios:
                # Obtener los alumnos inscritos en este horario
                alumnos_x_horario = AlumnoXHorario.objects.filter(horario=horario,periodo=periodoActual)
                
                for alumno_x_horario in alumnos_x_horario:
                    # Lista para almacenar las notas a crear
                    notas_a_crear = []
                    
                    # Crear notas de tipo Practica
                    if formula.numPracticas > 0 and formula.pesoPracticas > 0:
                        for i in range(1, formula.numPracticas + 1):
                            # Verificar si la nota ya existe
                            if not NotaNumerica.objects.filter(
                                idAlumnoXHorario=alumno_x_horario,
                                tipoDeNota=TNota.PRACTICA,
                                indice=i
                            ).exists():
                                notas_a_crear.append(NotaNumerica(
                                    idAlumnoXHorario=alumno_x_horario,
                                    tipoDeNota=TNota.PRACTICA,
                                    indice=i,
                                    valor=random.randint(0, 20)  # Valor inicial de la nota
                                ))
                    
                    # Crear notas de tipo Parcial
                    if formula.pesoParciales > 0:
                        if not NotaNumerica.objects.filter(
                            idAlumnoXHorario=alumno_x_horario,
                            tipoDeNota=TNota.PARCIAL,
                            indice=1
                        ).exists():
                            notas_a_crear.append(NotaNumerica(
                                idAlumnoXHorario=alumno_x_horario,
                                tipoDeNota=TNota.PARCIAL,
                                indice=1,
                                valor=random.randint(0, 20)  # Valor inicial de la nota
                            ))
                    
                    # Crear notas de tipo Final
                    if formula.pesoFinales > 0:
                        if not NotaNumerica.objects.filter(
                            idAlumnoXHorario=alumno_x_horario,
                            tipoDeNota=TNota.FINAL,
                            indice=1
                        ).exists():
                            notas_a_crear.append(NotaNumerica(
                                idAlumnoXHorario=alumno_x_horario,
                                tipoDeNota=TNota.FINAL,
                                indice=1,
                                valor=random.randint(0, 20)  # Valor inicial de la nota
                            ))
                    
                    # Si no hay notas de Practica, Parcial o Final, crear una nota Unica
                    if not notas_a_crear:
                        if not NotaNumerica.objects.filter(
                            idAlumnoXHorario=alumno_x_horario,
                            tipoDeNota=TNota.UNICA,
                            indice=1
                        ).exists():
                            notas_a_crear.append(NotaNumerica(
                                idAlumnoXHorario=alumno_x_horario,
                                tipoDeNota=TNota.UNICA,
                                indice=1,
                                valor=random.randint(0, 20)  # Valor inicial de la nota
                            ))
                    
                    # Guardar todas las notas en la base de datos
                    NotaNumerica.objects.bulk_create(notas_a_crear)
                    
            print(f"Curso {curso.nombre} completado!!")