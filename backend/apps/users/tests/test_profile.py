# apps/users/tests/test_profile.py
import pytest
from rest_framework import status

pytestmark = pytest.mark.django_db

PROFILE_URL = '/api/v1/users/profile/'


@pytest.fixture
def auth_client(api_client, test_user):
    api_client.force_authenticate(user=test_user)
    return api_client


class TestProfileGet:

    def test_requiere_autenticacion(self, api_client):
        response = api_client.get(PROFILE_URL)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_retorna_el_perfil_propio(self, auth_client, test_user):
        response = auth_client.get(PROFILE_URL)
        assert response.status_code == status.HTTP_200_OK
        assert set(response.data) == {'bio', 'phone_number', 'birth_date'}

    def test_crea_perfil_si_no_existe(self, auth_client, test_user):
        # test_user se crea sin Profile; el endpoint no debe explotar
        response = auth_client.get(PROFILE_URL)
        assert response.status_code == status.HTTP_200_OK


class TestProfilePatch:

    def test_actualiza_telefono_valido(self, auth_client):
        response = auth_client.patch(PROFILE_URL, {'phone_number': '3001234567'}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['phone_number'] == '3001234567'

    def test_telefono_invalido_retorna_400(self, auth_client):
        response = auth_client.patch(PROFILE_URL, {'phone_number': 'abc'}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
