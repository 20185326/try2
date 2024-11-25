from faker import Faker
import random
from datetime import date
from .models import Alumno
from django.db import transaction

fake = Faker()

def generar_telefono_formateado():
    # Generar las tres partes del número
    parte1 = random.randint(900, 999)  # Ej: 987
    parte2 = random.randint(100, 999)  # Ej: 654
    parte3 = random.randint(100, 999)  # Ej: 321

    # Formatear como '987 654 321'
    telefono = f"{parte1} {parte2} {parte3}"
    return telefono


def generar_alumnos(cantidad):
    """
    Genera una cantidad especificada de alumnos con datos aleatorios usando Faker
    y los guarda en la base de datos.
    
    Args:
        cantidad (int): Número de alumnos a generar.
    """
    alumnos_creados = []
    
    with transaction.atomic():
        for _ in range(cantidad):
            nombre = fake.first_name()
            primer_apellido = fake.last_name()
            segundo_apellido = fake.last_name()
            correo = fake.unique.email()
            codigo = fake.unique.bothify(text="2023####")  # Genera un código aleatorio único
            fecha_registro = fake.date_this_decade()
            telefono = generar_telefono_formateado()
            
            # Datos específicos del modelo Alumno
            factor_desempeno = 0  # Ejemplo de rendimiento aleatorio de 0 a 10
            creditos_primera = 0
            creditos_segunda = 0
            creditos_tercera = 0
            puntaje_competencias = random.choice(['A', 'B', 'C', 'D'])  # Ejemplo de puntaje
            numero_semestres = random.randint(1, 10)
            turno_orden_matricula = random.randint(1, 3)  # Ejemplo de turno entre 1 y 3
            anio_ingreso = fake.date_between(start_date="-5y", end_date="today")
            
            # Crear instancia de Alumno
            alumno = Alumno(
                nombre=nombre,
                primerApellido=primer_apellido,
                segundoApellido=segundo_apellido,
                correo=correo,
                codigo=codigo,
                fechaRegistro=fecha_registro,
                telefono=telefono,
                activo=True,
                factorDeDesempeno=factor_desempeno,
                creditosPrimera=creditos_primera,
                creditosSegunda=creditos_segunda,
                creditosTercera=creditos_tercera,
                puntajeTotalPorCompetencias=puntaje_competencias,
                numeroSemestres=numero_semestres,
                turnoOrdenMatricula=turno_orden_matricula,
                anioIngreso=anio_ingreso
            )
            
            # Guardar el alumno en la base de datos
            alumno.save()
            alumnos_creados.append(alumno)
        
        print(f"{len(alumnos_creados)} alumnos creados exitosamente.")
        
        