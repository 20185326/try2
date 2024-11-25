from django.test import TestCase

from django.db import connections
#from usuarios.models import Formula

# Create your tests here.
class listarFormulas(TestCase):
    
    def listarFormulas(self):
        param= 1
       # formulas= Formula.objects.all()
        #self.assertEqual(formulas.count(),13)
        #self.assertEqual(formulas[0].idformula, 1)
        #self.assertEqual(formulas[0].idformula, 2)
        
        

#python manage.py inspectdb nombre_tabla1 nombre_tabla2 > usuarios/models.py
#python manage.py inspectdb > usuarios/models.py
