#!/usr/bin/env python3
"""List KPI first-check projects due on a given day."""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta

from bot.config_loader import load_config
from bot.lark_bitable import get_tenant_access_token, list_records
from bot.workflow_kpi_result_push import posted_ids
from bot.workflow_kpi_schedule import (
    FIRST_DAYS,
    SCHEDULE_START,
    _STATE_FILE,
    _load_state,
    select_due,
)


def main() -> None:
    today = date(2026, 10, 10)
    cfg = load_config()
    token = get_tenant_access_token(
        os.environ["LARK_APP_ID"], os.environ["LARK_APP_SECRET"]
    )
    records = list_records(
        token, cfg.workflow_base_app_token, cfg.workflow_progress_table_id
    )
    state = _load_state(_STATE_FILE)
    posted = posted_ids()
    due = select_due(
        records,
        today=today,
        state=state,
        status_field=cfg.workflow_status_field,
        name_field=cfg.workflow_project_name_field,
        already_posted=posted,
    )
    first = [row for row in due if row["round"] == "first"]
    second = [row for row in due if row["round"] == "second"]
    print(f"SCHEDULE_START={SCHEDULE_START} FIRST_DAYS={FIRST_DAYS}")
    print(
        "state first={} second={} posted={}".format(
            len(state.get("first") or {}),
            len(state.get("second") or {}),
            len(posted),
        )
    )
    print(f"due_total={len(due)} first={len(first)} second={len(second)}")
    print("--- FIRST tomorrow ---")
    for row in first:
        live = datetime.strptime(row["live_date"], "%Y-%m-%d").date()
        due_day = live + timedelta(days=FIRST_DAYS)
        flag = "exact" if due_day == today else f"overdue_since_{due_day}"
        print(f"{row['live_date']}\t{row['project']}\t{row['record_id']}\t{flag}")


if __name__ == "__main__":
    main()
