"""Behavioral tests for the project, not for a real delivery service."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.generate_data import EVENTS, generate
from scripts.run_analysis import analyze


def test_generator_is_deterministic(tmp_path: Path) -> None:
    a, b = tmp_path / "a", tmp_path / "b"
    generate(a, n_users=90, seed=111)
    generate(b, n_users=90, seed=111)
    for name in ("users.csv", "events.csv"):
        assert (a / name).read_bytes() == (b / name).read_bytes()


def test_user_events_and_order(tmp_path: Path) -> None:
    out = tmp_path / "data"
    generate(out, n_users=300, seed=321)
    users = pd.read_csv(out / "users.csv")
    events = pd.read_csv(out / "events.csv")
    assert len(users) == users.user_id.nunique() == 300
    assert len(events) == events.event_id.nunique()
    assert set(events.event_name).issubset(EVENTS)
    assert events.user_id.isin(users.user_id).all()
    assert bool((events.groupby("user_id").event_name.first() == "signup").all())
    order = ["signup", "address_added", "restaurant_opened", "added_to_cart", "checkout_started", "order_completed"]
    for uid, user_events in events.groupby("user_id"):
        seen = set(user_events.event_name)
        if "order_completed" in seen:
            assert all(x in seen for x in order)
        times = pd.to_datetime(user_events.event_time)
        assert times.is_monotonic_increasing


def test_analysis_pipeline_with_small_dataset(tmp_path: Path) -> None:
    raw, reports = tmp_path / "raw", tmp_path / "reports"
    generate(raw, n_users=500, seed=2026)
    metrics = analyze(raw, reports)
    assert metrics["users"] == 500
    assert 0 <= metrics["first_orders"] <= 500
    assert 0 <= metrics["conversion"] <= 100
    for name in ["analysis_report.md", "validation_report.md", "figures/01_overall_funnel.png",
                 "figures/02_checkout_platform.png", "figures/03_payment_failures.png",
                 "figures/04_step_dropoff.png", "figures/05_acquisition_channels.png",
                 "tables/funnel.csv", "tables/payments.csv"]:
        assert (reports / name).is_file()
