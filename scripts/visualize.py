"""Generate analytical charts from the SQL-derived report tables."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd

NAVY = "#24384B"
TEAL = "#1C7775"
SLATE = "#8194A3"
TEXT = "#1E2D38"
MUTED = "#637483"
GRID = "#E9EEF1"
WHITE = "#FFFFFF"
STEPS = {
    "Signup": "Registration",
    "Address added": "Address added",
    "Restaurant opened": "Restaurant opened",
    "Added to cart": "Added to cart",
    "Checkout started": "Checkout started",
    "First order": "First order",
}


def _style(ax: plt.Axes, xgrid: bool = False) -> None:
    ax.set_facecolor(WHITE)
    for side in ax.spines.values():
        side.set_visible(False)
    ax.tick_params(axis="both", length=0, colors=MUTED, labelsize=10, pad=8)
    ax.set_axisbelow(True)
    if xgrid:
        ax.grid(axis="x", color=GRID, linewidth=0.9)


def _save(fig: plt.Figure, path: Path) -> None:
    fig.savefig(path, dpi=180, facecolor=WHITE, bbox_inches="tight", pad_inches=0.24)
    plt.close(fig)


def _title(ax: plt.Axes, headline: str, detail: str) -> None:
    ax.set_title(headline, fontsize=17, fontweight="semibold", color=TEXT, loc="left", pad=30)
    ax.text(0, 1.055, detail, transform=ax.transAxes, fontsize=10, color=MUTED,
            ha="left", va="bottom")


def save_charts(funnel: pd.DataFrame, segments: pd.DataFrame,
                payments: pd.DataFrame, output_dir: Path) -> None:
    """Generate five consistent PNG charts from SQL aggregates."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    total = int(funnel.iloc[0]["users"])
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "figure.facecolor": WHITE,
        "axes.facecolor": WHITE, "savefig.facecolor": WHITE,
        "font.size": 10, "axes.unicode_minus": False,
    })

    # Funnel: same denominator (registrations) for every cumulative share.
    order = funnel.iloc[::-1].reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(11.6, 5.9))
    fig.subplots_adjust(left=0.23, right=0.85, top=0.79, bottom=0.15)
    y = range(len(order))
    colors = [TEAL if name == "First order" else NAVY for name in order["event"]]
    ax.barh(y, order["users"], color=colors, height=0.62, zorder=3)
    ax.set_yticks(list(y), [STEPS.get(s, s) for s in order["event"]], color=TEXT)
    ax.set_xlim(0, total * 1.33)
    ax.set_xticks([0, 3000, 6000, 9000, 12000])
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(
        lambda n, _: f"{n/1000:,.0f}k" if n else "0"))
    ax.set_xlabel("Unique users", color=MUTED, fontsize=10, labelpad=12)
    _style(ax, xgrid=True)
    for idx, row in order.iterrows():
        pct = 100 * int(row["users"]) / total
        ax.text(int(row["users"]) + 160, idx,
                f"{int(row['users']):,}   ({pct:.1f}%)",
                va="center", ha="left", fontsize=10, color=TEXT)
    _title(ax, "First-order activation funnel",
           "7-day window from signup · synthetic event data · n = 12,000")
    _save(fig, output_dir / "01_overall_funnel.png")

    # Step loss: local denominator, unlike cumulative funnel conversion.
    loss = funnel.iloc[1:].copy()
    loss["loss_pct"] = 100 - loss["from_previous_pct"].astype(float)
    loss["label"] = ["Signup → address", "Address → restaurant", "Restaurant → cart",
                     "Cart → checkout", "Checkout → first order"]
    loss = loss.iloc[::-1].reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(10.5, 5.3))
    fig.subplots_adjust(left=0.28, right=0.88, top=0.77, bottom=0.18)
    y = range(len(loss))
    colors = [TEAL if r.event == "Added to cart" else SLATE
              for r in loss.itertuples()]
    ax.barh(y, loss["loss_pct"], color=colors, height=0.52)
    ax.set_yticks(list(y), loss["label"], color=TEXT)
    ax.set_xlim(0, 41)
    ax.set_xticks([0, 10, 20, 30, 40])
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    _style(ax, xgrid=True)
    for idx, row in loss.iterrows():
        ax.text(row["loss_pct"] + 0.8, idx,
                f"{row['loss_pct']:.1f}% · {int(row['lost_users']):,} users",
                va="center", fontsize=10, color=TEXT)
    _title(ax, "Drop-off between consecutive steps",
           "Rate = users lost / users entering the step")
    _save(fig, output_dir / "04_step_dropoff.png")

    pay = payments.set_index("platform")
    labels = ["Android", "iOS"]
    vals = [float(pay.loc["android", "checkout_success_pct"]),
            float(pay.loc["ios", "checkout_success_pct"])]
    fig, ax = plt.subplots(figsize=(9.0, 4.15))
    fig.subplots_adjust(left=0.21, right=0.84, top=0.72, bottom=0.22)
    ax.barh([1, 0], vals, height=0.44, color=[NAVY, TEAL])
    ax.set_yticks([1, 0], labels, color=TEXT)
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    _style(ax, xgrid=True)
    for yval, p, name in zip([1, 0], vals, ["android", "ios"]):
        n = int(pay.loc[name, "checkout_users"])
        ax.text(p + 1.6, yval, f"{p:.1f}%  ·  n={n:,}", va="center",
                color=TEXT, fontsize=10)
    _title(ax, "Checkout-to-order conversion",
           f"iOS − Android: {vals[1] - vals[0]:.1f} percentage points · descriptive")
    _save(fig, output_dir / "02_checkout_platform.png")

    # Failure event incidence, not share of permanently failed orders.
    failure = [float(pay.loc["android", "payment_failure_pct"]),
               float(pay.loc["ios", "payment_failure_pct"])]
    fig, ax = plt.subplots(figsize=(9.0, 4.15))
    fig.subplots_adjust(left=0.21, right=0.84, top=0.72, bottom=0.22)
    ax.barh([1, 0], failure, height=0.44, color=[NAVY, TEAL])
    ax.set_yticks([1, 0], labels, color=TEXT)
    ax.set_xlim(0, 50)
    ax.set_xticks([0, 10, 20, 30, 40, 50])
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    _style(ax, xgrid=True)
    for yval, p, name in zip([1, 0], failure, ["android", "ios"]):
        n = int(pay.loc[name, "users_with_payment_failure"])
        ax.text(p + 0.9, yval, f"{p:.1f}%  ·  {n:,} users", va="center",
                color=TEXT, fontsize=10)
    _title(ax, "Users with a payment-failure event",
           "Share of checkout starters · one or more failed attempts")
    _save(fig, output_dir / "03_payment_failures.png")

    # Acquisition channel: denominators (signups) displayed alongside ratios.
    channels = segments.loc[segments["segment_type"] == "channel"].copy()
    channels = channels.sort_values("signup_to_order_pct").reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(9.8, 4.65))
    fig.subplots_adjust(left=0.19, right=0.83, top=0.72, bottom=0.19)
    y = range(len(channels))
    ax.barh(y, channels["signup_to_order_pct"], color=SLATE, height=0.50)
    ax.set_yticks(list(y), [s.title() for s in channels["segment"]], color=TEXT)
    ax.set_xlim(0, 51)
    ax.set_xticks([0, 10, 20, 30, 40, 50])
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    _style(ax, xgrid=True)
    for idx, row in channels.iterrows():
        ax.text(float(row["signup_to_order_pct"]) + 0.8, idx,
                f"{float(row['signup_to_order_pct']):.1f}%  ·  n={int(row['signups']):,}",
                va="center", color=TEXT, fontsize=10)
    _title(ax, "First-order conversion by acquisition channel",
           "7-day activation · descriptive comparison")
    _save(fig, output_dir / "05_acquisition_channels.png")
