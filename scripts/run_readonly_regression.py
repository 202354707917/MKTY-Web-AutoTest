from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
FRONTEND_URL = "http://localhost:8088"
EXPECTED_ALLURE_VERSION = "2.46.1"
TEST_MARKERS = "ui and readonly and not write"
TEST_PATH = "tests/ui"

REQUIRED_CREDENTIALS = (
    "MKTY_UI_TEST_USERNAME",
    "MKTY_UI_TEST_PASSWORD",
    "MKTY_DOCTOR_USERNAME",
    "MKTY_DOCTOR_PASSWORD",
)


class PipelineError(RuntimeError):
    """Raised when the read-only regression pipeline cannot continue."""


def log(message: str) -> None:
    print(message, flush=True)


def get_python_path() -> Path:
    """Return the project's virtual-environment Python interpreter."""
    python_path = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"

    if not python_path.is_file():
        raise PipelineError(
            f"Project virtual-environment Python was not found: {python_path}"
        )

    return python_path


def check_credentials() -> None:
    """Check that required variables exist without printing their values."""
    missing = []

    for name in REQUIRED_CREDENTIALS:
        value = os.environ.get(name)

        if value is None or not value.strip():
            log(f"{name}=MISSING")
            missing.append(name)
        else:
            log(f"{name}=SET")

    if missing:
        raise PipelineError(
            "One or more read-only UI test credential variables are missing."
        )


