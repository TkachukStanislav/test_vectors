async def test_create_job_queues_processing(client, user_id, queued_jobs):
    response = await client.post("/jobs", json={"payload": "hello", "user_id": user_id})

    assert response.status_code == 201
    job = response.json()
    assert job["status"] == "pending"
    assert queued_jobs.calls == [(job["id"],)]


async def test_create_job_unknown_user(client):
    response = await client.post("/jobs", json={"payload": "hello", "user_id": 999})

    assert response.status_code == 404


async def test_get_job_not_found(client):
    response = await client.get("/jobs/999")

    assert response.status_code == 404


async def test_get_job_is_cached(client, user_id, fake_redis):
    created = await client.post("/jobs", json={"payload": "hello", "user_id": user_id})
    job_id = created.json()["id"]

    await client.get(f"/jobs/{job_id}")

    assert await fake_redis.get(f"job:{job_id}") is not None


async def test_similar_jobs_closest_first(client, user_id):
    ids = {}
    for payload in ["hello", "xyz", "olleh"]:
        response = await client.post("/jobs", json={"payload": payload, "user_id": user_id})
        ids[payload] = response.json()["id"]

    response = await client.get(f"/jobs/{ids['hello']}/similar")

    assert [job["payload"] for job in response.json()] == ["olleh", "xyz"]


async def test_users_list_includes_jobs(client, user_id):
    for payload in ["a", "b"]:
        await client.post("/jobs", json={"payload": payload, "user_id": user_id})

    response = await client.get("/users")

    assert len(response.json()[0]["jobs"]) == 2
