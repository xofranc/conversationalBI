---
type: Model
language: python
source: "backend/apps/dataset/models.py"
tags: [model, dataset, datasettable]
date: 2026-07-24T09:37:21.360102
---

# dataset/models.py

## Used By

- [[datasetDetail.py]]
- [[datasetList.py]]
- [[datasetTable.py]]
- [[dataset_service.py]]
- [[dataset/views.py]]

## Source

`backend/apps/dataset/models.py`

```mermaid
graph TD
  dataset_models_py["dataset/models.py"]
  datasetDetail_py["datasetDetail.py"]
  datasetDetail_py --> dataset_models_py
  datasetList_py["datasetList.py"]
  datasetList_py --> dataset_models_py
  datasetTable_py["datasetTable.py"]
  datasetTable_py --> dataset_models_py
  dataset_service_py["dataset_service.py"]
  dataset_service_py --> dataset_models_py
  dataset_views_py["dataset/views.py"]
  dataset_views_py --> dataset_models_py
```

---
*Community: 2*