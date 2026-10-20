from apps.dataset.domain.policies import DatasetUploadPolicy
from apps.dataset.infrastructure.adapters import DjangoDatasetFileStorage

# Legacy constants retained as policy-backed aliases.
ALLOWED_EXTENSIONS = DatasetUploadPolicy.ALLOWED_EXTENSIONS
MAX_FILE_SIZE = DatasetUploadPolicy.MAX_FILE_SIZE_BYTES / (1024 * 1024)


class FileService:
    @staticmethod
    def validate(file) -> None:
        DatasetUploadPolicy.validate(file.name, file.size)

    @staticmethod
    def save(file, user_id: int) -> str:
        content = b"".join(file.chunks())
        return DjangoDatasetFileStorage().store(file.name, content, user_id)

    @staticmethod
    def delete(file_path: str) -> None:
        DjangoDatasetFileStorage().delete(file_path)
