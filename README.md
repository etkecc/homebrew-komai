# Komai Homebrew Tap

The official [etke.cc](https://etke.cc/) Homebrew tap for [Komai](https://komai.chat/), a Matrix chat client for the desktop.

## Requirements

- Apple Silicon Mac (ARM64)
- macOS 13.3 (Ventura) or newer
- [Homebrew](https://brew.sh/)

Komai does not currently provide an Intel Mac build.

## Install

```sh
brew install --cask etkecc/komai/komai
```

Homebrew adds the tap automatically.
On Homebrew 6 and newer, this command trusts only the Komai cask; trusting the whole tap is unnecessary.

### First launch

Komai is not signed with an Apple Developer ID or notarized, so macOS blocks the first launch:

- **macOS 13/14:** right-click `komai.app` in `/Applications` and choose **Open**.
- **macOS 15+:** try opening the app once, then go to **System Settings → Privacy & Security → Open Anyway**.

See [Apple's explanation of opening apps from unidentified developers](https://support.apple.com/en-us/102445).

## Upgrade

Quit Komai before upgrading, then run:

```sh
brew update
brew upgrade --cask etkecc/komai/komai
```

The tap checks for new [Komai releases](https://github.com/etkecc/komai/releases) daily.
The updater refreshes the cask version and computes the DMG checksum when a new release appears.

## Uninstall

```sh
brew uninstall --cask etkecc/komai/komai
brew untap etkecc/komai
```

Uninstalling removes the app and keeps your Komai settings and account data.

## Acknowledgements

The initial Komai cask and automated updater were created by [Boris Stäheli](https://github.com/bstaeheli) in [bstaeheli/homebrew-komai](https://github.com/bstaeheli/homebrew-komai).
Boris [proposed an official tap](https://github.com/etkecc/komai/issues/282) and made his work available for adoption by etke.cc.

This repository preserves the original Git history and attribution.
The official tap is maintained by etke.cc.

## License

This tap is licensed under the **GNU General Public License, version 3 or later**; see [COPYING](COPYING).
Boris confirmed this license for the original tap in [the handoff discussion](https://github.com/etkecc/komai/issues/282#issuecomment-5582476747).

[Komai](https://github.com/etkecc/komai) is also licensed under GPL-3.0-or-later.

## Support

Report packaging problems in [this repository's issues](https://github.com/etkecc/homebrew-komai/issues).
