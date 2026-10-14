
from pathlib import Path
import random
import sqlite3

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "marketing.db"

def main():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    rng = random.Random(42)

    conversion_probabilities = {
        "Email": 0.12,
        "Paid Search": 0.08,
        "Social": 0.05,
    }

    rows = []
    for event_id in range(1, 1001):
        channel = rng.choice(list(conversion_probabilities))
        converted = int(
            rng.random() < conversion_probabilities[channel]
        )
        rows.append((event_id, channel, converted))

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DROP TABLE IF EXISTS marketing_events")
        conn.execute(
            """
            CREATE TABLE marketing_events (
                event_id INTEGER PRIMARY KEY,
                channel TEXT NOT NULL,
                converted INTEGER NOT NULL
            )
            """
        )
        conn.executemany(
            "INSERT INTO marketing_events VALUES (?, ?, ?)",
            rows,
        )

        results = conn.execute(
            """
            SELECT channel,
                   COUNT(*) AS total_events,
                   SUM(converted) AS conversions,
                   ROUND(AVG(converted) * 100, 2)
                       AS conversion_rate_pct
            FROM marketing_events
            GROUP BY channel
            ORDER BY conversion_rate_pct DESC
            """
        ).fetchall()

    for result in results:
        print(result)


if __name__ == "__main__":
    main()
