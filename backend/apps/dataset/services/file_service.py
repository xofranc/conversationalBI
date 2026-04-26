import os
import uuid
from django.conf import settings


ALLOWED_EXTENSIONS = ['.csv', '.xlsx', '.json']
MAX_FILE_SIZE = 50


class FileService:
    
    @staticmethod
    def validate(file) -> None:
        
        ext = os.path.splitext(file.name)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Formato no soportado: {ext}. Formatos permitidos: {', '.join(ALLOWED_EXTENSIONS)}")
        
        size_mb = file.size / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE:
            raise ValueError(f"Archivo demasiado grande: {size_mb:.2f} MB. El tamaño máximo permitido es {MAX_FILE_SIZE} MB.")
        
    @staticmethod
    def save(file, user_id: int) -> str:
        '''
            Retorna la ruta relativa a MEDIA_ROOT
        '''
        
        ext = os.path.splitext(file.name)[1].lower()
        filename = f"{uuid.uuid4().hex}{ext}"
        rel_dir = os.path.join('datasets', str(user_id))
        abs_dir = os.path.join(settings.MEDIA_ROOT, rel_dir)
        
        os.makedirs(abs_dir, exist_ok=True)
        
        with open(os.path.join(abs_dir, filename), 'wb') as dest:
            for chunk in file.chunks():
                dest.write(chunk)
                
        return os.path.join(rel_dir, filename)
    
    
    @staticmethod
    def delete(file_path: str) -> None:
        abs_path = os.path.join(settings.MEDIA_ROOT, file_path)
        if os.path.exists(abs_path):
            os.remove(abs_path)