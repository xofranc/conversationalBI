from dataclasses import replace

import pytest

from apps.dataset.application.dtos import (
    CreateDatasetInput,
    DeleteDatasetInput,
    GetDatasetInput,
    ListDatasetsInput,
    ProcessDatasetInput,
)
from apps.dataset.application.use_cases import (
    CreateDataset,
    DatasetAccessDenied,
    DatasetNotFound,
    DeleteDataset,
    DatasetUploadRejected,
    GetDataset,
    ListDatasets,
    ProcessDataset,
)
from apps.dataset.domain.entities import Dataset, DatasetStatus, DatasetTable
from apps.dataset.domain.exceptions import DatasetOwnershipViolation


class DatasetMemory:
    def __init__(self, initial=()):
        self.items = {item.id: item for item in initial if item.id is not None}
        self.next_id = max(self.items, default=0) + 1

    def get_by_id(self, dataset_id):
        return self.items.get(dataset_id)

    def list_by_user(self, user_id):
        return tuple(item for item in self.items.values() if item.user_id == user_id)

    def save(self, item):
        if item.id is None:
            item = replace(item, id=self.next_id)
            self.next_id += 1
        self.items[item.id] = item
        return item

    def delete(self, dataset_id):
        self.items.pop(dataset_id, None)


class TableMemory:
    def __init__(self):
        self.items = {}
        self.next_id = 1

    def list_by_dataset(self, dataset_id):
        return tuple(item for item in self.items.values() if item.dataset_id == dataset_id)

    def save(self, item):
        key = (item.dataset_id, item.table_name)
        existing = self.items.get(key)
        saved = replace(item, id=existing.id if existing else self.next_id)
        if existing is None:
            self.next_id += 1
        self.items[key] = saved
        return saved


class FileStorage:
    def __init__(self, fail_store=False):
        self.fail_store = fail_store
        self.deleted = []

    def validate(self, filename, size):
        if not filename.endswith(".csv"):
            raise ValueError("Formato no soportado")
        if size == 0:
            raise ValueError("Archivo vacío")

    def store(self, filename, content, user_id):
        if self.fail_store:
            raise OSError("disk full")
        return f"users/{user_id}/{filename}"

    def delete(self, path):
        self.deleted.append(path)


class Materializer:
    def __init__(self, fail=False):
        self.fail = fail
        self.calls = []
        self.deleted = []

    def materialize(self, dataset_id, file_path):
        self.calls.append((dataset_id, file_path))
        if self.fail:
            raise RuntimeError("cannot materialize")
        return f"db/{dataset_id}"

    def delete(self, path):
        self.deleted.append(path)


class ResourceCleanupMemory:
    def __init__(self, datasets):
        self.datasets = datasets
        self.calls = []

    def delete(self, dataset_id, user_id):
        self.calls.append((dataset_id, user_id))
        self.datasets.delete(dataset_id)


class SchemaExtractor:
    def __init__(self, schema=None, fail=False):
        self.schema = schema or {"tables": [{"name": "orders", "row_count": 3, "columns": [{"name": "id"}, {"name": "amount"}]}]}
        self.fail = fail

    def extract(self, path):
        if self.fail:
            raise ValueError("bad schema")
        return self.schema


def test_process_dataset_materializes_extracts_tables_and_marks_ready():
    datasets = DatasetMemory([Dataset(id=5, user_id=2, name="orders", file_path="orders.csv")])
    tables = TableMemory()
    materializer = Materializer()
    use_case = ProcessDataset(datasets, tables, materializer, SchemaExtractor())

    result = use_case.execute(ProcessDatasetInput(dataset_id=5, user_id=2))

    assert (result.status, result.row_count, result.column_count) == ("ready", 3, 2)
    assert result.tables[0].table_name == "orders"
    assert datasets.get_by_id(5).db_path == "db/5"
    assert materializer.calls == [(5, "orders.csv")]


@pytest.mark.parametrize("failure", ["missing", "owner"])
def test_process_dataset_rejects_missing_or_non_owned_dataset_before_io(failure):
    datasets = DatasetMemory([] if failure == "missing" else [Dataset(id=5, user_id=9, name="x", file_path="x.csv")])
    materializer = Materializer()
    use_case = ProcessDataset(datasets, TableMemory(), materializer, SchemaExtractor())
    expected = DatasetNotFound if failure == "missing" else DatasetAccessDenied
    with pytest.raises(expected):
        use_case.execute(ProcessDatasetInput(dataset_id=5, user_id=2))
    assert not materializer.calls


def test_process_dataset_marks_error_and_reraises_schema_failure():
    datasets = DatasetMemory([Dataset(id=5, user_id=2, name="orders", file_path="orders.csv")])
    use_case = ProcessDataset(datasets, TableMemory(), Materializer(), SchemaExtractor(fail=True))
    with pytest.raises(ValueError, match="bad schema"):
        use_case.execute(ProcessDatasetInput(dataset_id=5, user_id=2))
    assert datasets.get_by_id(5).status is DatasetStatus.ERROR
    assert datasets.get_by_id(5).error_msg == "bad schema"


