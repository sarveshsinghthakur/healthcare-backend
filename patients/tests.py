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


class PatientAPITests(TestCase):
    def setUp(self):
        self.client1 = login_client('p1@example.com')
        self.client2 = login_client('p2@example.com')

    def _create(self, client, **overrides):
        data = {'name': 'John Doe', 'age': 30, 'gender': 'M', 'phone': '555-1234'}
        data.update(overrides)
        return client.post('/api/patients/', data, format='json')

    def test_unauthenticated_rejected(self):
        r = APIClient().get('/api/patients/')
        self.assertEqual(r.status_code, 401)

    def test_full_crud_flow(self):
        r = self._create(self.client1)
        self.assertEqual(r.status_code, 201)
        pid = r.data['id']

        r = self.client1.get('/api/patients/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.data), 1)

        r = self.client1.get(f'/api/patients/{pid}/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['age'], 30)

        r = self.client1.put(
            f'/api/patients/{pid}/',
            {'name': 'John Doe', 'age': 31, 'gender': 'M', 'disease': 'Cold'},
            format='json',
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['age'], 31)

        r = self.client1.delete(f'/api/patients/{pid}/')
        self.assertEqual(r.status_code, 204)

    def test_scoping_other_user_cannot_see_patient(self):
        pid = self._create(self.client1).data['id']

        # other user's list is empty
        r = self.client2.get('/api/patients/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data, [])

        # detail / update / delete of another user's patient -> 404
        self.assertEqual(self.client2.get(f'/api/patients/{pid}/').status_code, 404)
        r = self.client2.put(
            f'/api/patients/{pid}/',
            {'name': 'H', 'age': 20, 'gender': 'M'},
            format='json',
        )
        self.assertEqual(r.status_code, 404)
        self.assertEqual(self.client2.delete(f'/api/patients/{pid}/').status_code, 404)

    def test_age_validation(self):
        self.assertEqual(self._create(self.client1, age=0).status_code, 400)
        self.assertEqual(self._create(self.client1, age=200).status_code, 400)

    def test_phone_validation(self):
        self.assertEqual(self._create(self.client1, phone='abc').status_code, 400)
        self.assertEqual(self._create(self.client1, phone='').status_code, 201)

    def test_gender_required_and_valid_choice(self):
        data = {'name': 'A', 'age': 20}
        r = self.client1.post('/api/patients/', data, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertEqual(self._create(self.client1, gender='X').status_code, 400)

    def test_whitespace_name_rejected(self):
        self.assertEqual(self._create(self.client1, name='   ').status_code, 400)
