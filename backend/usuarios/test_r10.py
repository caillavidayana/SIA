"""R10: verificar la política vigente sin reescribir autenticación o recuperación."""
from django.contrib.auth import password_validation
from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase
from .models import Usuario


class PasswordR10Tests(SimpleTestCase):
    def test_politica_publica_solo_expone_minimo_vigente(self):
        r=self.client.get('/api/configuracion-publica/')
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json(),{'password_min_length':10})
    def test_minimo_diez_y_no_numerica(self):
        for password in ('Corta#2','12345678901'):
            with self.assertRaises(ValidationError):password_validation.validate_password(password)
        password_validation.validate_password('SistemaSeguro#2026!')

    def test_no_similar_al_usuario(self):
        u=Usuario(username='NombreApellido2026!',email='NombreApellido2026!@example.test',nombre_completo='Nombre Apellido')
        with self.assertRaises(ValidationError):password_validation.validate_password('NombreApellido2026!',u)

    def test_argon2id_y_compatibilidad_pbkdf2(self):
        password='ClaveValida#2026!'
        actual=make_password(password)
        self.assertTrue(actual.startswith('argon2$argon2id$'))
        self.assertTrue(check_password(password,actual))
        antiguo=make_password(password,hasher='pbkdf2_sha256')
        self.assertTrue(check_password(password,antiguo))
