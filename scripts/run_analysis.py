"""Run auditable SQL analytics on generated product events; export report and figures."""
from __future__ import annotations

import math
import sqlite3
from pathlib import Path

from scripts.visualize import save_charts
import pandas as pd

SQL_ROOT = Path(__file__).resolve().parents[1] / "sql"


def query(connection: sqlite3.Connection, filename: str) -> pd.DataFrame:
    sql = (SQL_ROOT / filename).read_text(encoding="utf-8")
    return pd.read_sql_query(sql, connection)


def analyze(data_dir: Path, report_dir: Path) -> dict:
    data_dir, report_dir = Path(data_dir), Path(report_dir)
    (report_dir / "tables").mkdir(parents=True, exist_ok=True)
    (report_dir / "figures").mkdir(parents=True, exist_ok=True)
    users = pd.read_csv(data_dir / "users.csv", dtype=str)
    events = pd.read_csv(data_dir / "events.csv", dtype=str)
    with sqlite3.connect(":memory:") as db:
        users.to_sql("users", db, index=False)
        events.to_sql("events", db, index=False)
        db.execute("CREATE UNIQUE INDEX idx_user ON users(user_id)")
        db.execute("CREATE INDEX idx_event_lookup ON events(user_id,event_name,event_time)")
        db.executescript((SQL_ROOT / "00_build_user_funnel.sql").read_text(encoding="utf-8"))
        outputs = {
            "data_quality": query(db, "01_data_quality.sql"),
            "funnel": query(db, "02_funnel_overall.sql"),
            "segments": query(db, "03_funnel_by_segment.sql"),
            "payments": query(db, "04_payment_failures.sql"),
            "repeat": query(db, "05_repeat_purchase.sql"),
        }
    for name, frame in outputs.items():
        frame.to_csv(report_dir / "tables" / f"{name}.csv", index=False)

    qa = outputs["data_quality"]
    assert (qa["n"] == 0).all(), f"Data quality checks failed:\n{qa.to_string(index=False)}"
    funnel = outputs["funnel"]
    assert funnel["users"].is_monotonic_decreasing, "Impossible non-monotonic funnel"
    assert int(funnel.loc[0, "users"]) == len(users)

    # Independent Pandas count checks (SQL and Pandas are not using the same aggregation).
    events_by_type = events.groupby("event_name")["user_id"].nunique()
    checks = {
        "Signup": "signup", "Address added": "address_added",
        "Restaurant opened": "restaurant_opened", "Added to cart": "added_to_cart",
        "Checkout started": "checkout_started", "First order": "order_completed",
    }
    for _, row in funnel.iterrows():
        assert int(row["users"]) == int(events_by_type.get(checks[row["event"]], 0)), (
            "SQL and independent pandas counts differ", row["event"]
        )

    pay = outputs["payments"].set_index("platform")
    segments = outputs["segments"]
    repeat = outputs["repeat"].iloc[0]
    total, converted = int(funnel.iloc[0]["users"]), int(funnel.iloc[-1]["users"])
    conversion = 100 * converted / total
    android = pay.loc["android"]
    ios = pay.loc["ios"]
    android_n, ios_n = int(android["checkout_users"]), int(ios["checkout_users"])
    android_x, ios_x = int(android["completed_users"]), int(ios["completed_users"])
    p_android, p_ios = android_x / android_n, ios_x / ios_n
    gap_pp = 100 * (p_ios - p_android)
    # Approximate independent two-proportion 95% confidence interval, descriptive only.
    se = math.sqrt(p_ios * (1 - p_ios) / ios_n + p_android * (1 - p_android) / android_n)
    low, high = (p_ios - p_android - 1.96 * se) * 100, (p_ios - p_android + 1.96 * se) * 100
    losses = funnel.dropna(subset=["lost_users"]).sort_values("lost_users", ascending=False)
    largest_loss = losses.iloc[0]

    save_charts(funnel, segments, outputs["payments"], report_dir / "figures")

    # What-if is not a causal estimate: just hypothetical +5 pp Android checkout completion.
    hypothetical_extra = round(android_n * 0.05)
    (report_dir / "analysis_report.md").write_text(f"""# Аналитический отчёт: воронка первого заказа

> **Источник:** воспроизводимые **синтетические** события, созданные кодом `scripts/generate_data.py` (seed 20261029). Не реальные данные компании и не рыночная статистика. Встроенные вероятности специально создают различия платформ и каналов.

## 1. Продуктовая задача

Руководитель продукта доставки еды хочет понять, сколько новых пользователей делают первый заказ в течение 7 дней регистрации и где в пути теряются пользователи. Задача аналитика — рассчитать воронку, найти диагностические различия и предложить следующие измерения и эксперимент.

## 2. Короткий вывод

- Регистраций: **{total:,}**; завершили первый заказ: **{converted:,}** (**{conversion:.1f}%**).
- Крупнейшая абсолютная потеря на переходе **{funnel.loc[int(largest_loss['step'])-2, 'event']} → {largest_loss['event']}**: **{int(largest_loss['lost_users']):,} пользователей**. Это не обязательно самая легко исправимая проблема.
- Конверсия **checkout → first order**: **{p_android*100:.1f}% на Android**, **{p_ios*100:.1f}% на iOS** (разница **{gap_pp:.1f} п.п.** в пользу iOS; приближённый 95% ДИ разницы: **[{low:.1f}; {high:.1f}] п.п.**).
- Событие `payment_failed` среди начавших checkout: **{android['payment_failure_pct']:.1f}% Android** и **{ios['payment_failure_pct']:.1f}% iOS**. Это диагностическая корреляция в симуляции, не доказательство причинности в реальном продукте.

## 3. Воронка

![Общая воронка](figures/01_overall_funnel.png)

![Потери между этапами](figures/04_step_dropoff.png)

Деноминатор для общей конверсии — **все зарегистрированные**; для конверсии шага — **дошедшие до предыдущего шага**. Строки — уникальные пользователи, а не количество событий.

| Шаг | Пользователей | От регистраций | От предыдущего шага | Потеря пользователей |
|---|---:|---:|---:|---:|
""" + "\n".join(
        f"| {r.event} | {int(r.users):,} | {r.from_signup_pct:.1f}% | "
        f"{('—' if pd.isna(r.from_previous_pct) else f'{r.from_previous_pct:.1f}%')} | "
        f"{('—' if pd.isna(r.lost_users) else f'{int(r.lost_users):,}')} |"
        for r in funnel.itertuples()
    ) + f"""

## 4. Проверка платформ

![Конверсия checkout](figures/02_checkout_platform.png)

![Ошибки оплаты](figures/03_payment_failures.png)

На Android доля зафиксированных ошибок оплаты выше, а завершение оформления заказа ниже. **Гипотеза:** некоторым пользователям Android сложнее успешно оплатить заказ. **Нельзя заключить**, что события ошибок объясняют всю разницу: не учтены типы банковских карт, версии приложения, цена заказа, интернет-соединение, промокоды и другие факторы. Для проверки нужны логи ошибок, методы оплаты и контрольный эксперимент.

### Каналы привлечения

![Активация по каналам](figures/05_acquisition_channels.png)

## 5. Возврат за повторной покупкой (вторичная метрика)

Из **{int(repeat['first_orders']):,}** пользователей с первым заказом повторили покупку **{int(repeat['repeated_within_7d']):,} ({repeat['repeat_7d_pct']:.1f}%)** за 7 дней и **{int(repeat['repeated_within_30d']):,} ({repeat['repeat_30d_pct']:.1f}%)** за 30 дней. Это **кумулятивный repeat purchase**, не классический exact-day retention на D7/D30. Полное окно наблюдения есть у всех покупателей (см. methodology).

## 6. Что рекомендовать продукту

1. **Проверить качество событий:** что значит `payment_failed`, нет ли потерь логирования по платформам, нет ли повторов.
2. **Разбить checkout Android по версии приложения, методу оплаты и кодам ошибок**, чтобы найти конкретный механизм (если появятся такие поля).
3. **Провести качественное исследование** (сессии/интервью) пользователей, не завершивших оплату.
4. **Проверить исправление через A/B-тест:** Android-пользователи, начавшие checkout; рандомизация по `user_id`; основная метрика — доля завершивших первый заказ из начавших checkout; guardrails — платёжные ошибки и отмены, стоимость обработки платежей. Срок и размер выборки рассчитать до запуска по MDE/мощности.

**Простая оценка масштаба, не прогноз:** при гипотетическом росте Android checkout-конверсии на **5 п.п.** это дало бы около **{hypothetical_extra}** дополнительных первых заказов на таком же объёме checkout. Здесь НЕ оценен реальный эффект и НЕ заявлено, что он достижим.

## 7. Проверки и ограничения

- Проверено шесть типов ошибок качества данных, каждое количество = 0.
- Проверена последовательность событий и окно 7 дней; все шаги вложены друг в друга.
- Счётчики SQL сверены независимо через `pandas`.
- **Ограничения:** синтетические данные; нет пользовательского эксперимента; не показана выручка; поля ошибок намеренно упрощены; сегментные сравнения описательные и не причинные.

Таблицы с расчётами: [`tables/`](tables/). Определения: [`../docs/methodology.md`](../docs/methodology.md). SQL: [`../sql/`](../sql/).
""", encoding="utf-8")

    validation = (
        "# Validation report\n\nПроверки качества:\n\n"
        + "\n".join(f"- `{row.issue}`: **{int(row.n)}**" for row in qa.itertuples())
        + "\n\nSQL и pandas совпали по всем шести шагам; вложенность воронки соблюдена.\n"
    )
    (report_dir / "validation_report.md").write_text(validation, encoding="utf-8")
    return {"users": total, "first_orders": converted, "conversion": conversion,
            "android_checkout_pct": p_android * 100, "ios_checkout_pct": p_ios * 100,
            "largest_loss": str(largest_loss["event"]), "gap_pp": gap_pp,
            "android_checkouts": android_n, "ios_checkouts": ios_n,
            "android_fail_pct": float(android["payment_failure_pct"]),
            "ios_fail_pct": float(ios["payment_failure_pct"]),
            "repeat_7d_pct": float(repeat["repeat_7d_pct"]),
            "repeat_30d_pct": float(repeat["repeat_30d_pct"])}


def main() -> None:
    result = analyze(Path("data/raw"), Path("reports"))
    print(result)


if __name__ == "__main__":
    main()
