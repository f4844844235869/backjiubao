from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from time import perf_counter

BASE_DIR = Path(__file__).resolve().parents[1]
TEST_LOGS_DIR = BASE_DIR / "docs" / "test-logs"


@dataclass(frozen=True)
class ScenarioCase:
    key: str
    title: str
    path: str


@dataclass(frozen=True)
class ScenarioResult:
    case: ScenarioCase
    exit_code: int
    duration_seconds: float
    command: list[str]

    @property
    def status(self) -> str:
        return "PASS" if self.exit_code == 0 else "FAIL"


SCENARIO_CASES = [
    ScenarioCase(
        key="employee_onboarding",
        title="员工建档与后台授权流程",
        path="tests/scenarios/test_employee_onboarding_flow.py",
    ),
    ScenarioCase(
        key="current_store_context",
        title="多门店当前门店上下文",
        path="tests/scenarios/test_current_store_context_flow.py",
    ),
    ScenarioCase(
        key="employee_rehire",
        title="员工离职再入职",
        path="tests/scenarios/test_employee_rehire_flow.py",
    ),
    ScenarioCase(
        key="multi_role_scope_union",
        title="多角色多数据范围并集",
        path="tests/scenarios/test_multi_role_scope_union_flow.py",
    ),
    ScenarioCase(
        key="org_inheritance",
        title="组织树父子节点继承",
        path="tests/scenarios/test_org_inheritance_flow.py",
    ),
    ScenarioCase(
        key="store_employee_permission",
        title="门店员工权限边界",
        path="tests/scenarios/test_store_employee_permission_flow.py",
    ),
    ScenarioCase(
        key="miniapp_store_context",
        title="小程序门店上下文与关联员工",
        path="tests/scenarios/test_miniapp_store_context_flow.py",
    ),
    ScenarioCase(
        key="backend_miniapp_e2e",
        title="后台与小程序端到端链路",
        path="tests/scenarios/test_backend_miniapp_end_to_end_flow.py",
    ),
    ScenarioCase(
        key="employee_cross_store",
        title="单店员工跨店访问限制",
        path="tests/scenarios/test_employee_cross_store_access_flow.py",
    ),
    ScenarioCase(
        key="employee_role_change",
        title="员工角色变更后权限收敛",
        path="tests/scenarios/test_employee_role_change_flow.py",
    ),
    ScenarioCase(
        key="employee_multi_store_membership",
        title="员工多门店归属访问",
        path="tests/scenarios/test_employee_multi_store_membership_flow.py",
    ),
    ScenarioCase(
        key="user_to_employee_transfer",
        title="用户转员工与主门店切换",
        path="tests/scenarios/test_user_to_employee_transfer_flow.py",
    ),
    ScenarioCase(
        key="employee_position_change",
        title="员工岗位变更同步任职记录",
        path="tests/scenarios/test_employee_position_change_flow.py",
    ),
    ScenarioCase(
        key="store_org_maintenance",
        title="门店与组织基础维护",
        path="tests/scenarios/test_store_org_maintenance_flow.py",
    ),
    ScenarioCase(
        key="store_org_deletion_boundary",
        title="门店与组织删除边界",
        path="tests/scenarios/test_store_org_deletion_boundary_flow.py",
    ),
    ScenarioCase(
        key="role_grant_boundary",
        title="角色可见与可分配边界",
        path="tests/scenarios/test_role_grant_boundary_flow.py",
    ),
]

SCENARIO_GROUPS = {
    "backend": [
        "employee_onboarding",
        "employee_rehire",
        "store_employee_permission",
        "employee_cross_store",
        "employee_role_change",
        "employee_multi_store_membership",
        "user_to_employee_transfer",
        "employee_position_change",
        "store_org_maintenance",
        "store_org_deletion_boundary",
        "role_grant_boundary",
    ],
    "miniapp": [
        "miniapp_store_context",
        "backend_miniapp_e2e",
    ],
    "permission": [
        "current_store_context",
        "multi_role_scope_union",
        "org_inheritance",
        "store_employee_permission",
        "employee_cross_store",
        "employee_role_change",
        "employee_multi_store_membership",
        "user_to_employee_transfer",
        "employee_position_change",
        "store_org_maintenance",
        "store_org_deletion_boundary",
        "role_grant_boundary",
    ],
    "all": [case.key for case in SCENARIO_CASES],
}