def test_process_dataset_marks_materializer_failure_without_schema_calls():
    datasets = DatasetMemory([Dataset(id=5, user_id=2, name="orders", file_path="orders.csv")])
    materializer = Materializer(fail=True)
    use_case = ProcessDataset(datasets, TableMemory(), materializer, SchemaExtractor())
    with pytest.raises(RuntimeError, match="cannot materialize"):
        use_case.execute(ProcessDatasetInput(dataset_id=5, user_id=2))
    assert datasets.get_by_id(5).status is DatasetStatus.ERROR
    assert datasets.get_by_id(5).error_msg == "cannot materialize"
    assert len(materializer.calls) == 1


def test_create_dataset_validates_stores_and_delegates_processing():
    datasets = DatasetMemory()
    storage = FileStorage()
    seen = []

    class ProcessSpy:
        def execute(self, request):
            seen.append(request)
            return type("DatasetResponse", (), {"id": request.dataset_id, "status": "ready"})()

    result = CreateDataset(datasets, storage, ProcessSpy()).execute(
        CreateDatasetInput(user_id=2, name="orders", filename="orders.csv", content=b"id\n1", description="daily")
    )
    assert (result.id, result.status) == (1, "ready")
    assert seen[0].dataset_id == 1 and seen[0].user_id == 2
    saved = datasets.get_by_id(1)
    assert (saved.file_path, saved.file_size, saved.description) == ("users/2/orders.csv", 4, "daily")


def test_create_dataset_validation_and_storage_failures_have_distinct_persistence():
    datasets = DatasetMemory()
    storage = FileStorage(fail_store=True)
    use_case = CreateDataset(datasets, storage, object())
    with pytest.raises(DatasetUploadRejected, match="Extensión de archivo no soportada"):
        use_case.execute(CreateDatasetInput(2, "invalid", "invalid.txt", b"data"))
    assert not datasets.items

    with pytest.raises(OSError, match="disk full"):
        use_case.execute(CreateDatasetInput(2, "orders", "orders.csv", b"data"))
    saved = datasets.get_by_id(1)
    assert saved.status is DatasetStatus.ERROR and saved.error_msg == "disk full"


def test_create_dataset_requires_repository_assigned_identity():
    class NoIdentityRepository(DatasetMemory):
        def save(self, item):
            return item

    class NeverCalled:
        def execute(self, request):
            raise AssertionError("processing should not start without a persistent id")

    with pytest.raises(RuntimeError, match="asignar identidad"):
        CreateDataset(NoIdentityRepository(), FileStorage(), NeverCalled()).execute(
            CreateDatasetInput(2, "orders", "orders.csv", b"id\n1")
        )


def test_list_get_and_delete_apply_user_scope_and_delegate_resource_cleanup():
    dataset = Dataset(id=3, user_id=2, name="orders", file_path="orders.csv", db_path="db/3")
    datasets = DatasetMemory([dataset])
    tables = TableMemory()
    resource_cleanup = ResourceCleanupMemory(datasets)
    tables.save(DatasetTable(dataset_id=3, table_name="orders"))
    assert ListDatasets(datasets).execute(ListDatasetsInput(2))[0].id == 3
    assert GetDataset(datasets, tables).execute(GetDatasetInput(2, 3)).tables[0].table_name == "orders"
    with pytest.raises(DatasetAccessDenied):
        GetDataset(datasets, tables).execute(GetDatasetInput(8, 3))
    with pytest.raises(DatasetNotFound):
        GetDataset(datasets, tables).execute(GetDatasetInput(2, 999))
    with pytest.raises(DatasetAccessDenied):
        DeleteDataset(datasets, resource_cleanup).execute(DeleteDatasetInput(8, 3))
    assert resource_cleanup.calls == []

    DeleteDataset(datasets, resource_cleanup).execute(DeleteDatasetInput(2, 3))
    assert resource_cleanup.calls == [(3, 2)]
    assert datasets.get_by_id(3) is None
    with pytest.raises(DatasetNotFound):
        DeleteDataset(datasets, resource_cleanup).execute(DeleteDatasetInput(2, 3))
    assert resource_cleanup.calls == [(3, 2)]


def test_delete_dataset_translates_cleanup_ownership_race_and_preserves_message():
    datasets = DatasetMemory([Dataset(id=3, user_id=2, name="orders", file_path="orders.csv")])
    message = "ownership changed during cleanup"

    class OwnershipRaceCleanup:
        def delete(self, dataset_id, user_id):
            raise DatasetOwnershipViolation(message)

    with pytest.raises(DatasetAccessDenied) as error:
        DeleteDataset(datasets, OwnershipRaceCleanup()).execute(DeleteDatasetInput(2, 3))

    assert str(error.value) == message
