"""
runner.py – Build the C scheduler binary and invoke it.

Works on Windows (gcc directly, no make required) and Linux/macOS.
Import this from gui.py, compare.py, etc.  Never run as __main__.
"""

import subprocess
import sys
import os
import glob

# ── Platform detection ────────────────────────────────────────────
IS_WINDOWS = sys.platform == "win32"

# ── Path constants ────────────────────────────────────────────────
ROOT_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C_DIR       = os.path.join(ROOT_DIR, "c_code")
OUTPUT_DIR  = os.path.join(ROOT_DIR, "output")
OUTPUT_JSON = os.path.join(OUTPUT_DIR, "output.json")

# Binary name differs on Windows (.exe) vs Unix (no extension)
_BIN_NAME = "scheduler.exe" if IS_WINDOWS else "scheduler"
BINARY    = os.path.join(C_DIR, _BIN_NAME)

# All C source files that must be compiled together
_C_SOURCES = [
    "common.c", "fcfs.c", "sjf.c", "srtf.c",
    "priority_np.c", "priority_p.c", "round_robin.c",
]


# ── Compilation ───────────────────────────────────────────────────

def _source_newer_than_binary() -> bool:
    """Return True if any .c or .h file is newer than the binary."""
    if not os.path.exists(BINARY):
        return True
    bin_mtime = os.path.getmtime(BINARY)
    for pattern in ("*.c", "*.h"):
        for path in glob.glob(os.path.join(C_DIR, pattern)):
            if os.path.getmtime(path) > bin_mtime:
                return True
    return False


def build_c(force: bool = False) -> None:
    """
    Compile the C scheduler with gcc directly (no make needed).

    Recompiles when:
    - *force* is True
    - the binary does not exist
    - any .c / .h source file is newer than the binary

    Raises RuntimeError with the compiler stderr on failure.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if not force and not _source_newer_than_binary():
        return  # binary is already up-to-date

    sources = [os.path.join(C_DIR, s) for s in _C_SOURCES]

    # Verify all source files are present
    missing = [s for s in sources if not os.path.exists(s)]
    if missing:
        raise RuntimeError(
            "Missing source files:\n" + "\n".join(missing) +
            "\nMake sure the c_code/ folder is complete."
        )

    cmd = ["gcc", "-Wall", "-O2", "-std=c11"] + sources + ["-o", BINARY]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=C_DIR,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Build failed (gcc returned {result.returncode}):\n"
            f"{result.stderr or result.stdout}"
        )


# ── Scheduling ────────────────────────────────────────────────────

def run_scheduler(algo: str, processes: list[dict],
                  quantum: int | None = None) -> None:
    """
    Invoke the compiled C binary with the given process list.

    Each dict in *processes* needs: pid, at, bt, priority.
    Raises subprocess.CalledProcessError on non-zero exit.
    """
    if not os.path.exists(BINARY):
        raise RuntimeError(
            "Scheduler binary not found. "
            "Call build_c() before run_scheduler()."
        )

    args = [BINARY, "--algo", algo]
    for p in processes:
        args += [
            "--pid",      str(p["pid"]),
            "--at",       str(p["at"]),
            "--bt",       str(p["bt"]),
            "--priority", str(p.get("priority", 0)),
        ]
    if quantum is not None:
        args += ["--quantum", str(quantum)]

    subprocess.run(args, check=True, cwd=ROOT_DIR)


def run_scheduler_from_file(algo: str, file_path: str,
                             quantum: int | None = None) -> None:
    """Run the scheduler using a pre-written .txt input file."""
    if not os.path.exists(BINARY):
        raise RuntimeError("Scheduler binary not found. Call build_c() first.")

    args = [BINARY, "--file", file_path, "--algo", algo]
    if quantum is not None:
        args += ["--quantum", str(quantum)]

    subprocess.run(args, check=True, cwd=ROOT_DIR)
