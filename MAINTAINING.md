# Maintaining the Komai tap

The tap packages the published Apple Silicon DMG from `etkecc/komai`.
It does not build Komai or host another copy of the app.

## Checks

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

The **Validate Komai Cask** workflow runs the installation checks on an ARM64 `macos-26` runner for pushes, pull requests, and manual runs.
