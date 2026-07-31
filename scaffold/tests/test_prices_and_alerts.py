from datetime import datetime, timedelta


def _commodity_by_desk(seed_commodities, desk):
    match = next((c for c in seed_commodities if c.desk == desk), None)
    assert match is not None, f"seed_commodities fixture must include a {desk} commodity"
    return match


def test_record_price_snapshot_success(client, seed_commodities):
    commodity = _commodity_by_desk(seed_commodities, "metals")
    resp = client.post(
        f"/commodities/{commodity.id}/prices",
        json={
            "price": "100.50",
            "captured_at": datetime(2026, 1, 1, 12, 0, 0).isoformat(),
            "source": "test-feed",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["source"] == "test-feed"


def test_record_price_rejects_non_positive_price(client, seed_commodities):
    commodity = _commodity_by_desk(seed_commodities, "metals")
    resp = client.post(
        f"/commodities/{commodity.id}/prices",
        json={
            "price": "-5",
            "captured_at": datetime(2026, 1, 1).isoformat(),
            "source": "test-feed",
        },
    )
    assert resp.status_code in (400, 422)


def test_record_price_rejects_out_of_order_captured_at(client, seed_commodities):
    commodity = _commodity_by_desk(seed_commodities, "metals")
    first = client.post(
        f"/commodities/{commodity.id}/prices",
        json={
            "price": "100",
            "captured_at": datetime(2026, 1, 10).isoformat(),
            "source": "test-feed",
        },
    )
    assert first.status_code == 201

    second = client.post(
        f"/commodities/{commodity.id}/prices",
        json={
            "price": "101",
            "captured_at": datetime(2026, 1, 5).isoformat(),
            "source": "test-feed",
        },
    )
    assert second.status_code == 400


def test_metals_desk_alert_uses_1_5_pct_threshold(client, seed_commodities):
    """FR-4.1 — metals/agriculture desks use a 1.5% threshold."""
    commodity = _commodity_by_desk(seed_commodities, "metals")
    base_time = datetime(2026, 2, 1)

    client.post(
        f"/commodities/{commodity.id}/prices",
        json={"price": "100", "captured_at": base_time.isoformat(), "source": "test"},
    )
    resp = client.post(
        f"/commodities/{commodity.id}/prices",
        json={
            "price": "102",
            "captured_at": (base_time + timedelta(days=1)).isoformat(),
            "source": "test",
        },
    )
    assert resp.status_code == 201

    alerts = client.get(f"/alerts/?commodity_id={commodity.id}").json()
    assert len(alerts) == 1
    assert float(alerts[0]["threshold_used"]) == 1.5
    assert alerts[0]["threshold_breached"] is True


def test_metals_desk_small_move_does_not_trigger_alert(client, seed_commodities):
    commodity = _commodity_by_desk(seed_commodities, "metals")
    base_time = datetime(2026, 2, 1)

    client.post(
        f"/commodities/{commodity.id}/prices",
        json={"price": "100", "captured_at": base_time.isoformat(), "source": "test"},
    )
    client.post(
        f"/commodities/{commodity.id}/prices",
        json={
            "price": "100.50",
            "captured_at": (base_time + timedelta(days=1)).isoformat(),
            "source": "test",
        },
    )

    alerts = client.get(f"/alerts/?commodity_id={commodity.id}").json()
    assert len(alerts) == 0


def test_energy_desk_alert_uses_3_pct_threshold(client, seed_commodities):
    """FR-4.1 — the energy desk uses a 3% threshold, not 1.5%."""
    commodity = _commodity_by_desk(seed_commodities, "energy")
    base_time = datetime(2026, 2, 1)

    client.post(
        f"/commodities/{commodity.id}/prices",
        json={"price": "100", "captured_at": base_time.isoformat(), "source": "test"},
    )
    resp = client.post(
        f"/commodities/{commodity.id}/prices",
        json={
            "price": "102",
            "captured_at": (base_time + timedelta(days=1)).isoformat(),
            "source": "test",
        },
    )
    assert resp.status_code == 201
    alerts = client.get(f"/alerts/?commodity_id={commodity.id}").json()
    assert len(alerts) == 0, "a 2% move on the energy desk should not breach the 3% threshold"

    client.post(
        f"/commodities/{commodity.id}/prices",
        json={
            "price": "106.08",
            "captured_at": (base_time + timedelta(days=2)).isoformat(),
            "source": "test",
        },
    )
    alerts = client.get(f"/alerts/?commodity_id={commodity.id}").json()
    assert len(alerts) == 1
    assert float(alerts[0]["threshold_used"]) == 3.0


def test_first_snapshot_for_commodity_never_creates_alert(client, seed_commodities):
    commodity = _commodity_by_desk(seed_commodities, "metals")
    client.post(
        f"/commodities/{commodity.id}/prices",
        json={
            "price": "999",
            "captured_at": datetime(2026, 3, 1).isoformat(),
            "source": "test",
        },
    )
    alerts = client.get(f"/alerts/?commodity_id={commodity.id}").json()
    assert len(alerts) == 0


def test_list_price_history_most_recent_first(client, seed_commodities):
    commodity = _commodity_by_desk(seed_commodities, "metals")
    base_time = datetime(2026, 4, 1)
    for i in range(3):
        client.post(
            f"/commodities/{commodity.id}/prices",
            json={
                "price": str(100 + i),
                "captured_at": (base_time + timedelta(days=i)).isoformat(),
                "source": "test",
            },
        )

    resp = client.get(f"/commodities/{commodity.id}/prices")
    assert resp.status_code == 200
    prices = resp.json()
    captured_ats = [p["captured_at"] for p in prices]
    assert captured_ats == sorted(captured_ats, reverse=True)


def test_get_single_commodity(client, seed_commodities):
    commodity = seed_commodities[0]
    resp = client.get(f"/commodities/{commodity.id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == commodity.id
    assert resp.json()["symbol"] == commodity.symbol


def test_get_single_commodity_not_found(client):
    resp = client.get("/commodities/999999")
    assert resp.status_code == 404