def get_case_map() -> dict[str, ScenarioCase]:
    return {case.key: case for case in SCENARIO_CASES}


def resolve_cases(group: str) -> list[ScenarioCase]:
    case_map = get_case_map()
    return [case_map[key] for key in SCENARIO_GROUPS[group]]


def build_pytest_command(case: ScenarioCase) -> list[str]:
    return [sys.executable, "-m", "pytest", case.path, "-q"]


def run_case(case: ScenarioCase) -> ScenarioResult:
    command = build_pytest_command(case)
    started_at = perf_counter()
    completed = subprocess.run(command, cwd=BASE_DIR, check=False)
    duration_seconds = perf_counter() - started_at
    return ScenarioResult(
        case=case,
        exit_code=completed.returncode,
        duration_seconds=duration_seconds,
        command=command,
    )


def build_log_filename(now: datetime) -> str:
    return now.strftime("%Y%m%d_%H%M%S.md")


def build_log_markdown(
    *,
    group: str,
    started_at: datetime,
    results: list[ScenarioResult],
    run_full: bool,
) -> str:
    executed = len(results)
    passed = len([item for item in results if item.exit_code == 0])
    failed = len([item for item in results if item.exit_code != 0])
    total_duration = sum(item.duration_seconds for item in results)
    full_suffix = "，并在最后执行全量测试" if run_full else ""

    lines = [
        "# 场景执行日志",
        "",
        f"记录时间：`{started_at.strftime('%Y-%m-%d %H:%M:%S CST')}`",
        "",
        "## 执行说明",
        "",
        f"- 场景分组：`{group}`",
        f"- 执行策略：按顺序串行执行，前一个场景结束后自动开始下一个场景{full_suffix}",
        f"- 执行场景数：`{executed}`",
        f"- 成功：`{passed}`",
        f"- 失败：`{failed}`",
        f"- 总耗时：`{total_duration:.2f}s`",
        "",
        "## 场景明细",
        "",
        "| 场景 | 测试文件 | 状态 | 耗时 | 命令 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for result in results:
        lines.append(
            f"| {result.case.title} | `{result.case.path}` | `{result.status}` | "
            f"`{result.duration_seconds:.2f}s` | `{' '.join(result.command)}` |"
        )
    lines.extend(
        [
            "",
            "## 当前结论",
            "",
            "- 这个日志由场景执行脚本自动生成，可用于记录一轮连续场景验证结果",
            "- 单个场景失败时会保留已执行结果，便于定位中断点",
        ]
    )
    if failed:
        lines.append("- 当前存在失败场景，请优先修复后再继续后续场景链路验证")
    else:
        lines.append("- 当前所选场景组已全部通过")
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="按顺序执行一组场景测试并生成日志")
    parser.add_argument(
        "--group",
        default="all",
        choices=sorted(SCENARIO_GROUPS.keys()),
        help="要执行的场景分组",
    )
    parser.add_argument(
        "--continue-on-failure",
        action="store_true",
        help="单个场景失败后继续执行后续场景",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="场景组执行完成后追加一次全量 pytest",
    )
    parser.add_argument(
        "--skip-log",
        action="store_true",
        help="不生成测试日志文件",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    started_at = datetime.now()
    cases = resolve_cases(args.group)
    results: list[ScenarioResult] = []

    for case in cases:
        result = run_case(case)
        results.append(result)
        if result.exit_code != 0 and not args.continue_on_failure:
            break

    if args.full and (args.continue_on_failure or all(item.exit_code == 0 for item in results)):
        full_case = ScenarioCase(
            key="full_pytest",
            title="全量 pytest",
            path="tests",
        )
        command = [sys.executable, "-m", "pytest", "-q"]
        started = perf_counter()
        completed = subprocess.run(command, cwd=BASE_DIR, check=False)
        results.append(
            ScenarioResult(
                case=full_case,
                exit_code=completed.returncode,
                duration_seconds=perf_counter() - started,
                command=command,
            )
        )

    if not args.skip_log:
        TEST_LOGS_DIR.mkdir(parents=True, exist_ok=True)
        log_path = TEST_LOGS_DIR / build_log_filename(started_at)
        log_path.write_text(
            build_log_markdown(
                group=args.group,
                started_at=started_at,
                results=results,
                run_full=args.full,
            ),
            encoding="utf-8",
        )
        sys.stdout.write(f"已生成场景日志：{log_path}\n")

    return 0 if all(item.exit_code == 0 for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
