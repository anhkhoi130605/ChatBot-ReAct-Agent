from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from agent import HelpdeskAgent
from env_loader import load_lab_env
from providers import make_provider
from tools import TOOL_FUNCTIONS, load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version


ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
DATA_DIR = ROOT / "data"
load_lab_env(ROOT)

ALLOWED_CASE_FAILURE_TYPES = {
    "wrong_tool",
    "wrong_arg_value",
    "wrong_boundary",
    "unnecessary_tool",
    "out_of_scope",
    "missing_info",
}


def load_cases(path: Path, phase: str) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    cases = data["cases"]
    cases = [case for case in cases if case["phase"] == phase]
    validate_case_failure_types(cases, path)
    return cases


def validate_case_failure_types(cases: list[dict[str, Any]], path: Path) -> None:
    invalid: list[str] = []
    for case in cases:
        failure_type = case.get("failure_type")
        if failure_type not in ALLOWED_CASE_FAILURE_TYPES:
            invalid.append(f"{case.get('id', '<missing id>')}: {failure_type!r}")
    if invalid:
        allowed = ", ".join(sorted(ALLOWED_CASE_FAILURE_TYPES))
        joined = "; ".join(invalid)
        raise ValueError(f"Invalid failure_type in {path}: {joined}. Allowed: {allowed}")


def validate_expected_tools(cases: list[dict[str, Any]], declarations: list[dict[str, Any]], path: Path) -> None:
    declared = {item["name"] for item in declarations}
    implemented = set(TOOL_FUNCTIONS)
    invalid: list[str] = []
    for case in cases:
        for call in case.get("expect", {}).get("tool_calls", []):
            name = call.get("name")
            if name not in declared:
                invalid.append(f"{case.get('id', '<missing id>')}: {name!r} not declared in tools.yaml")
            elif name not in implemented:
                invalid.append(f"{case.get('id', '<missing id>')}: {name!r} has no implementation in tools.py")
    if invalid:
        raise ValueError(f"Invalid expected tool in {path}: {'; '.join(invalid)}")


def load_dataset_info(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        "dataset_id": data.get("dataset_id", path.stem),
        "dataset_role": data.get("dataset_role", ""),
        "description": data.get("description", ""),
    }


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    return slug.strip("_") or "run"


def case_messages(case: dict[str, Any]) -> list[dict[str, str]]:
    if "turns" in case:
        turns = case["turns"]
        previous = turns[:-1]
        latest = turns[-1]["content"]
        previous_text = "\n".join(
            f"- Earlier {item['role']} turn {index + 1}: {item['content']}"
            for index, item in enumerate(previous)
        )
        content = (
            "Conversation context for a multi-turn eval.\n"
            "Use earlier turns only as context. Do not answer earlier turns and do not call tools for them.\n\n"
            f"{previous_text}\n\n"
            f"Latest user turn to answer now: {latest}"
        )
        return [{"role": "user", "content": content}]
    return [{"role": "user", "content": case.get("input") or case.get("query", "")}]


