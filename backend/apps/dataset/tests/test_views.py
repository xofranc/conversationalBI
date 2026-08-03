import pytest
from unittest.mock import patch
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.dataset.models import Dataset
from conftest import requires_postgres

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

    @requires_postgres
    def test_upload_integracion_real(self, client, settings, tmp_path, schema_cleanup):
        """Sin mocks: procesa un CSV real y verifica el estado final del dataset.

        Este test habría detectado el P0-1 (firma de mark_ready).
        """
        settings.MEDIA_ROOT = tmp_path
        from io import BytesIO
        csv = BytesIO(b"id,valor\n1,100\n2,200\n3,300\n")
        csv.name = "ventas.csv"

        response = client.post('/api/v1/dataset/', {
            'file': csv,
            'name': 'Ventas Reales',
        }, format='multipart')

        assert response.status_code == 201, response.data
        assert response.data['status'] == 'ready'
        assert response.data['row_count'] == 3
        assert response.data['column_count'] == 2
        assert len(response.data['tables']) == 1
        assert response.data['tables'][0]['row_count'] == 3

        ds = Dataset.objects.get(name='Ventas Reales')
        schema_cleanup.append(ds.db_path)
        assert ds.status == Dataset.Status.READY
        assert ds.column_count == 2
        assert ds.schema_json['tables'][0]['name'] == 'main'
        # La materialización ya no es un archivo: es el schema ds_<id> en Postgres
        assert ds.db_path == f'ds_{ds.id}'

    @requires_postgres
    def test_upload_csv_con_fechas_marca_ready(self, client, settings, tmp_path, schema_cleanup):
        """Las columnas fecha no deben romper la persistencia del schema (JSONField)."""
        settings.MEDIA_ROOT = tmp_path
        from io import BytesIO
        csv = BytesIO(b"fecha,monto\n2024-01-15,100.5\n2024-02-03,200.75\n")
        csv.name = "fechas.csv"

        response = client.post('/api/v1/dataset/', {
            'file': csv,
            'name': 'Con Fechas',
        }, format='multipart')

        assert response.status_code == 201, response.data
        assert response.data['status'] == 'ready'
        schema_cleanup.append(Dataset.objects.get(name='Con Fechas').db_path)

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
        