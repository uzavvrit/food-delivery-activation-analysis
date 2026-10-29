"""Generate deterministic *synthetic* product events (not company data)."""
from __future__ import annotations

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

SEED = 20261029
N_USERS = 12_000
CHANNELS = ("organic", "ads", "referral", "social")
CHANNEL_WEIGHTS = (0.35, 0.30, 0.20, 0.15)
PLATFORMS = ("android", "ios")
EVENTS = (
    "signup", "address_added", "restaurant_opened", "added_to_cart",
    "checkout_started", "payment_failed", "order_completed", "repeat_order_completed",
)


def generate(output_dir: Path, n_users: int = N_USERS, seed: int = SEED) -> tuple[Path, Path]:
    """Write users.csv and events.csv; reproducible with the same seed."""
    rng = random.Random(seed)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    users_file, events_file = output_dir / "users.csv", output_dir / "events.csv"
    start = datetime(2026, 1, 1)
    end = datetime(2026, 3, 31, 23, 59)
    total_minutes = int((end - start).total_seconds() // 60)
    event_no = 0

    with users_file.open("w", newline="", encoding="utf-8") as uf, events_file.open(
        "w", newline="", encoding="utf-8"
    ) as ef:
        user_writer = csv.writer(uf)
        event_writer = csv.writer(ef)
        user_writer.writerow(["user_id", "registered_at", "platform", "channel"])
        event_writer.writerow(["event_id", "user_id", "event_name", "event_time"])

        def emit(user_id: str, name: str, at: datetime) -> None:
            nonlocal event_no
            event_no += 1
            event_writer.writerow([f"ev_{event_no:08d}", user_id, name, at.strftime("%Y-%m-%d %H:%M:%S")])

        def advance(at: datetime) -> datetime:
            return at + timedelta(minutes=rng.randint(4, 45))

        for number in range(1, n_users + 1):
            uid = f"u_{number:06d}"
            registered = start + timedelta(minutes=rng.randint(0, total_minutes))
            platform = rng.choices(PLATFORMS, weights=(0.55, 0.45), k=1)[0]
            channel = rng.choices(CHANNELS, weights=CHANNEL_WEIGHTS, k=1)[0]
            user_writer.writerow([uid, registered.strftime("%Y-%m-%d %H:%M:%S"), platform, channel])
            event_time = registered
            emit(uid, "signup", event_time)

            # Controlled design assumptions: channel affects onboarding; platform affects payment friction.
            address_prob = {"organic": 0.90, "ads": 0.79, "referral": 0.87, "social": 0.83}[channel]
            address_prob += 0.02 if platform == "ios" else -0.015
            if rng.random() >= address_prob:
                continue
            event_time = advance(event_time)
            emit(uid, "address_added", event_time)
            if rng.random() >= 0.88:
                continue
            event_time = advance(event_time)
            emit(uid, "restaurant_opened", event_time)
            if rng.random() >= (0.72 if platform == "ios" else 0.70):
                continue
            event_time = advance(event_time)
            emit(uid, "added_to_cart", event_time)
            if rng.random() >= 0.88:
                continue
            event_time = advance(event_time)
            emit(uid, "checkout_started", event_time)

            failure = rng.random() < (0.33 if platform == "android" else 0.13)
            if failure:
                event_time = advance(event_time)
                emit(uid, "payment_failed", event_time)
            completed = rng.random() < (0.23 if failure else 0.87)
            if not completed:
                continue
            event_time = advance(event_time)
            emit(uid, "order_completed", event_time)

            if rng.random() < 0.39:
                # Cumulative second-purchase window: within 7 or 30 days after first order.
                days_to_second = rng.randint(1, 6) if rng.random() < 0.48 else rng.randint(8, 28)
                event_time += timedelta(days=days_to_second, minutes=rng.randint(3, 100))
                emit(uid, "repeat_order_completed", event_time)

    return users_file, events_file


def main() -> None:
    u, e = generate(Path("data/raw"))
    print(f"Generated {N_USERS:,} synthetic users: {u}, {e} (seed={SEED})")


if __name__ == "__main__":
    main()
