### Documentación del Archivo de Pruebas: test_views.py

Este archivo contiene pruebas unitarias para las vistas de la aplicación `dataset` en un proyecto Django. Utiliza `pytest` y `Django REST Framework` para probar endpoints de API relacionados con datasets. Las pruebas verifican autenticación, permisos de usuario y operaciones CRUD (crear, leer, eliminar) sobre datasets.

#### Clases de Prueba y Métodos

**`TestDatasetList`**  
Prueba el endpoint de lista de datasets (`GET /api/v1/dataset/`).

- `test_lista_solo_datasets_del_usuario`: Verifica que solo se devuelvan los datasets del usuario autenticado, no los de otros usuarios.
- `test_requiere_autenticacion`: Confirma que el endpoint requiere autenticación (retorna 401 sin login).

**`TestDatasetRetrieve`**  
Prueba el endpoint de detalle de dataset (`GET /api/v1/dataset/{id}/`).

- `test_propietario_puede_ver_detalle`: El propietario puede ver los detalles de su dataset (retorna 200).
- `test_otro_usuario_no_puede_ver_detalle`: Otros usuarios no pueden ver detalles de datasets ajenos (retorna 404).

**`TestDatasetUpload`**  
Prueba el endpoint de subida de datasets (`POST /api/v1/dataset/`).

- `test_upload_exitoso`: Simula una subida exitosa con archivo y nombre (retorna 201, usa mock para `DatasetService.create`).
- `test_upload_sin_archivo_retorna_400`: Sin archivo, retorna error 400.
- `test_upload_sin_autenticacion_retorna_401`: Sin autenticación, retorna 401.

**`TestDatasetDestroy`**  
Prueba el endpoint de eliminación de datasets (`DELETE /api/v1/dataset/{id}/`).

- `test_propietario_puede_eliminar`: El propietario puede eliminar su dataset (retorna 204, usa mock para `DatasetService.delete`).
- `test_otro_usuario_no_puede_eliminar`: Otros usuarios no pueden eliminar datasets ajenos (retorna 404).

**`TestDatasetSchema`**  
Prueba el endpoint de esquema de dataset (`GET /api/v1/dataset/{id}/schema/`).

- `test_retorna_schema_json`: Verifica que se devuelva el `schema_json` y el `id` del dataset (retorna 200).

#### Fixtures Utilizadas

- `user`: Crea un usuario de prueba.
- `other_user`: Crea otro usuario para pruebas de permisos.
- `client`: Cliente API autenticado con el usuario.
- `dataset`: Crea un dataset de prueba asociado al usuario.

Las pruebas usan `pytest.mark.django_db` para manejar la base de datos y mocks para servicios externos. Aseguran que las vistas respeten permisos y autenticación.
