from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


# Create your models here.


class CustomUserManager(BaseUserManager):
    
    #! Usamos de referencia el modelo de usuario personalizado de Django, para crear un nuevo usuario
    
    def create_user(self, email, password=None, **extra_fields):
        
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', User.ADMIN)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('El superusuario debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('El superusuario debe tener is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)
    
class User(AbstractUser):
    
    USER = 'USER'
    ADMIN = 'ADMIN'
    
    USER_TYPE_CHOICES = [
        (USER, 'User'),
        (ADMIN, 'Admin'),
    ]
    
    #! Sobrescribimos el campo username para usar email como identificador único
    username = None
    
    
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    is_active = models.BooleanField(default=True)
    
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    

    
    
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default=USER)
    
    
    #! Agregamos un campo para almacenar el ID del tipo de usuario, que puede ser útil para consultas rápidas
    user_type_id = models.PositiveIntegerField(null=True, blank=True, db_index=True )
    
    USER_TYPE_ID_MAP = {
        USER: 1,
        ADMIN: 2,
    }
    
    
    
    def save(self, *args, **kwargs):
        
        if self.user_type in self.USER_TYPE_ID_MAP:
            self.user_type_id = self.USER_TYPE_ID_MAP[self.user_type]
        
        else:
            self.user_type_id = None
            
        super().save(*args, **kwargs)
        
        
    def __str__(self):
        
        return f"{self.email} ({self.user_type.capitalize()} - ID: {self.user_type_id or 'N/A'})"



class Profile(models.Model):
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True)
    phone_number = models.CharField(max_length=10, blank=True, unique=True)
    birth_date = models.DateField(null=True, blank=True)
    entry_date = models.DateField(auto_now_add=True)

    query_count = models.PositiveIntegerField(default=0)
    query_limit = models.PositiveIntegerField(default=100)
    
    
    
    def save(self, *args, **kwargs):
        
        if self.phone_number and not self.phone_number.isdigit():
            raise ValueError('El número de teléfono debe contener solo dígitos')
        
        elif self.phone_number and len(self.phone_number) != 10:
            raise ValueError('El número de teléfono debe tener exactamente 10 dígitos')

        super().save(*args, **kwargs)
        