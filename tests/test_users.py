async def test_create_user(client):
    response = await client.post("/users", json={"email": "a@example.com"})

    assert response.status_code == 201
    assert response.json()["email"] == "a@example.com"


async def test_create_user_duplicate_email(client):
    await client.post("/users", json={"email": "a@example.com"})
    response = await client.post("/users", json={"email": "a@example.com"})

    assert response.status_code == 409


async def test_get_user(client):
    created = await client.post("/users", json={"email": "a@example.com"})
    user_id = created.json()["id"]

    response = await client.get(f"/users/{user_id}")

    assert response.status_code == 200
    assert response.json()["id"] == user_id


async def test_get_user_not_found(client):
    response = await client.get("/users/999")

    assert response.status_code == 404
