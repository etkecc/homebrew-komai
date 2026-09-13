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
First launch and real upgrade behavior need a separate Mac check.

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

## Initial rollout

The source history was imported from Boris Stäheli's [original tap](https://github.com/bstaeheli/homebrew-komai) through commit `ca14ac513713a8e32384c035ba5ae12e4050d1f1`, preserving all 13 commits.
Repository Actions were disabled before importing its scheduled updater.

1. Obtain maintainer approval for the acknowledgement, documentation, and implementation before committing the adoption changes.
2. Commit and push the reviewed changes while Actions remains disabled.
3. Enable Actions, leaving `KOMAI_AUTO_UPDATE` unset.
   Keep the default workflow token permission at read-only; the updater grants write only to publishing.
4. Manually run **Update Komai Cask** on `main` and inspect its validation run.
   Resolve any macOS or Homebrew failures before enabling publishing.
5. Set `KOMAI_AUTO_UPDATE=true` after those checks pass.
6. Verify a fresh install and first launch, an upgrade from an older release, and migration from Boris's tap on Apple Silicon.
   Confirm settings and account data survive.
   Homebrew automation does not verify these GUI flows.
7. Advertise the tap and close [Komai issue #282](https://github.com/etkecc/komai/issues/282) after the installation and upgrade checks pass.

Keep force pushes and deletion disabled for `main`.
The updater publishes validated bumps directly, so requiring PR-only changes or additional push checks would need a corresponding redesign of the publishing job.
