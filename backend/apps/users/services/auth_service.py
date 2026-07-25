from django.core.exceptions import ValidationError
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
