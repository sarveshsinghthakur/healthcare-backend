from django.test import TestCase
from rest_framework.test import APIClient

PASSWORD = 'Str0ngPass!23'


def login_client(email):
    client = APIClient()
    client.post(
        '/api/auth/register/',
        {'name': 'User', 'email': email, 'password': PASSWORD},
        format='json',
    )
    r = client.post(
        '/api/auth/login/', {'email': email, 'password': PASSWORD}, format='json'
    )
    client.credentials(HTTP_AUTHORIZATION='Bearer ' + r.data['access'])
    return client


class DoctorAPITests(TestCase):
    def setUp(self):
        self.client1 = login_client('d1@example.com')
        self.client2 = login_client('d2@example.com')

    def _create(self, client, **overrides):
        data = {
            'name': 'Dr Smith',
            'specialization': 'Cardiology',
            'phone': '555-5678',
            'email': 'dr@example.com',
        }
        data.update(overrides)
        return client.post('/api/doctors/', data, format='json')

    def test_unauthenticated_rejected(self):
        self.assertEqual(APIClient().get('/api/doctors/').status_code, 401)

    def test_full_crud_flow(self):
        r = self._create(self.client1)
        self.assertEqual(r.status_code, 201)
        did = r.data['id']

        r = self.client1.get('/api/doctors/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.data), 1)

        r = self.client1.get(f'/api/doctors/{did}/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['name'], 'Dr Smith')

        r = self.client1.put(
            f'/api/doctors/{did}/',
            {'name': 'Dr Smith', 'specialization': 'Neurology'},
            format='json',
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['specialization'], 'Neurology')

        self.assertEqual(self.client1.delete(f'/api/doctors/{did}/').status_code, 204)

    def test_doctor_list_is_global_for_authenticated_users(self):
        self._create(self.client1)
        r = self.client2.get('/api/doctors/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.data), 1)

    def test_email_normalized_lowercase(self):
        r = self._create(self.client1, email='DR@Example.COM')
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data['email'], 'dr@example.com')

    def test_invalid_email_rejected(self):
        self.assertEqual(self._create(self.client1, email='not-an-email').status_code, 400)

    def test_phone_validation(self):
        self.assertEqual(self._create(self.client1, phone='abc').status_code, 400)
        self.assertEqual(self._create(self.client1, phone='+1 (555) 123-4567').status_code, 201)

    def test_missing_required_fields(self):
        r = self.client1.post('/api/doctors/', {'name': 'Dr X'}, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertEqual(self._create(self.client1, name='   ').status_code, 400)
        self.assertEqual(self._create(self.client1, specialization='  ').status_code, 400)

    def test_delete_not_found(self):
        self.assertEqual(self.client1.delete('/api/doctors/9999/').status_code, 404)
