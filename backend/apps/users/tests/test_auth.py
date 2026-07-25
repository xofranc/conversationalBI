# apps/users/tests/test_auth.py
import pytest
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import Profile

pytestmark = pytest.mark.django_db

REGISTER_URL = '/api/v1/users/register/'
LOGIN_URL = '/api/v1/users/login/'
LOGOUT_URL = '/api/v1/users/logout/'
REFRESH_URL = '/api/v1/users/token/refresh/'

USER_DATA = {
    'email': 'nuevo@example.com',
    'password': 'Segura#2026xyz',
    'first_name': 'Nuevo',
    'last_name': 'Usuario',
}


class TestRegister:

    def test_registro_exitoso_crea_perfil(self, api_client):
        response = api_client.post(REGISTER_URL, USER_DATA, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert Profile.objects.filter(user__email=USER_DATA['email']).exists()

    def test_email_duplicado_retorna_400_no_500(self, api_client, test_user):
        response = api_client.post(REGISTER_URL, {
            **USER_DATA, 'email': test_user.email,
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_password_debil_retorna_400(self, api_client):
        response = api_client.post(REGISTER_URL, {
            **USER_DATA, 'password': '123',
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestLogin:

    def test_login_exitoso_retorna_ambos_tokens(self, api_client, test_user):
        response = api_client.post(LOGIN_URL, {
            'email': test_user.email, 'password': 'testpass123',
        }, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['access']
        assert response.data['refresh']

    def test_credenciales_invalidas_retorna_400(self, api_client, test_user):
        response = api_client.post(LOGIN_URL, {
            'email': test_user.email, 'password': 'incorrecta',
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cuenta_desactivada_retorna_400(self, api_client, test_user):
        test_user.is_active = False
        test_user.save(update_fields=['is_active'])
        response = api_client.post(LOGIN_URL, {
            'email': test_user.email, 'password': 'testpass123',
        }, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestRefresh:

    def test_refresh_retorna_nuevo_access_y_rota_refresh(self, api_client, test_user):
        refresh = RefreshToken.for_user(test_user)
        response = api_client.post(REFRESH_URL, {'refresh': str(refresh)}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['access']
        # ROTATE_REFRESH_TOKENS=True → también devuelve un refresh nuevo
        assert response.data['refresh']
        assert response.data['refresh'] != str(refresh)

    def test_refresh_invalido_retorna_401(self, api_client):
        response = api_client.post(REFRESH_URL, {'refresh': 'token-falso'}, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestLogout:

    def test_logout_invalida_el_refresh(self, api_client, test_user):
        refresh = RefreshToken.for_user(test_user)
        api_client.force_authenticate(user=test_user)

        response = api_client.post(LOGOUT_URL, {'refresh': str(refresh)}, format='json')
        assert response.status_code == status.HTTP_200_OK

        # El refresh queda en blacklist: ya no sirve para pedir nuevos access
        response = api_client.post(REFRESH_URL, {'refresh': str(refresh)}, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_requiere_autenticacion(self, api_client):
        response = api_client.post(LOGOUT_URL, {'refresh': 'x'}, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
