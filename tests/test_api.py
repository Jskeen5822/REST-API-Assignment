from fastapi.testclient import TestClient

from app.main import app, reset_state


def get_client() -> TestClient:
    return TestClient(app)


def setup_function() -> None:
    reset_state()


def teardown_function() -> None:
    reset_state()


def test_inventory_crud_flow() -> None:
    with get_client() as client:
        create_resp = client.post(
            "/inventory",
            json={"name": "Widget", "quantity": 10, "price": 12.5},
        )
        assert create_resp.status_code == 201
        item = create_resp.json()

        list_resp = client.get("/inventory")
        assert list_resp.status_code == 200
        assert any(entry["id"] == item["id"] for entry in list_resp.json())

        put_resp = client.put(
            f"/inventory/{item['id']}",
            json={"name": "Widget", "quantity": 25, "price": 11.0},
        )
        assert put_resp.status_code == 200
        assert put_resp.json()["quantity"] == 25

        patch_resp = client.patch(
            f"/inventory/{item['id']}",
            json={"price": 9.99},
        )
        assert patch_resp.status_code == 200
        assert patch_resp.json()["price"] == 9.99

        delete_resp = client.delete(f"/inventory/{item['id']}")
        assert delete_resp.status_code == 204

        list_after_delete = client.get("/inventory")
        assert list_after_delete.status_code == 200
        assert item["id"] not in {entry["id"] for entry in list_after_delete.json()}


def test_order_crud_flow() -> None:
    with get_client() as client:
        first_item = client.post(
            "/inventory",
            json={"name": "Gear", "quantity": 5, "price": 20.0},
        ).json()
        second_item = client.post(
            "/inventory",
            json={"name": "Bolt", "quantity": 50, "price": 1.5},
        ).json()

        create_resp = client.post(
            "/orders",
            json={
                "customer": "Ada Lovelace",
                "items": [first_item["id"], second_item["id"]],
                "status": "pending",
            },
        )
        assert create_resp.status_code == 201
        order = create_resp.json()
        assert order["customer"] == "Ada Lovelace"
        assert len(order["items"]) == 2

        read_resp = client.get(f"/orders/{order['id']}")
        assert read_resp.status_code == 200
        assert read_resp.json()["id"] == order["id"]

        put_resp = client.put(
            f"/orders/{order['id']}",
            json={
                "customer": "Ada Lovelace",
                "items": [second_item["id"]],
                "status": "confirmed",
            },
        )
        assert put_resp.status_code == 200
        assert put_resp.json()["status"] == "confirmed"

        patch_resp = client.patch(
            f"/orders/{order['id']}",
            json={"status": "shipped"},
        )
        assert patch_resp.status_code == 200
        assert patch_resp.json()["status"] == "shipped"

        delete_resp = client.delete(f"/orders/{order['id']}")
        assert delete_resp.status_code == 204

        not_found_resp = client.get(f"/orders/{order['id']}")
        assert not_found_resp.status_code == 404
