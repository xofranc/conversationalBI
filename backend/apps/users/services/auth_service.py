from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from ..models import User, Profile


class AuthService:

    # ── Registro ───────────────────────────────────────────────────────────
    @staticmethod
    def register(email: str, password: str,
                 first_name: str, last_name: str) -> User:
        """
        Crea el usuario y su perfil asociado.
        El serializer valida el formato — este método maneja
        la lógica de negocio: unicidad, creación y perfil.
        """
        if User.objects.filter(email=email).exists():
            raise ValidationError("Ya existe una cuenta con ese email.")

        user = User.objects.create_user(
            email      = email,
            password   = password,
            first_name = first_name,
            last_name  = last_name,
        )

        # Crea el perfil asociado al usuario
        Profile.objects.get_or_create(user=user)

        return user

    # ── Login ──────────────────────────────────────────────────────────────
    @staticmethod
    def login(email: str, password: str) -> dict:
        """
        Autentica y retorna los tokens JWT.
        Centraliza la lógica para poder reutilizarla
        en otros flujos como OAuth en el futuro.
        """
        user = authenticate(email=email, password=password)

        if not user:
            raise ValidationError("Credenciales inválidas.")

        if not user.is_active:
            raise ValidationError("La cuenta está desactivada.")

        refresh = RefreshToken.for_user(user)

        return {
            "user": {
                "id":         user.id,
                "email":      user.email,
                "first_name": user.first_name,
                "last_name":  user.last_name,
                "user_type":  user.user_type,
            },
            "access":  str(refresh.access_token),
            "refresh": str(refresh),
        }

    # ── Logout ─────────────────────────────────────────────────────────────
    @staticmethod
    def logout(refresh_token: str) -> None:
        """
        Invalida el refresh token agregándolo a la blacklist.
        Requiere INSTALLED_APPS: 'rest_framework_simplejwt.token_blacklist'
        """
        from rest_framework_simplejwt.tokens import RefreshToken, TokenError
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError as e:
            raise ValidationError(f"Token inválido o expirado: {e}")

    # ── Utilidades ─────────────────────────────────────────────────────────
    @staticmethod
    def get_user_by_email(email: str) -> User:
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            raise ValidationError("No existe ningún usuario con ese email.")

    @staticmethod
    def deactivate_user(user: User) -> None:
        """Desactiva la cuenta sin eliminarla — útil para admin."""
        user.is_active = False
        user.save(update_fields=['is_active'])

    @staticmethod
    def change_password(user: User, old_password: str,
                        new_password: str) -> None:
        """
        Cambia la contraseña verificando la anterior.
        Invalida todos los tokens activos al cambiar.
        """
        if not user.check_password(old_password):
            raise ValidationError("La contraseña actual es incorrecta.")

        user.set_password(new_password)
        user.save(update_fields=['password'])