def check_frontend() -> None:
    """Require the local frontend to return HTTP 200."""
    request = urllib.request.Request(
        FRONTEND_URL,
        method="GET",
        headers={"User-Agent": "MKTY-Readonly-Regression/1.0"},
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            status_code = response.status
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise PipelineError(
            f"Frontend {FRONTEND_URL} is not accessible."
        ) from exc

    if status_code != 200:
        raise PipelineError(
            f"Frontend {FRONTEND_URL} returned HTTP {status_code}, expected 200."
        )

    log(f"Frontend check passed: HTTP {status_code}")


def create_report_directories(
    report_run_id: str | None,
) -> tuple[Path, Path, Path]:
    """Create isolated result directories and never reuse existing paths."""
    if report_run_id:
        if not re.fullmatch(r"\d{8}_\d{6}-[a-f0-9]{32}", report_run_id):
            raise PipelineError(
                "ReportRunId must match YYYYMMDD_HHMMSS- followed by 32 lowercase hex characters."
            )
        run_id = report_run_id
    else:
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    base_junit = ARTIFACTS_DIR / f"junit-readonly-regression-{run_id}"
    base_allure = ARTIFACTS_DIR / f"allure-results-readonly-regression-{run_id}"
    base_report = ARTIFACTS_DIR / f"allure-report-readonly-regression-{run_id}"

    candidates = (base_junit, base_allure, base_report)

    if report_run_id and any(path.exists() for path in candidates):
        raise PipelineError(
            f"Report directories already exist for run {report_run_id}; refusing to reuse them."
        )

    suffix = 0

    while any(path.exists() for path in candidates):
        suffix += 1
        candidates = (
            Path(f"{base_junit}-{suffix}"),
            Path(f"{base_allure}-{suffix}"),
            Path(f"{base_report}-{suffix}"),
        )

    junit_dir, allure_results_dir, report_dir = candidates

    # Create each directory exclusively. If a concurrent run races with us,
    # fail rather than reuse another run's output.
    created: list[Path] = []

    try:
        for directory in candidates:
            directory.mkdir(parents=True, exist_ok=False)
            created.append(directory)
    except OSError as exc:
        # Do not delete any directories here; preserve all evidence.
        raise PipelineError(
            f"Could not create an isolated report directory: {exc}"
        ) from exc

    log(f"JUnit directory: {junit_dir}")
    log(f"Allure raw results directory: {allure_results_dir}")
    log(f"Allure HTML directory: {report_dir}")

    return junit_dir, allure_results_dir, report_dir


def run_pytest(
    python_path: Path,
    junit_path: Path,
    allure_results_dir: Path,
) -> int:
    """Run only the UI readonly regression tests and preserve the exit code."""
    command = [
        str(python_path),
        "-m",
        "pytest",
        "-v",
        f"--junitxml={junit_path}",
        f"--alluredir={allure_results_dir}",
        "-m",
        TEST_MARKERS,
        TEST_PATH,
    ]

    log("Starting pytest read-only regression.")
    log(f"Test selection: {TEST_MARKERS}")

    try:
        completed = subprocess.run(command, cwd=PROJECT_ROOT, check=False)
    except OSError as exc:
        raise PipelineError(f"pytest could not be started: {exc}") from exc

    log(f"pytest exit code: {completed.returncode}")
    return completed.returncode


def validate_junit(junit_path: Path) -> dict[str, int]:
    """Validate JUnit XML structure and aggregate test statistics."""
    if not junit_path.is_file():
        raise PipelineError(f"JUnit XML report was not generated: {junit_path}")

    try:
        root = ElementTree.parse(junit_path).getroot()
    except (ElementTree.ParseError, OSError) as exc:
        raise PipelineError(f"JUnit XML is invalid: {exc}") from exc

    if root.tag != "testsuites":
        raise PipelineError("JUnit XML does not contain a testsuites root element.")

    stat_names = ("tests", "failures", "errors", "skipped")
    nodes = [root] if "tests" in root.attrib else root.findall("./testsuite")

    if not nodes:
        raise PipelineError(
            "JUnit XML has no root tests attribute or direct testsuite nodes."
        )

    stats = {name: 0 for name in stat_names}

    for node in nodes:
        for name in stat_names:
            raw_value = node.get(name)

            if name == "tests" and (
                raw_value is None or not raw_value.isdigit()
            ):
                raise PipelineError(
                    "JUnit XML tests attribute must be a non-negative integer."
                )

            if raw_value is None:
                value = 0
            elif raw_value.isdigit():
                value = int(raw_value)
            else:
                raise PipelineError(
                    f"JUnit XML {name} attribute must be a non-negative integer."
                )

            stats[name] += value

    test_cases = root.findall(".//testcase")

    if stats["tests"] > 0 and not test_cases:
        raise PipelineError("JUnit XML reports tests but contains no testcase nodes.")

    if sum(stats[name] for name in ("failures", "errors", "skipped")) > stats["tests"]:
        raise PipelineError("JUnit XML outcome counts exceed the tests count.")

    if stats["tests"] == 0:
        raise PipelineError(
            "JUnit XML is valid but contains zero tests; regression requires executed tests."
        )

    stats["passed"] = (
        stats["tests"] - stats["failures"] - stats["errors"] - stats["skipped"]
    )

    log(
        "Test summary: "
        f"total={stats['tests']} "
        f"passed={stats['passed']} "
        f"failed={stats['failures']} "
        f"errors={stats['errors']} "
        f"skipped={stats['skipped']}"
    )

    return stats


def validate_allure_results(allure_results_dir: Path) -> None:
    """Validate Allure result and container JSON files."""
    if not allure_results_dir.is_dir():
        raise PipelineError(
            f"Allure raw results directory was not generated: {allure_results_dir}"
        )

    result_files = [
        path
        for path in allure_results_dir.iterdir()
        if path.is_file()
        and (
            path.name.endswith("-result.json")
            or path.name.endswith("-container.json")
        )
    ]

    if not result_files:
        raise PipelineError(
            "Allure raw results contain no result or container JSON files."
        )

    valid_statuses = {"passed", "failed", "broken", "skipped", "unknown"}

    for path in result_files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise PipelineError(
                f"Invalid Allure result JSON '{path.name}': {exc}"
            ) from exc

        if not isinstance(data, dict) or not isinstance(data.get("uuid"), str) or not data["uuid"].strip():
            raise PipelineError(
                f"Invalid Allure result JSON '{path.name}': missing required uuid."
            )

        if path.name.endswith("-result.json"):
            if not isinstance(data.get("name"), str) or not data["name"].strip():
                raise PipelineError(
                    f"Allure result file '{path.name}' is missing required name."
                )

            status = data.get("status")
            if not isinstance(status, str) or status.lower() not in valid_statuses:
                raise PipelineError(
                    f"Allure result file '{path.name}' has an unsupported status."
                )

        if path.name.endswith("-container.json"):
            children = data.get("children")

            if not isinstance(children, list):
                raise PipelineError(
                    f"Allure container '{path.name}' is missing children."
                )

            if any(not isinstance(child, str) or not child.strip() for child in children):
                raise PipelineError(
                    f"Allure container '{path.name}' has invalid children UUIDs."
                )

    log(f"Allure raw result files validated: {len(result_files)}")


def find_allure_cli() -> Path:
    """Resolve Allure CLI from the project tools directory or environment."""
    configured = os.environ.get("MKTY_ALLURE_CLI", "").strip()
    project_cli = (
        PROJECT_ROOT / "tools" / "allure" / "allure-2.46.1" / "bin" / "allure.bat"
    )

    candidates = [project_cli]

    if configured:
        candidates.insert(0, Path(configured))

    for candidate in candidates:
        if candidate.is_file() and candidate.name.lower() == "allure.bat":
            return candidate.resolve()

    raise PipelineError(
        "Allure CLI 2.46.1 was not found. Ensure the project's Allure CLI exists "
        "or set MKTY_ALLURE_CLI to an existing allure.bat file."
    )

def run_allure_command(
    allure_cli: Path,
    *arguments: str,
) -> subprocess.CompletedProcess[str]:
    """Run a Windows batch file through cmd.exe and return its exit code."""
    if not allure_cli.is_file():
        raise PipelineError(f"Allure CLI file not found: {allure_cli}")

    # Quote the batch-file path and every argument for Windows command parsing.
    quoted_args = subprocess.list2cmdline(
        [str(allure_cli), *arguments]
    )

    # CALL ensures control returns from the batch file to cmd.exe.
    command_line = f"call {quoted_args}"
    command = ["cmd.exe", "/d", "/s", "/c", command_line]

    try:
        return subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError as exc:
        raise PipelineError(
            f"Allure CLI command could not be started: {exc}"
        ) from exc


def generate_allure_report(
    allure_cli: Path,
    allure_results_dir: Path,
    report_dir: Path,
) -> None:
    """Verify the CLI version and generate the static HTML report."""
    version_result = run_allure_command(allure_cli, "--version")
    version_output = (version_result.stdout or "") + (version_result.stderr or "")

    if (
        version_result.returncode != 0
        or not re.search(
            r"(?<!\d)2\.46\.1(?!\d)",
            version_output,
        )
    ):
        raise PipelineError(
            "Unsupported Allure CLI version. Expected 2.46.1; "
            f"received exit code {version_result.returncode}."
        )

    log(f"Using Allure CLI 2.46.1: {allure_cli}")

    result = run_allure_command(
        allure_cli,
        "generate",
        str(allure_results_dir),
        "--output",
        str(report_dir),
    )

    if result.returncode != 0:
        raise PipelineError(
            f"Allure HTML generation failed with exit code {result.returncode}."
        )

    index_path = report_dir / "index.html"

    if not index_path.is_file():
        raise PipelineError(
            f"Allure HTML report index.html was not generated: {index_path}"
        )

    log(f"Allure HTML report: {report_dir}")

def open_allure_report(allure_cli: Path, allure_results_dir: Path) -> None:
    """Start the local Allure report server and open it in the browser."""
    if not allure_cli.is_file():
        raise PipelineError(f"Allure CLI file not found: {allure_cli}")

    command_line = subprocess.list2cmdline(
        [str(allure_cli), "open", str(allure_results_dir)]
    )
    command = [
        "cmd.exe",
        "/d",
        "/s",
        "/c",
        f'call "{command_line}"',
    ]

    log("Starting the local Allure report server...")

    try:
        subprocess.Popen(
            command,
            cwd=PROJECT_ROOT,
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )
    except OSError as exc:
        raise PipelineError(
            f"Could not start the local Allure report server: {exc}"
        ) from exc

    log("Allure report server process launched.")

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the MKTY read-only UI regression and generate reports."
    )
    parser.add_argument(
        "--ci",
        action="store_true",
        help="Run in CI mode; generate reports without opening a report server.",
    )
    parser.add_argument(
        "--report-run-id",
        help="Unique run ID in YYYYMMDD_HHMMSS-<32 lowercase hex> format.",
    )
    args = parser.parse_args()

    pytest_exit_code = 2

    try:
        os.chdir(PROJECT_ROOT)
        python_path = get_python_path()
        check_credentials()
        check_frontend()

        junit_dir, allure_results_dir, report_dir = create_report_directories(
            args.report_run_id
        )
        junit_path = junit_dir / "junit.xml"

        pytest_exit_code = run_pytest(
            python_path,
            junit_path,
            allure_results_dir,
        )

        # Validate reports even when pytest failed, preserving diagnostic output.
        validate_junit(junit_path)
        validate_allure_results(allure_results_dir)

        allure_cli = find_allure_cli()
        generate_allure_report(allure_cli, allure_results_dir, report_dir)
        if not args.ci:
            open_allure_report(allure_cli, allure_results_dir)
        if pytest_exit_code != 0:
            return pytest_exit_code

        log("Read-only regression pipeline completed successfully.")
        return 0

    except PipelineError as exc:
        log(f"ERROR: {exc}")
        return pytest_exit_code if pytest_exit_code != 0 else 1
    except KeyboardInterrupt:
        log("Interrupted by user.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
