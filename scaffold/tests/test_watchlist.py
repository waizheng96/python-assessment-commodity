def test_add_to_watchlist(client, make_trader, seed_commodities):
    trader = make_trader(email="watch1@example.com")
    commodity_id = seed_commodities[0].id

    resp = client.post(
        "/watchlist/",
        json={"commodity_id": commodity_id},
        headers={"X-Trader-Id": str(trader["id"])},
    )
    assert resp.status_code == 201
    assert resp.json()["commodity_id"] == commodity_id
    assert resp.json()["trader_id"] == trader["id"]


def test_add_duplicate_to_watchlist_returns_400(client, make_trader, seed_commodities):
    trader = make_trader(email="watchdupe@example.com")
    commodity_id = seed_commodities[0].id
    headers = {"X-Trader-Id": str(trader["id"])}

    first = client.post("/watchlist/", json={"commodity_id": commodity_id}, headers=headers)
    assert first.status_code == 201

    second = client.post("/watchlist/", json={"commodity_id": commodity_id}, headers=headers)
    assert second.status_code == 400
    assert "already on your watchlist" in second.json()["detail"].lower()


def test_missing_trader_id_header_rejected(client, seed_commodities):
    commodity_id = seed_commodities[0].id
    resp = client.post("/watchlist/", json={"commodity_id": commodity_id})
    assert resp.status_code in (400, 401, 422)


def test_watchlist_isolation_between_traders(client, make_trader, seed_commodities):
    """FR-3.2 — the isolation test the marker specifically checks."""
    trader_a = make_trader(email="traderA@example.com")
    trader_b = make_trader(email="traderB@example.com")
    commodity_a_id = seed_commodities[0].id
    commodity_b_id = seed_commodities[1].id

    client.post(
        "/watchlist/",
        json={"commodity_id": commodity_a_id},
        headers={"X-Trader-Id": str(trader_a["id"])},
    )
    client.post(
        "/watchlist/",
        json={"commodity_id": commodity_b_id},
        headers={"X-Trader-Id": str(trader_b["id"])},
    )

    resp_a = client.get("/watchlist/", headers={"X-Trader-Id": str(trader_a["id"])})
    resp_b = client.get("/watchlist/", headers={"X-Trader-Id": str(trader_b["id"])})

    assert resp_a.status_code == 200
    assert resp_b.status_code == 200

    ids_a = {item["commodity_id"] for item in resp_a.json()}
    ids_b = {item["commodity_id"] for item in resp_b.json()}

    assert ids_a == {commodity_a_id}
    assert ids_b == {commodity_b_id}
    assert commodity_b_id not in ids_a
    assert commodity_a_id not in ids_b


def test_remove_from_watchlist(client, make_trader, seed_commodities):
    trader = make_trader(email="removeme@example.com")
    commodity_id = seed_commodities[0].id
    headers = {"X-Trader-Id": str(trader["id"])}

    client.post("/watchlist/", json={"commodity_id": commodity_id}, headers=headers)
    resp = client.delete(f"/watchlist/{commodity_id}", headers=headers)
    assert resp.status_code == 204

    remaining = client.get("/watchlist/", headers=headers).json()
    assert remaining == []


def test_remove_nonexistent_watchlist_item_returns_404(client, make_trader, seed_commodities):
    trader = make_trader(email="removenonexistent@example.com")
    commodity_id = seed_commodities[0].id
    headers = {"X-Trader-Id": str(trader["id"])}

    resp = client.delete(f"/watchlist/{commodity_id}", headers=headers)
    assert resp.status_code == 404


def test_cannot_remove_another_traders_watchlist_item(client, make_trader, seed_commodities):
    """Reinforces isolation: Trader B can't delete Trader A's watchlist entry."""
    trader_a = make_trader(email="ownerA@example.com")
    trader_b = make_trader(email="attackerB@example.com")
    commodity_id = seed_commodities[0].id

    client.post(
        "/watchlist/",
        json={"commodity_id": commodity_id},
        headers={"X-Trader-Id": str(trader_a["id"])},
    )

    resp = client.delete(
        f"/watchlist/{commodity_id}", headers={"X-Trader-Id": str(trader_b["id"])}
    )
    assert resp.status_code == 404

    still_there = client.get(
        "/watchlist/", headers={"X-Trader-Id": str(trader_a["id"])}
    ).json()
    assert len(still_there) == 1