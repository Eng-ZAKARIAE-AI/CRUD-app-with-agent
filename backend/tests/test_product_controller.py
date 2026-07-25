"""Integration tests for Product API Controller endpoints."""

def test_create_product(client):
    """Test creating a valid product via HTTP POST."""
    payload = {
        "name": "Gaming Mouse",
        "sku": "GM-999",
        "price": 49.99,
        "description": "RGB high precision mouse",
        "stock_quantity": 100,
        "is_active": True,
    }
    response = client.post("/products/", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["sku"] == payload["sku"]
    assert float(data["price"]) == payload["price"]
    assert "id" in data


def test_create_duplicate_sku_returns_409(client):
    """Test creating a product with an existing SKU raises 409 Conflict."""
    payload = {
        "name": "Keyboard",
        "sku": "KB-100",
        "price": 89.00,
        "stock_quantity": 10,
    }
    # First creation
    client.post("/products/", json=payload)
    
    # Second creation with same SKU
    response = client.post("/products/", json=payload)
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_list_products(client):
    """Test listing products with pagination."""
    # Create two items
    client.post("/products/", json={"name": "P1", "sku": "SKU1", "price": 10.0})
    client.post("/products/", json={"name": "P2", "sku": "SKU2", "price": 20.0})

    response = client.get("/products/?skip=0&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_product_by_id(client):
    """Test retrieving a product by ID."""
    created = client.post("/products/", json={"name": "Monitor", "sku": "MON-1", "price": 199.99}).json()
    product_id = created["id"]

    response = client.get(f"/products/{product_id}")
    assert response.status_code == 200
    assert response.json()["sku"] == "MON-1"


def test_update_product(client):
    """Test partial update via PATCH."""
    created = client.post("/products/", json={"name": "Laptop", "sku": "LAP-1", "price": 999.99}).json()
    product_id = created["id"]

    patch_payload = {"price": 899.99, "stock_quantity": 5}
    response = client.patch(f"/products/{product_id}", json=patch_payload)
    
    assert response.status_code == 200
    assert float(response.json()["price"]) == 899.99
    assert response.json()["stock_quantity"] == 5


def test_delete_product_soft(client):
    """Test soft deleting a product (is_active = False)."""
    created = client.post("/products/", json={"name": "Desk", "sku": "DSK-1", "price": 150.0}).json()
    product_id = created["id"]

    # Perform soft delete
    delete_res = client.delete(f"/products/{product_id}?soft=true")
    assert delete_res.status_code == 204

    # Verify product is now inactive
    get_res = client.get(f"/products/{product_id}")
    assert get_res.status_code == 200
    assert get_res.json()["is_active"] is False