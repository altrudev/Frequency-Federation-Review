"""Local runner control-flow tests with stubbed git/npm/node; no external run."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CAPSULE = Path("capsules/aps-priorseal-v0.1")
REVIEW = "a" * 40


class RunPinnedTests(unittest.TestCase):
    def test_verification_status_propagates(self):
        for stage, code, expected in (
            ("ci", 17, ["ci"]),
            ("selftest", 23, ["ci", "selftest"]),
            ("verify", 31, ["ci", "selftest", "verify"]),
            ("none", 0, ["ci", "selftest", "verify"]),
        ):
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as tmp:
                base = Path(tmp)
                repo = base / "review"
                shutil.copytree(ROOT / CAPSULE, repo / CAPSULE)
                bin_dir = base / "bin"
                bin_dir.mkdir()
                stubs = {
                    "git": '''#!/bin/bash
if [[ "$*" == *"status --porcelain" ]]; then exit 0; fi
case "$2" in
  */review) echo aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa ;;
  */aps) echo 948f99b85343bef2c6fa677c8543965caacfc087 ;;
  */priorseal) echo d749d2691c3e6be139de4020e7b27cdafca2c428 ;;
  *) exit 99 ;;
esac
''',
                    "npm": '''#!/bin/bash
stage=ci
if [[ "$1" == run ]]; then stage=selftest; fi
echo "$stage" >> "$CALL_LOG"
if [[ "$FAIL_STAGE" == "$stage" ]]; then exit "$FAIL_CODE"; fi
''',
                    "node": '''#!/bin/bash
echo verify >> "$CALL_LOG"
if [[ "$FAIL_STAGE" == verify ]]; then exit "$FAIL_CODE"; fi
''',
                }
                for name, body in stubs.items():
                    path = bin_dir / name
                    path.write_text(body)
                    path.chmod(0o755)
                attempt = base / "attempt"
                log = base / "calls"
                result = subprocess.run(
                    ["bash", str(repo / CAPSULE / "run-pinned.sh"),
                     "--repo", str(repo), "--adapter-commit", REVIEW,
                     "--aps-repo", str(base / "aps"),
                     "--priorseal-repo", str(base / "priorseal"),
                     "--attempt-dir", str(attempt)],
                    env={**os.environ, "PATH": f"{bin_dir}:{os.environ['PATH']}",
                         "FAIL_STAGE": stage, "FAIL_CODE": str(code),
                         "CALL_LOG": str(log)},
                    capture_output=True, text=True,
                )
                self.assertEqual(result.returncode, code, result.stderr)
                self.assertEqual((attempt / "exit-status.txt").read_text(), f"{code}\n")
                self.assertEqual(log.read_text().splitlines(), expected)
                self.assertEqual("PASS:" in result.stdout, code == 0)
                self.assertTrue((attempt / "run-metadata.txt").is_file())
                # Stubs never create a verification report, even on success.
                self.assertFalse((attempt / "frequency-run-report.json").exists())


if __name__ == "__main__":
    unittest.main()
