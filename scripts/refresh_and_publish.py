# SPDX-FileCopyrightText: © Sebastian Thomschke and contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-ArtifactOfProjectHomePage: https://github.com/Second-Hand-Friends/kleinanzeigen-bot/
"""Run the local refresh workflow step by step, aborting on the first failure:

1. git fetch + rebase onto origin/main
2. pdm install
3. delete the "downloaded-ads" folder
4. download all ads
5. publish all ads
"""
import os, shutil, stat, subprocess, sys  # isort: skip  # noqa: S404
from collections.abc import Callable
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOWNLOAD_DIR = PROJECT_ROOT / "downloaded-ads"


def run(cmd:list[str]) -> None:
    print(f"\n>>> {' '.join(cmd)}", flush = True)
    result = subprocess.run(cmd, cwd = PROJECT_ROOT, check = False)  # noqa: S603
    if result.returncode != 0:
        print(f"\n!!! Command failed with exit code {result.returncode}: {' '.join(cmd)}", flush = True)
        sys.exit(result.returncode)


def delete_download_dir() -> None:
    print(f"\n>>> deleting {DOWNLOAD_DIR}", flush = True)
    if not DOWNLOAD_DIR.exists():
        print("    (does not exist, nothing to delete)", flush = True)
        return

    def make_writable_and_retry(func:Callable[..., Any], path:str, _exc:BaseException) -> None:
        os.chmod(path, stat.S_IWRITE)  # read-only files cannot be deleted on Windows
        func(path)

    shutil.rmtree(DOWNLOAD_DIR, onexc = make_writable_and_retry)


def main() -> None:
    git = shutil.which("git")
    if git is None:
        sys.exit("!!! 'git' not found on PATH")
    pdm = shutil.which("pdm")
    if pdm is None:
        sys.exit("!!! 'pdm' not found on PATH")
    bot = [sys.executable, "-m", "kleinanzeigen_bot"]

    run([git, "fetch", "origin"])
    run([git, "rebase", "origin/main"])  # on conflicts git exits non-zero and leaves the rebase for manual resolution
    run([pdm, "install"])
    delete_download_dir()
    run([*bot, "download", "--ads=all"])
    run([*bot, "publish", "--ads=all"])
    print("\n>>> All steps completed successfully.", flush = True)


if __name__ == "__main__":
    main()
