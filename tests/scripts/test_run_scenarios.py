from datetime import datetime

from scripts.run_scenarios import (
    ScenarioResult,
    build_log_filename,
    build_log_markdown,
    resolve_cases,
)


def test_resolve_cases_returns_ordered_group_cases() -> None:
    cases = resolve_cases("miniapp")

    assert [item.key for item in cases] == [
        "miniapp_store_context",
        "backend_miniapp_e2e",
    ]


def test_build_log_markdown_includes_summary_and_case_rows() -> None:
    now = datetime(2026, 3, 15, 7, 30, 0)
    cases = resolve_cases("backend")
    results = [
        ScenarioResult(
            case=cases[0],
            exit_code=0,
            duration_seconds=1.23,
            command=["python", "-m", "pytest", cases[0].path, "-q"],
        ),
        ScenarioResult(
            case=cases[1],
            exit_code=1,
            duration_seconds=2.34,
            command=["python", "-m", "pytest", cases[1].path, "-q"],
        ),
    ]

    markdown = build_log_markdown(
        group="backend",
        started_at=now,
        results=results,
        run_full=False,
    )

    assert "场景分组：`backend`" in markdown
    assert "成功：`1`" in markdown
    assert "失败：`1`" in markdown
    assert cases[0].title in markdown
    assert cases[1].path in markdown
    assert "当前存在失败场景" in markdown


def test_build_log_filename_uses_timestamp_format() -> None:
    filename = build_log_filename(datetime(2026, 3, 15, 7, 30, 0))

    assert filename == "20260315_073000.md"
