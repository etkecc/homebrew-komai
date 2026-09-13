#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Prepare a version/checksum-only cask update; never commit or push it."""

import argparse
import datetime
import json
import os
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
CASK = ROOT / "Casks/komai.rb"
VERSION_LINE = re.compile(r'^  version "([^"\n]+)"$', re.MULTILINE)
SHA_LINE = re.compile(r'^  sha256 "([a-f0-9]{64})"$', re.MULTILINE)


def version_parts(version):
    if not isinstance(version, str) or not re.fullmatch(
        r"[0-9]{4}\.[0-9]{2}\.[0-9]{2}\.(?:0|[1-9][0-9]*)", version
    ):
        raise ValueError("Expected a Komai version in YYYY.MM.DD.N format")
    parts = tuple(map(int, version.split(".")))
    datetime.date(*parts[:3])
    return parts


def release_candidate(release):
    if not isinstance(release, dict):
        raise ValueError("Release metadata must be an object")
    if release.get("draft") is not False or release.get("prerelease") is not False:
        raise ValueError("Only published stable releases are accepted")
    tag = release.get("tag_name", "")
    if not isinstance(tag, str) or not tag.startswith("v"):
        raise ValueError("Expected a version tag starting with v")
    version = tag[1:]
    version_parts(version)
    name = f"komai-{version}-macos-arm64.dmg"
    assets = release.get("assets")
    if not isinstance(assets, list):
        raise ValueError("Release assets must be a list")
    matches = [a for a in assets if isinstance(a, dict) and a.get("name") == name]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one release asset named {name}")
    asset = matches[0]
    expected_url = f"https://github.com/etkecc/komai/releases/download/{tag}/{name}"
    if asset.get("browser_download_url") != expected_url:
        raise ValueError("Asset URL does not match the cask's official download URL")
    if asset.get("state") != "uploaded" or type(asset.get("size")) is not int or asset["size"] <= 0:
        raise ValueError("Release asset is incomplete or empty")
    digest = asset.get("digest")
    if not isinstance(digest, str) or not re.fullmatch(r"sha256:[a-f0-9]{64}", digest):
        raise ValueError("Release asset must have a GitHub SHA-256 digest")
    return version, digest.removeprefix("sha256:")


def update_text(text, version, sha256):
    candidate = version_parts(version)
    if not isinstance(sha256, str) or not re.fullmatch(r"[a-f0-9]{64}", sha256):
        raise ValueError("Expected a SHA-256 checksum")
    versions, checksums = VERSION_LINE.findall(text), SHA_LINE.findall(text)
    if len(versions) != 1 or len(checksums) != 1:
        raise ValueError("Expected one version and one SHA-256 stanza")
    current = version_parts(versions[0])
    if candidate < current:
        raise ValueError("Refusing to downgrade the cask")
    if candidate == current:
        if sha256 != checksums[0]:
            raise ValueError("The existing release checksum changed; maintainer review is required")
        return text
    text = VERSION_LINE.sub(lambda _: f'  version "{version}"', text)
    return SHA_LINE.sub(lambda _: f'  sha256 "{sha256}"', text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--release-json", type=Path)
    source.add_argument("--version")
    parser.add_argument("--sha256")
    args = parser.parse_args()
    if (args.version is not None) != (args.sha256 is not None):
        parser.error("--version and --sha256 must be provided together")
    try:
        if args.release_json:
            version, sha256 = release_candidate(json.loads(args.release_json.read_text()))
        else:
            version, sha256 = args.version, args.sha256
        original = CASK.read_text()
        updated = update_text(original, version, sha256)
        changed = original != updated
        if changed:
            CASK.write_text(updated)
        if output := os.environ.get("GITHUB_OUTPUT"):
            with open(output, "a", encoding="utf-8") as stream:
                stream.write(f"changed={str(changed).lower()}\nversion={version}\nsha256={sha256}\n")
        print(f"Komai {version}: {'cask updated' if changed else 'already up to date'}")
    except (ValueError, OSError) as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
