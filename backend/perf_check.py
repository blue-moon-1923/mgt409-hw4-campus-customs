"""Count SQLite statements and time the catalogue reads.

    python perf_check.py

Used to measure the N+1 fix in Problem 9: `search_catalogue` used to issue one
query per product for its size rows.
"""

from __future__ import annotations

import time

import tools

counter = {"n": 0}
_real_connect = tools.connect_ro


def counting_connect():
    conn = _real_connect()
    conn.set_trace_callback(lambda _stmt: counter.__setitem__("n", counter["n"] + 1))
    return conn


tools.connect_ro = counting_connect


def measure(label: str, call, runs: int = 20) -> None:
    tools._snapshot_cache = None  # cold: force a real read
    counter["n"] = 0
    start = time.perf_counter()
    call()
    cold_ms = (time.perf_counter() - start) * 1000
    cold_statements = counter["n"]

    counter["n"] = 0
    start = time.perf_counter()
    for _ in range(runs):
        call()
    warm_ms = (time.perf_counter() - start) * 1000 / runs
    warm_statements = counter["n"] / runs

    print(
        f"{label:<24} cold: {cold_statements:4d} statements {cold_ms:7.2f} ms  |  "
        f"warm: {warm_statements:5.1f} statements {warm_ms:7.2f} ms"
    )


if __name__ == "__main__":
    measure("search_catalogue", lambda: tools.search_catalogue("warm navy hoodie"))
    measure("browse_category", lambda: tools.browse_category("Hoodies"))
    measure("load_product_summaries", tools.load_product_summaries)
    measure("load_product_detail", lambda: tools.load_product_detail("basic-hoodie-big-yale"))
    measure("related_products", lambda: tools.related_products("grace-hopper-college-crewneck"))
