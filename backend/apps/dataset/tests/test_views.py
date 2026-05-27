import pytest
from unittest.mock import patch
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.dataset.models import Dataset 

User = get_user_model()
pytestmark = pytest.mark.django_db


    
@pytest.fixture
def user(db):
    return User.objects.create_user(email="view@bi.com", password="test1234")

@pytest.fixture
def other_user(db):
    return User.objects.create_user(email="otro@bi.com", password="test1234")

@pytest.fixture
def client(user):
    c = APIClient()
    c.force_authenticate(user=user)
    return c

@pytest.fixture
def dataset(user):
    return Dataset.objects.create(
        user        = user,
        name        = "Ventas Q1",
        file_path   = "datasets/test.csv",
        file_size   = 2048,
        status      = Dataset.Status.READY,
        row_count   = 100,
        schema_json = {"tables": []},
    )


class TestDatasetList:

    def test_lista_solo_datasets_del_usuario(self, client, user, other_user):
        Dataset.objects.create(user=user,       name="Mío",   file_path="a", file_size=1)
        Dataset.objects.create(user=other_user, name="Ajeno", file_path="b", file_size=1)

        response = client.get('/api/v1/dataset/')

        assert response.status_code == 200
        nombres = [d['name'] for d in response.data]
        assert 'Mío'   in nombres
        assert 'Ajeno' not in nombres

    def test_requiere_autenticacion(self):
        response = APIClient().get('/api/v1/dataset/')
        assert response.status_code == 401


class TestDatasetRetrieve:

    def test_propietario_puede_ver_detalle(self, client, dataset):
        response = client.get(f'/api/v1/dataset/{dataset.id}/')
        assert response.status_code == 200
        assert response.data['name'] == 'Ventas Q1'

    def test_otro_usuario_no_puede_ver_detalle(self, other_user, dataset):
        c = APIClient()
        c.force_authenticate(user=other_user)
        response = c.get(f'/api/v1/dataset/{dataset.id}/')
        assert response.status_code == 404


class TestDatasetUpload:

    @patch('apps.dataset.views.DatasetService.create')
    def test_upload_exitoso(self, mock_create, client, user, dataset):
        mock_create.return_value = dataset
        from io import BytesIO
        fake_file = BytesIO(b"id,valor\n1,100\n")
        fake_file.name = "datos.csv"

        response = client.post('/api/v1/dataset/', {
            'file': fake_file,
            'name': 'Test Upload',
        }, format='multipart')

        assert response.status_code == 201
        assert response.data['name'] == 'Ventas Q1'

    def test_upload_sin_archivo_retorna_400(self, client):
        response = client.post('/api/v1/dataset/', {'name': 'Sin archivo'}, format='multipart')
        assert response.status_code == 400

    def test_upload_sin_autenticacion_retorna_401(self):
        response = APIClient().post('/api/v1/dataset/', {}, format='multipart')
        assert response.status_code == 401


class TestDatasetDestroy:

    @patch('apps.dataset.views.DatasetService.delete')
    def test_propietario_puede_eliminar(self, mock_delete, client, dataset):
        response = client.delete(f'/api/v1/dataset/{dataset.id}/')
        assert response.status_code == 204
        mock_delete.assert_called_once_with(dataset.id, client.handler._force_user)

    def test_otro_usuario_no_puede_eliminar(self, other_user, dataset):
        c = APIClient()
        c.force_authenticate(user=other_user)
        response = c.delete(f'/api/v1/dataset/{dataset.id}/')
        assert response.status_code == 404


class TestDatasetSchema:

    def test_retorna_schema_json(self, client, dataset):
        response = client.get(f'/api/v1/dataset/{dataset.id}/schema/')
        assert response.status_code == 200
        assert 'schema_json' in response.data
        assert 'id'          in response.data
        