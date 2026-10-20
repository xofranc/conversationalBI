from apps.dataset.domain.policies import DatasetUploadPolicy
from apps.dataset.services import file_service
from apps.dataset.services.file_service import FileService


def test_legacy_file_service_delegates_validation_to_canonical_upload_policy(monkeypatch):
    calls = []
    monkeypatch.setattr(
        DatasetUploadPolicy,
        "validate",
        lambda filename, size: calls.append((filename, size)),
    )
    uploaded = type("UploadedFile", (), {"name": "sales.csv", "size": 123})()

    FileService.validate(uploaded)

    assert calls == [("sales.csv", 123)]


def test_legacy_file_service_delegates_storage_without_duplicate_file_io(monkeypatch):
    class StorageFake:
        def __init__(self):
            self.stored = []
            self.deleted = []

        def store(self, filename, content, user_id):
            self.stored.append((filename, content, user_id))
            return "datasets/9/sales.csv"

        def delete(self, path):
            self.deleted.append(path)

    storage = StorageFake()
    monkeypatch.setattr(file_service, "DjangoDatasetFileStorage", lambda: storage)
    uploaded = type(
        "UploadedFile", (),
        {"name": "sales.csv", "chunks": lambda self: iter((b"sales,", b"total\n"))},
    )()

    path = FileService.save(uploaded, user_id=9)
    FileService.delete(path)

    assert path == "datasets/9/sales.csv"
    assert storage.stored == [("sales.csv", b"sales,total\n", 9)]
    assert storage.deleted == [path]
