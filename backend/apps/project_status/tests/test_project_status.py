import pytest
from rest_framework import status

from apps.project_status.models import ProjectModule, ProjectPhase


@pytest.fixture
def initial_data(db):
    """Las migraciones de datos crean fases y módulos por defecto."""
    return {
        'phases': ProjectPhase.objects.count(),
        'modules': ProjectModule.objects.count(),
    }


@pytest.mark.django_db
class TestProjectStatus:
    def test_endpoint_publico(self, api_client, initial_data):
        response = api_client.get('/api/v1/project-status/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['project_name'] == 'ConversationalBI'
        assert 'author' in response.data
        assert len(response.data['phases']) == initial_data['phases']
        assert len(response.data['modules']) == initial_data['modules']

    def test_fases_ordenadas(self, api_client):
        response = api_client.get('/api/v1/project-status/')
        orders = [p['order'] for p in response.data['phases']]
        assert orders == sorted(orders)

    def test_modulos_tienen_estado(self, api_client):
        response = api_client.get('/api/v1/project-status/')
        for module in response.data['modules']:
            assert module['status'] in dict(ProjectModule.Status.choices)

    def test_author_info_completa(self, api_client):
        response = api_client.get('/api/v1/project-status/')
        author = response.data['author']
        assert author['name'] == 'Santiago Vásquez Franco'
        assert 'github' in author
        assert 'linkedin' in author
        assert 'email' in author
