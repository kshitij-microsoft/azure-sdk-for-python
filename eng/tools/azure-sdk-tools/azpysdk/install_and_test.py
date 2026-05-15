import argparse
import os
import sys
from subprocess import CalledProcessError
from typing import Dict, List, Optional

from .Check import Check, DEPENDENCY_TOOLS_REQUIREMENTS, PACKAGING_REQUIREMENTS, TEST_TOOLS_REQUIREMENTS

from ci_tools.functions import is_error_code_5_allowed, install_into_venv
from ci_tools.scenario.generation import create_package_and_install
from ci_tools.variables import discover_repo_root, set_envvar_defaults
from ci_tools.logging import logger

REPO_ROOT = discover_repo_root()


class InstallAndTest(Check):
    """Shared implementation for build-and-test style checks."""

    def __init__(
        self,
        *,
        package_type: str,
        proxy_url: Optional[str],
        display_name: str,
        additional_pytest_args: Optional[List[str]] = None,
        coverage_enabled: bool = True,
    ) -> None:
        super().__init__()
        self.package_type = package_type
        self.proxy_url = proxy_url
        self.display_name = display_name
        self.additional_pytest_args = list(additional_pytest_args or [])
        self.coverage_enabled = coverage_enabled

    def register(
        self, subparsers: "argparse._SubParsersAction", parent_parsers: Optional[List[argparse.ArgumentParser]] = None
    ) -> None:
        raise NotImplementedError

    def run(self, args: argparse.Namespace) -> int:
        logger.info(f"Running {self.display_name} check...")

        env_defaults = self.get_env_defaults()
        if env_defaults:
            set_envvar_defaults(env_defaults)

        targeted = self.get_targeted_directories(args)
        if not targeted:
            logger.warning(f"No target packages discovered for {self.display_name} check.")
            return 0

        results: List[int] = []

        for parsed in targeted:
            if os.getcwd() != parsed.folder:
                os.chdir(parsed.folder)
            package_dir = parsed.folder
            package_name = parsed.name

            executable, staging_directory = self.get_executable(
                args.isolate,
                args.command,
                sys.executable,
                package_dir,
                python_version=getattr(args, "python_version", None),
            )
            logger.info(f"Processing {package_name} using interpreter {executable}")

            install_result = self.install_all_requirements(
                executable, staging_directory, package_name, package_dir, args
            )
            if install_result != 0:
                results.append(install_result)
                continue

            pytest_args = self._build_pytest_args(package_dir, args)
            pytest_result = self.run_pytest(executable, staging_directory, package_dir, package_name, pytest_args)
            if pytest_result != 0:
                results.append(pytest_result)
                continue

            if not self.coverage_enabled:
                continue

            coverage_result = self.check_coverage(executable, package_dir, package_name)
            if coverage_result != 0:
                results.append(coverage_result)

        return max(results) if results else 0

    def check_coverage(self, executable: str, package_dir: str, package_name: str) -> int:
        coverage_command = [
            os.path.join(REPO_ROOT, "eng/scripts/run_coverage.py"),
            "-t",
            package_dir,
            "-r",
            REPO_ROOT,
        ]
        coverage_result = self.run_venv_command(executable, coverage_command, cwd=package_dir)
        if coverage_result.returncode != 0:
            logger.error(f"Coverage generation failed for {package_name} with exit code {coverage_result.returncode}.")
            if coverage_result.stdout:
                logger.error(coverage_result.stdout)
            if coverage_result.stderr:
                logger.error(coverage_result.stderr)
            return coverage_result.returncode
        return 0

    def run_pytest(
        self, executable: str, staging_directory: str, package_dir: str, package_name: str, pytest_args: List[str]
    ) -> int:
        # Probe: previous bash-wrap probe showed pytest writes ZERO bytes before
        # SIGABRT (rc=134) -> the abort is in PyPy interpreter / site init, not in
        # any user import. This probe binary-searches the cause:
        #   1. python -V                 (does the interpreter even start?)
        #   2. python -c 'print("hi")'   (does site init complete?)
        #   3. python -c 'import azure.core'      etc, one suspect at a time
        # Each step is captured to its own log; the FIRST step that aborts is
        # the culprit. Then we still try the real pytest invocation.
        log_dir = staging_directory
        try:
            os.makedirs(log_dir, exist_ok=True)
        except Exception:
            pass

        def _q(s: str) -> str:
            return "'" + s.replace("'", "'\\''") + "'"

        probe_steps = [
            ("00_version", [executable, "-V"]),
            ("01_print",   [executable, "-S", "-c", "print('hi')"]),  # -S skips site
            ("02_site",    [executable, "-c", "print('hi')"]),         # with site
            ("03_psutil",  [executable, "-c", "import psutil; print(psutil.__version__)"]),
            ("04_otelapi", [executable, "-c", "import opentelemetry; print(opentelemetry.__file__)"]),
            ("05_otelsdk", [executable, "-c", "import opentelemetry.sdk; print(opentelemetry.sdk.__file__)"]),
            ("06_azmon",   [executable, "-c", "import azure.monitor.opentelemetry; print('azmon ok')"]),
            ("07_azmonexp",[executable, "-c", "import azure.monitor.opentelemetry.exporter; print('exp ok')"]),
            ("08_azcore",  [executable, "-c", "import azure.core; print(azure.core.__version__)"]),
            ("09_azid",    [executable, "-c", "import azure.identity; print(azure.identity.__version__)"]),
            ("10_aiml",    [executable, "-c", "import azure.ai.ml; print('aiml ok')"]),
            ("11_pytest",  [executable, "-c", "import pytest; print(pytest.__version__)"]),
        ]

        probe_lines = ["echo '=== probe: starting incremental import probes ==='"]
        for name, cmd in probe_steps:
            log_path = os.path.join(log_dir, f"probe_{name}.log")
            cmd_str = " ".join(_q(a) for a in cmd)
            probe_lines.append(f"echo '--- probe step {name} ---'")
            probe_lines.append(f"set +e; ({cmd_str}) >{_q(log_path)} 2>&1; rc=$?; set -e")
            probe_lines.append(f"echo '  rc='$rc")
            probe_lines.append(f"cat {_q(log_path)} | sed 's/^/  out| /'")
            probe_lines.append(
                f"if [ $rc -ne 0 ]; then echo '*** probe step {name} FAILED with rc='$rc' ***'; fi"
            )

        # Then attempt the real pytest run, capturing stderr separately
        inner_args = [executable, "-X", "faulthandler", "-X", "dev", "-X", "importtime", "-u", "-m", "pytest", *pytest_args]
        inner_cmd = " ".join(_q(a) for a in inner_args)
        pytest_stdout = os.path.join(log_dir, "pytest_stdout.log")
        pytest_stderr = os.path.join(log_dir, "pytest_stderr.log")
        probe_lines.append("echo '=== probe: launching real pytest ==='")
        probe_lines.append(
            f"set +e; ({inner_cmd}) >{_q(pytest_stdout)} 2>{_q(pytest_stderr)}; rc=$?; set -e"
        )
        probe_lines.append("echo '=== probe: pytest exited with rc='$rc' ==='")
        probe_lines.append("echo '--- pytest stdout (last 200 lines) ---'")
        probe_lines.append(f"tail -n 200 {_q(pytest_stdout)} | sed 's/^/  stdout| /'")
        probe_lines.append("echo '--- pytest stderr (last 200 lines) ---'")
        probe_lines.append(f"tail -n 200 {_q(pytest_stderr)} | sed 's/^/  stderr| /'")
        probe_lines.append("echo '--- byte counts ---'")
        probe_lines.append(f"wc -c {_q(pytest_stdout)} {_q(pytest_stderr)} 2>/dev/null || true")
        probe_lines.append("exit $rc")

        bash_script = "\n".join(probe_lines)
        pytest_command = ["/bin/bash", "-c", bash_script]

        environment = os.environ.copy()
        environment.update(
            {
                "PYTHONPYCACHEPREFIX": staging_directory,
                "PYTHONFAULTHANDLER": "1",
                "PYTHONUNBUFFERED": "1",
            }
        )

        logger.info(f"Running pytest probe for {package_name} (incremental import diagnostic)")

        pytest_result = self.run_venv_command(
            executable,
            pytest_command,
            cwd=package_dir,
            immediately_dump=True,
            additional_environment_settings=environment,
            append_executable=False,
        )
        if pytest_result.returncode != 0:
            if pytest_result.returncode == 5 and is_error_code_5_allowed(package_dir, package_name):
                logger.info(
                    "pytest exited with code 5 for %s, which is allowed for management or opt-out packages.",
                    package_name,
                )
                # Skip coverage when tests are skipped entirely
                return 0
            else:
                logger.error(f"pytest failed for {package_name} with exit code {pytest_result.returncode}.")
                return pytest_result.returncode
        return 0

    def install_all_requirements(
        self, executable: str, staging_directory: str, package_name: str, package_dir: str, args: argparse.Namespace
    ) -> int:
        try:
            self._install_common_requirements(executable, package_dir)
            if self.should_install_dev_requirements():
                self.install_dev_reqs(executable, args, package_dir)
        except CalledProcessError as exc:
            logger.error(f"Failed to prepare dependencies for {package_name}: {exc}")
            return exc.returncode or 1

        try:
            create_package_and_install(
                distribution_directory=staging_directory,
                target_setup=package_dir,
                skip_install=False,
                cache_dir=None,
                work_dir=staging_directory,
                force_create=False,
                package_type=self.package_type,
                pre_download_disabled=False,
                python_executable=executable,
            )
        except CalledProcessError as exc:
            logger.error(f"Failed to build/install {self.package_type} for {package_name}: {exc}")
            return 1
        return 0

    def get_env_defaults(self) -> Dict[str, str]:
        defaults: Dict[str, str] = {}

        if os.getenv("PROXY_URL") is not None:
            defaults["PROXY_URL"] = str(os.getenv("PROXY_URL"))
        if self.proxy_url:
            defaults["PROXY_URL"] = self.proxy_url
        return defaults

    def should_install_dev_requirements(self) -> bool:
        return True

    def _install_common_requirements(self, executable: str, package_dir: str) -> None:
        install_into_venv(executable, PACKAGING_REQUIREMENTS, package_dir)

        if os.path.exists(TEST_TOOLS_REQUIREMENTS):
            install_into_venv(executable, ["-r", TEST_TOOLS_REQUIREMENTS], package_dir)
        else:
            logger.warning(f"Test tools requirements file not found at {TEST_TOOLS_REQUIREMENTS}.")

    def _build_pytest_args(self, package_dir: str, args: argparse.Namespace) -> List[str]:
        return self._build_pytest_args_base(
            package_dir,
            args,
            ignore_globs=["**/.venv*", "**/.venv*/**"],
            extra_args=self.additional_pytest_args,
            test_target=package_dir,
        )
