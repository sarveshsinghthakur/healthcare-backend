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


class MappingAPITests(TestCase):
    def setUp(self):
        self.client1 = login_client('m1@example.com')
        self.client2 = login_client('m2@example.com')

        self.patient1 = self.client1.post(
            '/api/patients/',
            {'name': 'Pat One', 'age': 30, 'gender': 'M'},
            format='json',
        ).data['id']
        self.patient2 = self.client2.post(
            '/api/patients/',
            {'name': 'Pat Two', 'age': 40, 'gender': 'F'},
            format='json',
        ).data['id']
        self.doctor = self.client1.post(
            '/api/doctors/',
            {'name': 'Dr Map', 'specialization': 'General'},
            format='json',
        ).data['id']

    def _map(self, client, patient, doctor):
        return client.post(
            '/api/mappings/', {'patient': patient, 'doctor': doctor}, format='json'
        )

    def test_unauthenticated_rejected(self):
        self.assertEqual(APIClient().get('/api/mappings/').status_code, 401)

    def test_create_and_list_mapping(self):
        r = self._map(self.client1, self.patient1, self.doctor)
        self.assertEqual(r.status_code, 201)
        self.assertIn('doctor_detail', r.data)

        r = self.client1.get('/api/mappings/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.data), 1)

    def test_duplicate_mapping_rejected(self):
        self._map(self.client1, self.patient1, self.doctor)
        r = self._map(self.client1, self.patient1, self.doctor)
        self.assertEqual(r.status_code, 400)
        self.assertIn('error', r.data)

    def test_cannot_map_another_users_patient(self):
        r = self._map(self.client2, self.patient1, self.doctor)
        self.assertEqual(r.status_code, 400)
        self.assertIn('own patients', str(r.data))

    def test_list_is_scoped_to_own_patients(self):
        self._map(self.client1, self.patient1, self.doctor)
        r = self.client2.get('/api/mappings/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data, [])

    def test_doctors_for_patient_spec_route(self):
        self._map(self.client1, self.patient1, self.doctor)
        r = self.client1.get(f'/api/mappings/{self.patient1}/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.data['doctors']), 1)
        self.assertEqual(r.data['patient_id'], self.patient1)

    def test_doctors_for_patient_alias_route(self):
        self._map(self.client1, self.patient1, self.doctor)
        r = self.client1.get(f'/api/mappings/patient/{self.patient1}/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.data['doctors']), 1)

    def test_patient_without_doctors_returns_empty_list(self):
        r = self.client1.get(f'/api/mappings/{self.patient1}/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['doctors'], [])

    def test_unknown_patient_returns_404(self):
        r = self.client1.get('/api/mappings/9999/')
        self.assertEqual(r.status_code, 404)
        r = self.client1.get('/api/mappings/patient/9999/')
        self.assertEqual(r.status_code, 404)

    def test_cannot_read_other_users_patient_doctors(self):
        r = self.client2.get(f'/api/mappings/{self.patient1}/')
        self.assertEqual(r.status_code, 404)
        r = self.client2.get(f'/api/mappings/patient/{self.patient1}/')
        self.assertEqual(r.status_code, 404)

    def test_delete_mapping(self):
        mid = self._map(self.client1, self.patient1, self.doctor).data['id']

        r = self.client1.delete(f'/api/mappings/{mid}/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.client1.get('/api/mappings/').data, [])

        # deleting again -> 404
        self.assertEqual(self.client1.delete(f'/api/mappings/{mid}/').status_code, 404)

    def test_cannot_delete_other_users_mapping(self):
        mid = self._map(self.client1, self.patient1, self.doctor).data['id']
        r = self.client2.delete(f'/api/mappings/{mid}/')
        self.assertEqual(r.status_code, 404)

    def test_missing_fields_rejected(self):
        r = self.client1.post('/api/mappings/', {'patient': self.patient1}, format='json')
        self.assertEqual(r.status_code, 400)
