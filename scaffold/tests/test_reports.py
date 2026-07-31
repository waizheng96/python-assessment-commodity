from datetime import datetime, timedelta


def test_report_rejected_with_empty_watchlist(client, make_trader):
    trader = make_trader(email="emptywatchlist@example.com")
    resp = client.post(
        "/reports/",
        json={"date_from": "2026-01-01", "date_to": "2026-01-31"},
        headers={"X-Trader-Id": str(trader["id"])},
    )
    assert resp.status_code == 400
    assert "watchlist" in resp.json()["detail"].lower()


def test_report_generated_for_watchlisted_commodity(client, make_trader, seed_commodities):
    trader = make_trader(email="reportgen@example.com")
    headers = {"X-Trader-Id": str(trader["id"])}
    commodity = seed_commodities[0]

    client.post("/watchlist/", json={"commodity_id": commodity.id}, headers=headers)

    base_time = datetime(2026, 1, 1)
    for i in range(6):
        client.post(
            f"/commodities/{commodity.id}/prices",
            json={
                "price": str(100 + i),
                "captured_at": (base_time + timedelta(days=i)).isoformat(),
                "source": "test",
            },
        )

    resp = client.post(
        "/reports/",
        json={"date_from": "2026-01-01", "date_to": "2026-01-10"},
        headers=headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["trader_id"] == trader["id"]
    assert body["row_count"] == 6
    assert body["filename"].endswith(".xlsx")


def test_report_download_returns_file(client, make_trader, seed_commodities):
    trader = make_trader(email="reportdownload@example.com")
    headers = {"X-Trader-Id": str(trader["id"])}
    commodity = seed_commodities[0]

    client.post("/watchlist/", json={"commodity_id": commodity.id}, headers=headers)
    client.post(
        f"/commodities/{commodity.id}/prices",
        json={
            "price": "100",
            "captured_at": datetime(2026, 1, 1).isoformat(),
            "source": "test",
        },
    )

    gen_resp = client.post(
        "/reports/",
        json={"date_from": "2026-01-01", "date_to": "2026-01-10"},
        headers=headers,
    )
    report_id = gen_resp.json()["id"]

    # download requires the SAME trader's X-Trader-Id header — reports.py
    # scopes GET /reports/{id}/download to the owning trader.
    download_resp = client.get(
        f"/reports/{report_id}/download", headers=headers
    )
    assert download_resp.status_code == 200
    assert (
        download_resp.headers["content-type"]
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def test_report_download_404_for_nonexistent_report(client, make_trader):
    trader = make_trader(email="nonexistentreport@example.com")
    resp = client.get(
        "/reports/999999/download", headers={"X-Trader-Id": str(trader["id"])}
    )
    assert resp.status_code == 404


def test_report_download_404_for_another_traders_report(client, make_trader, seed_commodities):
    """reports.py scopes download by trader_id — Trader B can't fetch Trader A's report."""
    trader_a = make_trader(email="reportowner@example.com")
    trader_b = make_trader(email="reportintruder@example.com")
    commodity = seed_commodities[0]

    client.post(
        "/watchlist/",
        json={"commodity_id": commodity.id},
        headers={"X-Trader-Id": str(trader_a["id"])},
    )
    client.post(
        f"/commodities/{commodity.id}/prices",
        json={
            "price": "100",
            "captured_at": datetime(2026, 1, 1).isoformat(),
            "source": "test",
        },
    )
    gen_resp = client.post(
        "/reports/",
        json={"date_from": "2026-01-01", "date_to": "2026-01-10"},
        headers={"X-Trader-Id": str(trader_a["id"])},
    )
    report_id = gen_resp.json()["id"]

    resp = client.get(
        f"/reports/{report_id}/download", headers={"X-Trader-Id": str(trader_b["id"])}
    )
    assert resp.status_code == 404


def test_report_covers_only_requesting_traders_watchlist(client, make_trader, seed_commodities):
    """Report scope must be the CALLER's watchlist, not an arbitrary commodity list."""
    trader_a = make_trader(email="reportA@example.com")
    trader_b = make_trader(email="reportB@example.com")
    commodity_a, commodity_b = seed_commodities[0], seed_commodities[1]

    client.post(
        "/watchlist/",
        json={"commodity_id": commodity_a.id},
        headers={"X-Trader-Id": str(trader_a["id"])},
    )
    client.post(
        "/watchlist/",
        json={"commodity_id": commodity_b.id},
        headers={"X-Trader-Id": str(trader_b["id"])},
    )

    for commodity in (commodity_a, commodity_b):
        client.post(
            f"/commodities/{commodity.id}/prices",
            json={
                "price": "100",
                "captured_at": datetime(2026, 1, 1).isoformat(),
                "source": "test",
            },
        )

    resp_a = client.post(
        "/reports/",
        json={"date_from": "2026-01-01", "date_to": "2026-01-31"},
        headers={"X-Trader-Id": str(trader_a["id"])},
    )
    assert resp_a.json()["row_count"] == 1


def test_list_reports_scoped_to_acting_trader(client, make_trader, seed_commodities):
    """GET /reports also scopes by trader — matches list_reports in reports.py."""
    trader_a = make_trader(email="listreportsA@example.com")
    trader_b = make_trader(email="listreportsB@example.com")
    commodity = seed_commodities[0]

    for trader in (trader_a, trader_b):
        client.post(
            "/watchlist/",
            json={"commodity_id": commodity.id},
            headers={"X-Trader-Id": str(trader["id"])},
        )
    client.post(
        f"/commodities/{commodity.id}/prices",
        json={
            "price": "100",
            "captured_at": datetime(2026, 1, 1).isoformat(),
            "source": "test",
        },
    )

    client.post(
        "/reports/",
        json={"date_from": "2026-01-01", "date_to": "2026-01-10"},
        headers={"X-Trader-Id": str(trader_a["id"])},
    )

    resp_a = client.get("/reports/", headers={"X-Trader-Id": str(trader_a["id"])})
    resp_b = client.get("/reports/", headers={"X-Trader-Id": str(trader_b["id"])})

    assert len(resp_a.json()) == 1
    assert len(resp_b.json()) == 0