def normalize_value(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip().lower()
    if isinstance(value, list):
        return sorted(normalize_value(item) for item in value)
    return value


def compare_subset(expected: dict[str, Any], actual: dict[str, Any]) -> tuple[bool, list[str], int, int]:
    failures: list[str] = []
    total = 0
    correct = 0
    for key, expected_value in expected.items():
        total += 1
        actual_value = actual.get(key)
        if key == "missing_fields":
            expected_set = set(expected_value)
            actual_set = set(actual_value or [])
            ok = expected_set.issubset(actual_set)
        elif key == "constraints":
            expected_set = set(normalize_value(expected_value))
            actual_set = set(normalize_value(actual_value or []))
            ok = expected_set.issubset(actual_set)
        else:
            ok = normalize_value(actual_value) == normalize_value(expected_value)
        if ok:
            correct += 1
        else:
            failures.append(f"{key}: expected {expected_value!r}, got {actual_value!r}")
    return len(failures) == 0, failures, correct, total


def best_arg_match(expected_args: dict[str, Any], actual_calls: list[tuple[int, dict[str, Any]]]) -> tuple[int, list[str], int, int] | None:
    best: tuple[int, list[str], int, int] | None = None
    for index, actual_call in actual_calls:
        _, arg_failures, arg_correct, arg_total = compare_subset(expected_args, actual_call.get("args", {}))
        candidate = (index, arg_failures, arg_correct, arg_total)
        if best is None or (arg_correct, -len(arg_failures)) > (best[2], -len(best[1])):
            best = candidate
    return best


def evaluate_phase_b(case: dict[str, Any], tool_calls: list[dict[str, Any]], text: str | None) -> dict[str, Any]:
    expect = case["expect"]
    case_failure_type = case["failure_type"]
    if expect.get("no_tool"):
        passed = not tool_calls
        return {
            "passed": passed,
            "routing_correct": passed,
            "args_correct": passed,
            "actual_tool_calls": tool_calls,
            "actual_text": text,
            "case_failure_type": case_failure_type,
            "observed_mismatch": None if passed else "unexpected_tool_call",
            "failure_type": None if passed else case_failure_type,
            "failures": [] if passed else ["expected no tool call"],
        }

    expected_calls = expect.get("tool_calls", [])
    failures: list[str] = []
    routing_correct = True
    args_correct = True
    observed_mismatch: str | None = None
    unmatched_actual: dict[int, dict[str, Any]] = {index: call for index, call in enumerate(tool_calls)}

    for expected_call in expected_calls:
        same_name = [
            (index, actual_call)
            for index, actual_call in unmatched_actual.items()
            if actual_call["name"] == expected_call["name"]
        ]
        if not same_name:
            routing_correct = False
            args_correct = False
            observed_mismatch = observed_mismatch or "missing_tool_call"
            failures.append(f"missing tool call {expected_call['name']}")
            continue

        match = best_arg_match(expected_call.get("args", {}), same_name)
        if match is None:
            routing_correct = False
            args_correct = False
            observed_mismatch = observed_mismatch or "missing_tool_call"
            failures.append(f"missing tool call {expected_call['name']}")
            continue

        matched_index, arg_failures, arg_correct, arg_total = match
        unmatched_actual.pop(matched_index, None)
        if arg_correct != arg_total:
            args_correct = False
            observed_mismatch = observed_mismatch or "wrong_arg_value"
            failures.extend(arg_failures)

    for actual_call in unmatched_actual.values():
        routing_correct = False
        args_correct = False
        observed_mismatch = observed_mismatch or "extra_tool_call"
        failures.append(f"extra tool call {actual_call['name']}")

    passed = routing_correct and args_correct and not failures
    return {
        "passed": passed,
        "routing_correct": routing_correct,
        "args_correct": args_correct,
        "actual_tool_calls": tool_calls,
        "actual_text": text,
        "case_failure_type": case_failure_type,
        "observed_mismatch": None if passed else observed_mismatch,
        "failure_type": None if passed else case_failure_type,
        "failures": failures,
    }


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(results)
    measured = [item for item in results if item["result"].get("failure_type") != "provider_error"]
    provider_errors = total - len(measured)
    passed = sum(1 for item in measured if item["result"]["passed"])
    summary: dict[str, Any] = {
        "total_cases": total,
        "measured_cases": len(measured),
        "provider_error_cases": provider_errors,
        "passed_cases": passed,
        "case_accuracy": round(passed / len(measured), 4) if measured else 0.0,
    }

    phase_b = [item for item in measured if item["phase"] == "B"]
    if phase_b:
        routing = sum(1 for item in phase_b if item["result"].get("routing_correct"))
        args = sum(1 for item in phase_b if item["result"].get("args_correct"))
        multi = [item for item in phase_b if item.get("is_multiturn")]
        summary.update({
            "tool_routing_accuracy": round(routing / len(phase_b), 4),
            "argument_accuracy": round(args / len(phase_b), 4),
            "multiturn_accuracy": round(sum(1 for item in multi if item["result"]["passed"]) / len(multi), 4) if multi else None,
        })

    failure_counts: dict[str, int] = {}
    observed_mismatch_counts: dict[str, int] = {}
    for item in measured:
        failure_type = item["result"].get("failure_type")
        if failure_type:
            failure_counts[failure_type] = failure_counts.get(failure_type, 0) + 1
        observed_mismatch = item["result"].get("observed_mismatch")
        if observed_mismatch:
            observed_mismatch_counts[observed_mismatch] = observed_mismatch_counts.get(observed_mismatch, 0) + 1
    summary["failure_counts"] = failure_counts
    summary["observed_mismatch_counts"] = observed_mismatch_counts
    return summary


def print_table(results: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    for item in results:
        status = "PASS" if item["result"]["passed"] else "FAIL"
        failure = item["result"].get("failure_type") or ""
        print(f"{item['id']:<28} {status:<5} {failure}")
    print()
    for key, value in summary.items():
        print(f"{key}: {value}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run IT Helpdesk Agent live evals.")
    parser.add_argument("--phase", choices=["B"], default="B")
    parser.add_argument("--suite", choices=["base", "group", "cross", "extension", "adversarial"], default="base", help="Run label saved to JSON; does not filter --eval-cases.")
    parser.add_argument("--version", required=True)
    parser.add_argument("--provider", choices=["openai", "openrouter", "anthropic", "gemini"], required=True)
    parser.add_argument("--model", default=None)
    parser.add_argument("--system-prompt", type=Path, default=ARTIFACTS_DIR / "system_prompt.md")
    parser.add_argument("--tools", type=Path, default=ARTIFACTS_DIR / "tools.yaml")
    parser.add_argument("--eval-cases", type=Path, default=DATA_DIR / "eval_base.json")
    parser.add_argument("--runs-dir", type=Path, default=ROOT / "runs")
    args = parser.parse_args()

    system_prompt = args.system_prompt.read_text(encoding="utf-8")
    artifact_version = build_artifact_version(args.version, args.system_prompt, args.tools)
    provider = make_provider(args.provider)
    selected_model = args.model or getattr(provider, "default_model", None)
    dataset_info = load_dataset_info(args.eval_cases)
    cases = load_cases(args.eval_cases, args.phase)
    if not cases:
        raise SystemExit(f"No cases matched phase={args.phase!r} in {args.eval_cases}")

    tool_declarations = load_tool_declarations(args.tools)
    validate_expected_tools(cases, tool_declarations, args.eval_cases)
    openai_tools = to_openai_tools(tool_declarations)

    results: list[dict[str, Any]] = []
    for case in cases:
        print(f"Running {case['id']}...", flush=True)
        agent = HelpdeskAgent(provider, system_prompt=system_prompt, tools=openai_tools, model=args.model)
        try:
            tool_choice = None if case["expect"].get("no_tool") else "required"
            run = agent.run(case_messages(case), tool_choice=tool_choice)
            calls = [{"name": call.name, "args": call.args} for call in run.tool_calls]
            result = evaluate_phase_b(case, calls, run.text)
            tool_results = run.tool_results
        except Exception as exc:
            calls = []
            tool_results = []
            result = {
                "passed": False,
                "failure_type": "provider_error",
                "case_failure_type": case.get("failure_type"),
                "observed_mismatch": "provider_error",
                "failures": [f"{type(exc).__name__}: {str(exc)}"],
                "actual_tool_calls": [],
                "actual_text": None,
                "routing_correct": False,
                "args_correct": False,
            }
        results.append({
            "id": case["id"],
            "phase": case["phase"],
            "suite": args.suite,
            "case_suite": case.get("suite", args.suite),
            "is_multiturn": "turns" in case,
            "metadata": case.get("metadata", {}),
            "input": case.get("input") or case.get("query") or case.get("turns"),
            "expect": case["expect"],
            "result": result,
            "tool_results": tool_results,
        })

    summary = summarize(results)
    args.runs_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now()
    generated_at = now.isoformat(timespec="seconds")
    timestamp = now.strftime("%Y%m%dT%H%M%S%f")
    run_id = "_".join([
        safe_slug(args.version),
        safe_slug(args.phase),
        safe_slug(args.suite),
        safe_slug(args.provider),
        timestamp,
    ])
    payload = {
        "run_id": run_id,
        "version": args.version,
        **artifact_version_dict(artifact_version),
        "phase": args.phase,
        "suite": args.suite,
        "provider": args.provider,
        "model": selected_model,
        "system_prompt": str(args.system_prompt),
        "tools": str(args.tools),
        "eval_cases": str(args.eval_cases),
        **dataset_info,
        "generated_at": generated_at,
        "summary": summary,
        "results": results,
    }

    out_path = args.runs_dir / f"{run_id}.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print_table(results, summary)
    print(f"\nArtifact version: {artifact_version.artifact_version}")
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
