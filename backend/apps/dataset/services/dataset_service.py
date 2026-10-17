"""Compatibility facade for dataset application use cases."""

from apps.dataset.application.dtos import (
    CreateDatasetInput,
    DeleteDatasetInput,
)


def _dataset_use_cases():
    from config.composition import build_dataset_use_cases

    return build_dataset_use_cases()


class DatasetService:
    @staticmethod
    def create(file, user, name: str, description: str = ""):
        file.seek(0)
        content = file.read()
        file.seek(0)
        return _dataset_use_cases()["create"].execute(CreateDatasetInput(
            user_id=user.pk,
            name=name,
            filename=file.name,
            content=content,
            description=description,
        ))
    
    @staticmethod
    def delete(dataset_id: int, user) -> None:
        _dataset_use_cases()["delete"].execute(DeleteDatasetInput(
            user_id=user.pk,
            dataset_id=dataset_id,
        ))
