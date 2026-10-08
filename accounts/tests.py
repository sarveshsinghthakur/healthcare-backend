from django.test import TestCase
from rest_framework.test import APIClient

PASSWORD = 'Str0ngPass!23'


class AuthAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def _register(self, email='ada@example.com', password=PASSWORD, name='Ada'):
        return self.client.post(
            '/api/auth/register/',
            {'name': name, 'email': email, 'password': password},
            format='json',
        )

    def _login(self, email='ada@example.com', password=PASSWORD):
        return self.client.post(
            '/api/auth/login/', {'email': email, 'password': password}, format='json'
        )

    def test_register_success_normalizes_email(self):
        r = self._register(email='Ada@Example.com')
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data['email'], 'ada@example.com')
        self.assertNotIn('password', r.data)

    def test_register_duplicate_email_case_insensitive(self):
        self._register(email='ada@example.com')
        r = self._register(email='ADA@example.com')
        self.assertEqual(r.status_code, 400)
        self.assertIn('error', r.data)

    def test_register_weak_password_rejected(self):
        r = self._register(email='weak@example.com', password='12345678', name='Weak')
        self.assertEqual(r.status_code, 400)

    def test_register_whitespace_name_rejected(self):
        r = self._register(email='ws@example.com', name='   ')
        self.assertEqual(r.status_code, 400)

    def test_register_missing_fields(self):
        r = self.client.post('/api/auth/register/', {'email': 'x@example.com'}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_login_returns_jwt_pair(self):
        self._register()
        r = self._login()
        self.assertEqual(r.status_code, 200)
        self.assertIn('access', r.data)
        self.assertIn('refresh', r.data)

    def test_login_is_case_insensitive(self):
        self._register(email='ada@example.com')
        r = self._login(email='ADA@example.com')
        self.assertEqual(r.status_code, 200)

    def test_login_wrong_password(self):
        self._register()
        r = self._login(password='WrongPass!99')
        self.assertEqual(r.status_code, 400)
        self.assertIn('error', r.data)

    def test_login_unknown_email(self):
        r = self._login(email='nobody@example.com')
        self.assertEqual(r.status_code, 400)
        self.assertIn('error', r.data)

    def test_refresh_returns_new_access_token(self):
        self._register()
        refresh = self._login().data['refresh']
        r = self.client.post('/api/auth/refresh/', {'refresh': refresh}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertIn('access', r.data)

    def test_refresh_rejects_garbage_token(self):
        r = self.client.post('/api/auth/refresh/', {'refresh': 'not-a-token'}, format='json')
        self.assertEqual(r.status_code, 401)
        self.assertIn('error', r.data)
