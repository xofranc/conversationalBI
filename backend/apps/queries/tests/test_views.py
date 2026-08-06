# apps/queries/tests/test_views.py
from unittest.mock import patch

import pytest
from rest_framework import status

from apps.dataset.models import Dataset
from apps.queries.models import QueryFeedback, QueryHistory

pytestmark = pytest.mark.django_db

QUERY_URL = '/api/v1/queries/'
PREGUNTA = 'ventas totales por region'


@pytest.fixture
def dataset_error(test_user):
    return Dataset.objects.create(
        user=test_user,
        name='Dataset roto',
        file_path='datasets/x.csv',
        status=Dataset.Status.ERROR,
    )


@pytest.fixture
def otro_dataset(db):
    from django.contrib.auth import get_user_model
    otro = get_user_model().objects.create_user(
        email='otro@example.com', password='pass12345',
        first_name='Otro', last_name='User',
    )
    return Dataset.objects.create(
        user=otro,
        name='Ajeno',
        file_path='datasets/y.csv',
        status=Dataset.Status.READY,
    )


@pytest.fixture
def auth_client(api_client, test_user):
    api_client.force_authenticate(user=test_user)
    return api_client


class TestQueryCreate:

    def test_requiere_autenticacion(self, api_client, test_dataset):
        response = api_client.post(QUERY_URL, {
            'question': PREGUNTA, 'dataset_id': test_dataset.id,
        }, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_dataset_de_otro_usuario_retorna_403(self, auth_client, otro_dataset):
        response = auth_client.post(QUERY_URL, {
            'question': PREGUNTA, 'dataset_id': otro_dataset.id,
        }, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_dataset_inexistente_retorna_403(self, auth_client):
        # El guard de ownership no revela si el dataset existe
        response = auth_client.post(QUERY_URL, {
            'question': PREGUNTA, 'dataset_id': 99999,
        }, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_dataset_no_ready_retorna_400(self, auth_client, dataset_error):
        response = auth_client.post(QUERY_URL, {
            'question': PREGUNTA, 'dataset_id': dataset_error.id,
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'listo' in str(response.data).lower()

    def test_error_interno_no_filtra_detalles(self, auth_client, test_dataset):
        with patch('apps.queries.views.QueryService.execute') as mock_exec:
            mock_exec.side_effect = Exception('sqlite3.OperationalError: near "SECRET_TRACE"')
            response = auth_client.post(QUERY_URL, {
                'question': PREGUNTA, 'dataset_id': test_dataset.id,
            }, format='json')

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert 'SECRET_TRACE' not in response.content.decode()
        assert 'sqlite3' not in response.content.decode()


class TestQueryList:

    def test_list_no_incluye_result_json(self, auth_client, test_user, test_dataset):
        from apps.queries.models import QueryResult
        query = QueryHistory.objects.create(
            user=test_user, dataset=test_dataset, question=PREGUNTA, success=True,
        )
        QueryResult.objects.create(
            query=query, result_json=[{'a': 1}] * 100, columns=[],
            row_count=100, chart_type='table',
        )

        response = auth_client.get(QUERY_URL)

        assert response.status_code == status.HTTP_200_OK
        body = response.content.decode()
        assert 'result_json' not in body
        assert response.data['results'][0]['id'] == query.id

    def test_list_solo_muestra_queries_propias(self, auth_client, test_user, test_dataset, otro_dataset):
        from django.contrib.auth import get_user_model
        otro = get_user_model().objects.get(email='otro@example.com')
        QueryHistory.objects.create(user=test_user, dataset=test_dataset, question=PREGUNTA)
        QueryHistory.objects.create(user=otro, dataset=otro_dataset, question='query ajena')

        response = auth_client.get(QUERY_URL)

        assert response.data['count'] == 1


class TestFeedback:

    def _crear_query(self, test_user, test_dataset):
        return QueryHistory.objects.create(
            user=test_user, dataset=test_dataset,
            question=PREGUNTA, success=True,
        )

    def test_feedback_exitoso(self, auth_client, test_user, test_dataset):
        query = self._crear_query(test_user, test_dataset)
        response = auth_client.post(
            f'{QUERY_URL}{query.id}/feedback/',
            {'score': 1, 'comment': 'útil'}, format='json',
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert QueryFeedback.objects.filter(query=query).exists()

    def test_feedback_duplicado_retorna_400(self, auth_client, test_user, test_dataset):
        query = self._crear_query(test_user, test_dataset)
        QueryFeedback.objects.create(query=query, score=1)

        response = auth_client.post(
            f'{QUERY_URL}{query.id}/feedback/',
            {'score': -1}, format='json',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_feedback_en_query_ajena_retorna_404(self, auth_client, test_user, otro_dataset):
        from django.contrib.auth import get_user_model
        otro = get_user_model().objects.get(email='otro@example.com')
        query = QueryHistory.objects.create(
            user=otro, dataset=otro_dataset, question=PREGUNTA, success=True,
        )
        response = auth_client.post(
            f'{QUERY_URL}{query.id}/feedback/',
            {'score': 1}, format='json',
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
