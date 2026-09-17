from fastapi.testclient import TestClient
import pytest
 
from app.main import app
from app.database import categories_db
 
client = TestClient(app)
 
INITIAL_CATEGORIES = [
    {"id": 1, "name": "Computadores", "description": "Equipos de cómputo", "active": True},
    {"id": 2, "name": "Perifericos", "description": "Mouse, teclados y accesorios", "active": True},
]
 
 
@pytest.fixture(autouse=True)
def reset_categories_db():
    """Restablece categories_db a su estado inicial antes de cada prueba."""
    categories_db.clear()
    categories_db.extend([c.copy() for c in INITIAL_CATEGORIES])
 
 
# ---------------------------------------------------------------------------
# CA01 - Listar categorías -> GET /categories -> 200 y lista JSON
# ---------------------------------------------------------------------------
 
def test_ca01_listar_categorias():
    response = client.get("/categories")
 
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["name"] == "Computadores"
 
 
# ---------------------------------------------------------------------------
# CA02 - Consultar existente -> GET /categories/1 -> 200
# ---------------------------------------------------------------------------
 
def test_ca02_consultar_existente():
    response = client.get("/categories/1")
 
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Computadores"
    assert data["active"] is True
 
 
# ---------------------------------------------------------------------------
# CA03 - Consultar inexistente -> GET /categories/999 -> 404
# ---------------------------------------------------------------------------
 
def test_ca03_consultar_inexistente():
    response = client.get("/categories/999")
 
    assert response.status_code == 404
    assert response.json() == {"detail": "Category not found"}
 
 
# ---------------------------------------------------------------------------
# CA04 - ID inválido -> GET /categories/abc -> 422
# ---------------------------------------------------------------------------
 
def test_ca04_id_invalido():
    response = client.get("/categories/abc")
 
    assert response.status_code == 422
    assert "detail" in response.json()
 
 
# ---------------------------------------------------------------------------
# CA05 - Crear válida -> POST con datos correctos -> 201
# ---------------------------------------------------------------------------
 
def test_ca05_crear_valida():
    new_category = {
        "name": "Impresoras",
        "description": "Impresoras y consumibles",
        "active": True,
    }
 
    response = client.post("/categories", json=new_category)
 
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == new_category["name"]
    assert data["description"] == new_category["description"]
    assert data["active"] == new_category["active"]
    assert "id" in data
 
 
# ---------------------------------------------------------------------------
# CA06 - Nombre demasiado corto -> POST con name de 1-2 caracteres -> 422
# ---------------------------------------------------------------------------
 
def test_ca06_nombre_demasiado_corto():
    response = client.post("/categories", json={"name": "PC"})  # 2 caracteres
 
    assert response.status_code == 422
    assert "detail" in response.json()
 
 
# ---------------------------------------------------------------------------
# CA07 - Falta nombre -> POST sin name -> 422
# ---------------------------------------------------------------------------
 
def test_ca07_falta_nombre():
    response = client.post("/categories", json={"description": "Sin nombre"})
 
    assert response.status_code == 422
    assert "detail" in response.json()
 
 
# ---------------------------------------------------------------------------
# CA08 - Actualizar existente -> PATCH /categories/1 -> 200
# ---------------------------------------------------------------------------
 
def test_ca08_actualizar_existente():
    response = client.patch("/categories/1", json={"name": "Portatiles"})
 
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Portatiles"
    # Los campos no enviados deben conservarse (actualización parcial)
    assert data["description"] == "Equipos de cómputo"
    assert data["active"] is True
 
 
# ---------------------------------------------------------------------------
# CA09 - Actualizar inexistente -> PATCH /categories/999 -> 404
# ---------------------------------------------------------------------------
 
def test_ca09_actualizar_inexistente():
    response = client.patch("/categories/999", json={"name": "No existe"})
 
    assert response.status_code == 404
    assert response.json() == {"detail": "Category not found"}
 
 
# ---------------------------------------------------------------------------
# CA10 - Eliminar existente -> DELETE /categories/1 -> 204
# ---------------------------------------------------------------------------
 
def test_ca10_eliminar_existente():
    response = client.delete("/categories/1")
 
    assert response.status_code == 204
    assert response.content == b""  # 204 no debe traer cuerpo
 
    # Verificamos que efectivamente ya no existe
    get_response = client.get("/categories/1")
    assert get_response.status_code == 404
 
 
# ---------------------------------------------------------------------------
# CA11 - Eliminar inexistente -> DELETE /categories/999 -> 404
# ---------------------------------------------------------------------------
 
def test_ca11_eliminar_inexistente():
    response = client.delete("/categories/999")
 
    assert response.status_code == 404
    assert response.json() == {"detail": "Category not found"}
 
 
# ---------------------------------------------------------------------------
# CA12 - Filtrar activas -> GET /categories?active=true -> 200 y solo active=true
# ---------------------------------------------------------------------------
 
def test_ca12_filtrar_activas():
    # Desactivamos una categoría para tener un escenario mixto
    categories_db[1]["active"] = False
 
    response = client.get("/categories?active=true")
 
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert all(category["active"] is True for category in data)
 
 
# ---------------------------------------------------------------------------
# Pruebas adicionales de robustez (no exigidas por la matriz, pero
# recomendadas para reforzar la cobertura de reglas de negocio)
# ---------------------------------------------------------------------------
 
def test_filtrar_inactivas():
    categories_db[1]["active"] = False
 
    response = client.get("/categories?active=false")
 
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert all(category["active"] is False for category in data)
 
 
def test_crear_categoria_active_por_defecto_true():
    # active es opcional; su valor por defecto debe ser True
    response = client.post("/categories", json={"name": "Monitores"})
 
    assert response.status_code == 201
    data = response.json()
    assert data["active"] is True
    assert data["description"] is None
 
 
def test_crear_categoria_ignora_id_enviado_por_cliente():
    # El id es generado por la aplicación; el cliente no debe poder definirlo
    response = client.post("/categories", json={"id": 999, "name": "Accesorios"})
 
    assert response.status_code == 201
    data = response.json()
    assert data["id"] != 999
 
 
def test_crear_categoria_nombre_demasiado_largo():
    response = client.post("/categories", json={"name": "A" * 51})  # 51 caracteres
 
    assert response.status_code == 422
 
 
def test_crear_categoria_descripcion_demasiado_larga():
    response = client.post(
        "/categories",
        json={"name": "Categoria valida", "description": "A" * 201},  # 201 caracteres
    )
 
    assert response.status_code == 422
 
 
def test_actualizar_categoria_active_parcial():
    response = client.patch("/categories/1", json={"active": False})
 
    assert response.status_code == 200
    assert response.json()["active"] is False
 
 
def test_actualizar_categoria_nombre_invalido():
    response = client.patch("/categories/1", json={"name": "AB"})  # muy corto
 
    assert response.status_code == 422
 