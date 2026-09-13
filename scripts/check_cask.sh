#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
set -euo pipefail

if [[ "$(uname -s)" != Darwin || "$(uname -m)" != arm64 ]]; then
    echo "Cask installation validation requires an Apple Silicon Mac."
    exit 1
fi

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cask_name=etkecc/komai/komai

# Use a clean runner: never uninstall an operator's existing Komai installation.
if [[ -e /Applications/komai.app ]] || brew list --cask komai >/dev/null 2>&1; then
    echo "Komai is already installed; use a clean Mac or runner for this check."
    exit 1
fi

# Register the actual checkout so audits and installation use the candidate, including uncommitted changes, rather than fetching main from GitHub.
tap_dir="$(brew --repository)/Library/Taps/etkecc/homebrew-komai"
if [[ -e "$tap_dir" || -L "$tap_dir" ]]; then
    if [[ "$(cd "$tap_dir" && pwd -P)" != "$(cd "$repo_dir" && pwd -P)" ]]; then
        echo "A different etkecc/komai checkout is already tapped."
        exit 1
    fi
else
    mkdir -p "$(dirname "$tap_dir")"
    ln -s "$repo_dir" "$tap_dir"
fi
brew trust --cask "$cask_name"

brew style "$repo_dir/Casks/komai.rb"
# --new and --signing impose central Homebrew Cask acceptance requirements.
# Ordinary external-tap auditing keeps the app's normal Gatekeeper behavior.
brew audit --cask --online "$cask_name"

cleanup() {
    brew uninstall --cask "$cask_name" >/dev/null 2>&1 || true
}
trap cleanup EXIT
brew install --cask --appdir=/Applications "$cask_name"
test -d /Applications/komai.app
test "$(lipo -archs /Applications/komai.app/Contents/MacOS/komai)" = arm64
codesign --verify --deep --strict /Applications/komai.app
xattr -p com.apple.quarantine /Applications/komai.app
brew uninstall --cask "$cask_name"
test ! -e /Applications/komai.app
trap - EXIT
