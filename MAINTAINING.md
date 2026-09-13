# Maintaining the Komai tap

The tap packages the published Apple Silicon DMG from `etkecc/komai`.
It does not build Komai or host another copy of the app.

## Checks

Run the release parser and update tests on Linux or macOS:

```sh
python3 -m unittest discover -s tests -v
```

On a clean Apple Silicon Mac with current Homebrew:

```sh
bash scripts/check_cask.sh
```

The script registers this checkout as `etkecc/komai`, trusts only its Komai cask, runs `brew style` and `brew audit --cask --online`, then installs and uninstalls the app.
It verifies the ARM64 executable, bundle signature integrity, and quarantine attribute.
It refuses to run over an existing Komai installation or a different checkout of the tap.
It leaves the checkout tapped for subsequent checks.

These checks preserve quarantine and do not launch the app.
Komai is ad-hoc signed, without Developer ID signing or notarization.
Do not add `--no-quarantine`, remove quarantine attributes, or require `brew audit --new` or `--signing`: those signing checks target admission to Homebrew's central cask repository.
Interactive first launch, upgrades, and migration from another tap are outside this CI check.
Additional manual checks are optional and do not block publication of the tap.

The **Validate Komai Cask** workflow runs the tests and installation checks on an ARM64 `macos-26` runner for pushes, pull requests, and manual runs.
The updater also calls it for each candidate release before publishing.

## Automated updates

**Update Komai Cask** checks GitHub's latest stable release daily at 06:23 UTC and can also be run manually.
GitHub may delay scheduled runs.

The release parser requires a valid Komai date/version tag and exactly one fully uploaded DMG with the expected filename, official URL, and GitHub SHA-256 digest.
It refuses downgrades and checksum changes to an existing version.
A new version changes only the cask's version and checksum.
Homebrew downloads the DMG and verifies that checksum during validation.

Only the final publishing job has `contents: write`.
Release discovery and macOS validation have read access and do not persist checkout credentials.
All jobs use the same Git revision and candidate values.
Publishing aborts if `main` moved during testing; the final push is a normal fast-forward push.
Rerun the updater after such a conflict.
No personal token, GitHub App, or cross-repository write credential is required.

Publishing also requires the repository Actions variable `KOMAI_AUTO_UPDATE` to be exactly `true`.
When it is absent or `false`, the workflow can discover and test updates but cannot commit them.
A manual run validates even when the cask is already current.

GitHub does not start another push workflow for commits made with `GITHUB_TOKEN`; this is why the updater completes validation before committing.

To inspect an update locally:

```sh
gh api repos/etkecc/komai/releases/latest > /tmp/komai-release.json
python3 scripts/update_cask.py --release-json /tmp/komai-release.json
git diff -- Casks/komai.rb
```

The script never commits or pushes.
If GitHub has no asset digest, or the published file changes without a version bump, investigate the release instead of automatically replacing the checksum.

## Adoption and validation

The source history was imported from Boris Stäheli's [original tap](https://github.com/bstaeheli/homebrew-komai) through commit `ca14ac513713a8e32384c035ba5ae12e4050d1f1`, preserving all 13 commits.
Repository Actions were disabled before importing its scheduled updater.

The adopted tap passed [Apple Silicon CI on 2026-09-13](https://github.com/etkecc/homebrew-komai/actions/runs/34743589160), including all 13 updater tests, Homebrew style and online audit, installation, bundle signature verification, quarantine preservation, and uninstallation.
Daily publishing was enabled after that run passed.

The maintainer accepted the original author's experience and this independent CI validation as sufficient to publish the official tap.
The cask retains the original DMG and standard `app "komai.app"` installation, with no custom upgrade or user-data deletion hooks.
Interactive use, upgrades, and migration were not independently tested during adoption; do not describe them as verified.
Reconsider additional testing if the app installation path changes or custom install, upgrade, or uninstall logic is introduced.

Keep the default workflow token permission at read-only; only the publishing job needs write access.
The repository action policy requires full-length commit SHAs and allows only the checkout action revision used by the workflows.
When updating that action, allow the new revision in the repository's Actions settings before running validation, and remove the old allowance after the update passes.

Keep force pushes and deletion disabled for `main`.
The updater publishes validated bumps directly, so requiring PR-only changes or additional push checks would need a corresponding redesign of the publishing job.
