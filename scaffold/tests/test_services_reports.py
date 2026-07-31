from datetime import date
from decimal import Decimal

from app.routers.reports import (
    build_commodity_section,
    moving_average,
    pct_change,
)


def _d(x):
    return Decimal(str(x))


class TestMovingAverage:
    def test_returns_none_when_not_enough_history(self):
        prices = [_d(100), _d(102)]
        assert moving_average(prices, index=1, window=5) is None

    def test_computes_average_once_window_is_filled(self):
        prices = [_d(100), _d(102), _d(101), _d(105), _d(110)]
        result = moving_average(prices, index=4, window=5)
        assert result == (_d(100) + _d(102) + _d(101) + _d(105) + _d(110)) / Decimal(5)

    def test_window_slides_correctly(self):
        prices = [_d(x) for x in [1, 2, 3, 4, 5, 6]]
        result = moving_average(prices, index=5, window=5)
        assert result == _d(4)


class TestPctChange:
    def test_first_row_has_no_pct_change(self):
        prices = [_d(100), _d(110)]
        assert pct_change(prices, index=0) is None

    def test_computes_pct_change_vs_previous(self):
        prices = [_d(100), _d(110)]
        result = pct_change(prices, index=1)
        assert result == _d(10)

    def test_handles_price_decrease(self):
        prices = [_d(100), _d(95)]
        result = pct_change(prices, index=1)
        assert result == _d(-5)


class TestBuildCommoditySection:
    def test_no_snapshots_in_range_gets_excluded_note(self):
        section = build_commodity_section(
            symbol="XAU",
            name="Gold",
            snapshots_oldest_first=[],
            alert_snapshot_ids=set(),
            snapshot_ids_oldest_first=[],
        )
        assert section.rows == []
        assert "No price snapshots" in section.excluded_note

    def test_fewer_than_five_snapshots_included_with_note_no_averages(self):
        snaps = [(date(2026, 1, i + 1), _d(100 + i)) for i in range(3)]
        section = build_commodity_section(
            symbol="WTI",
            name="Oil",
            snapshots_oldest_first=snaps,
            alert_snapshot_ids=set(),
            snapshot_ids_oldest_first=[10, 11, 12],
        )
        assert len(section.rows) == 3
        assert section.excluded_note is not None
        assert "Only 3 snapshot(s)" in section.excluded_note
        assert all(row.ma_5 is None and row.ma_10 is None for row in section.rows)

    def test_five_or_more_snapshots_gets_ma5_no_note(self):
        snaps = [(date(2026, 1, i + 1), _d(100 + i)) for i in range(5)]
        section = build_commodity_section(
            symbol="XAU",
            name="Gold",
            snapshots_oldest_first=snaps,
            alert_snapshot_ids=set(),
            snapshot_ids_oldest_first=[1, 2, 3, 4, 5],
        )
        assert section.excluded_note is None
        assert section.rows[-1].ma_5 is not None
        assert section.rows[-1].ma_10 is None

    def test_alert_flag_set_on_matching_snapshot(self):
        snaps = [(date(2026, 1, i + 1), _d(100 + i)) for i in range(3)]
        section = build_commodity_section(
            symbol="WTI",
            name="Oil",
            snapshots_oldest_first=snaps,
            alert_snapshot_ids={11},
            snapshot_ids_oldest_first=[10, 11, 12],
        )
        flags = [row.is_alert for row in section.rows]
        assert flags == [False, True, False]