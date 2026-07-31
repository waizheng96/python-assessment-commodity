def test_create_trader_success(client):
    resp = client.post(
        "/traders/",
        json={"name": "Alice", "email": "alice@example.com", "desk": "metals"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Alice"
    assert body["email"] == "alice@example.com"
    assert body["desk"] == "metals"
    assert body["active"] is True


def test_create_trader_duplicate_email_returns_400(client, make_trader):
    make_trader(email="dupe@example.com")
    resp = client.post(
        "/traders/",
        json={"name": "Bob", "email": "dupe@example.com", "desk": "energy"},
    )
    assert resp.status_code == 400


def test_create_trader_invalid_desk_returns_422(client):
    resp = client.post(
        "/traders/",
        json={"name": "Bob", "email": "bob@example.com", "desk": "not_a_real_desk"},
    )
    assert resp.status_code == 422


def test_list_traders(client, make_trader):
    make_trader(email="t1@example.com")
    make_trader(email="t2@example.com")
    resp = client.get("/traders/")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_get_trader_by_id(client, make_trader):
    trader = make_trader(email="findme@example.com")
    resp = client.get(f"/traders/{trader['id']}")
    assert resp.status_code == 200
    assert resp.json()["email"] == "findme@example.com"


def test_get_trader_not_found_returns_404(client):
    resp = client.get("/traders/999999")
    assert resp.status_code == 404


def test_update_trader_fields(client, make_trader):
    trader = make_trader(email="update@example.com")
    resp = client.put(f"/traders/{trader['id']}", json={"name": "New Name"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"
    assert resp.json()["email"] == "update@example.com"


def test_update_trader_desk_blocked_with_nonempty_watchlist(client, make_trader, seed_commodities):
    trader = make_trader(email="deskchange@example.com", desk="metals")
    commodity_id = seed_commodities[0].id

    add_resp = client.post(
        "/watchlist/",
        json={"commodity_id": commodity_id},
        headers={"X-Trader-Id": str(trader["id"])},
    )
    assert add_resp.status_code == 201

    resp = client.put(f"/traders/{trader['id']}", json={"desk": "energy"})
    assert resp.status_code == 400
    assert "watchlist" in resp.json()["detail"].lower()


def test_update_trader_desk_allowed_with_empty_watchlist(client, make_trader):
    trader = make_trader(email="deskchangeok@example.com", desk="metals")
    resp = client.put(f"/traders/{trader['id']}", json={"desk": "energy"})
    assert resp.status_code == 200
    assert resp.json()["desk"] == "energy"


def test_delete_trader_returns_405(client, make_trader):
    trader = make_trader(email="nodelete@example.com")
    resp = client.delete(f"/traders/{trader['id']}")
    assert resp.status_code == 405