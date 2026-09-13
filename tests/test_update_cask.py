# SPDX-License-Identifier: GPL-3.0-or-later
import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("update_cask", ROOT / "scripts/update_cask.py")
updater = importlib.util.module_from_spec(spec)
spec.loader.exec_module(updater)

CURRENT = "2026.08.24.1"
NEXT = "2026.09.13.0"
OLD_HASH = "a" * 64
NEW_HASH = "b" * 64
CASK = f'''cask "komai" do
  version "{CURRENT}"
  sha256 "{OLD_HASH}"
  app "komai.app"
end
'''


def release():
    name = f"komai-{NEXT}-macos-arm64.dmg"
    return {
        "tag_name": f"v{NEXT}",
        "draft": False,
        "prerelease": False,
        "assets": [{
            "name": name,
            "state": "uploaded",
            "size": 12345,
            "digest": f"sha256:{NEW_HASH}",
            "browser_download_url": f"https://github.com/etkecc/komai/releases/download/v{NEXT}/{name}",
        }],
    }


class ReleaseTests(unittest.TestCase):
    def test_stable_release(self):
        self.assertEqual(updater.release_candidate(release()), (NEXT, NEW_HASH))

    def test_reject_drafts_prereleases_and_invalid_tags(self):
        for field, value in (("draft", True), ("prerelease", True), ("draft", None),
                             ("tag_name", "v2026.09.13.0\nchanged=true"),
                             ("tag_name", 'v2026.09.13.0"; system("bad")'),
                             ("tag_name", "v2026.02.30.0")):
            with self.subTest(field=field, value=value):
                data = release()
                data[field] = value
                with self.assertRaises(ValueError):
                    updater.release_candidate(data)

    def test_reject_missing_or_duplicate_asset(self):
        for assets in (None, [], release()["assets"] * 2):
            with self.subTest(assets=assets):
                data = release()
                data["assets"] = assets
                with self.assertRaises(ValueError):
                    updater.release_candidate(data)

    def test_reject_wrong_asset_or_unusable_digest(self):
        for field, value in (("name", "komai-other-macos-arm64.dmg"),
                             ("browser_download_url", "https://example.com/komai.dmg"),
                             ("state", "new"), ("size", 0), ("size", True),
                             ("digest", None), ("digest", "sha256:invalid")):
            with self.subTest(field=field, value=value):
                data = release()
                data["assets"][0][field] = value
                with self.assertRaises(ValueError):
                    updater.release_candidate(data)

    def test_other_architecture_assets_are_ignored(self):
        data = release()
        other = copy.deepcopy(data["assets"][0])
        other["name"] = "komai-linux.AppImage"
        data["assets"].insert(0, other)
        self.assertEqual(updater.release_candidate(data), (NEXT, NEW_HASH))


class UpdateTests(unittest.TestCase):
    def test_changes_only_version_and_checksum(self):
        expected = CASK.replace(CURRENT, NEXT).replace(OLD_HASH, NEW_HASH)
        self.assertEqual(updater.update_text(CASK, NEXT, NEW_HASH), expected)

    def test_idempotent(self):
        self.assertEqual(updater.update_text(CASK, CURRENT, OLD_HASH), CASK)

    def test_reject_replaced_release_and_downgrade(self):
        for version, digest in ((CURRENT, NEW_HASH), ("2026.08.20.0", NEW_HASH)):
            with self.subTest(version=version):
                with self.assertRaises(ValueError):
                    updater.update_text(CASK, version, digest)

    def test_numeric_revision_order(self):
        self.assertIn('version "2026.08.24.10"',
                      updater.update_text(CASK, "2026.08.24.10", NEW_HASH))

    def test_reject_ambiguous_cask(self):
        for text in (CASK + f'  version "{CURRENT}"\n', CASK.replace('  sha256', '  # sha256')):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    updater.update_text(text, NEXT, NEW_HASH)

    def test_reject_invalid_direct_inputs(self):
        for version, digest in ((NEXT + "\n", NEW_HASH), (NEXT, NEW_HASH + "\n"),
                                ("2026.09.13.00", NEW_HASH)):
            with self.subTest(version=version, digest=digest):
                with self.assertRaises(ValueError):
                    updater.update_text(CASK, version, digest)


class CommandTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "Casks").mkdir()
        (self.root / "scripts").mkdir()
        self.cask = self.root / "Casks/komai.rb"
        self.cask.write_text(CASK)
        self.script = self.root / "scripts/update_cask.py"
        shutil.copyfile(ROOT / "scripts/update_cask.py", self.script)
        self.metadata = self.root / "release.json"
        self.output = self.root / "outputs.txt"

    def run_update(self, data):
        self.metadata.write_text(json.dumps(data))
        return subprocess.run(
            [sys.executable, str(self.script), "--release-json", str(self.metadata)],
            env={**os.environ, "GITHUB_OUTPUT": str(self.output)},
            capture_output=True,
            text=True,
            check=False,
        )

    def test_update_then_noop_publishes_correct_job_outputs(self):
        result = self.run_update(release())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.cask.read_text(), CASK.replace(CURRENT, NEXT).replace(OLD_HASH, NEW_HASH))
        self.assertEqual(self.output.read_text(),
                         f"changed=true\nversion={NEXT}\nsha256={NEW_HASH}\n")
        self.output.unlink()
        result = self.run_update(release())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.output.read_text().startswith("changed=false\n"))

    def test_invalid_release_does_not_change_cask_or_emit_outputs(self):
        data = release()
        data["assets"][0]["digest"] = "sha256:invalid"
        result = self.run_update(data)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.cask.read_text(), CASK)
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
