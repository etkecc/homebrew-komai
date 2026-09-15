cask "komai" do
  version "2026.09.15.0"
  sha256 "4f3a0c8fa5cf9f71c9d449aa762a4b86cca86b140097bc5d8bd84239bd123b46"

  url "https://github.com/etkecc/komai/releases/download/v#{version}/komai-#{version}-macos-arm64.dmg"
  name "Komai"
  desc "Matrix chat client"
  homepage "https://github.com/etkecc/komai"

  livecheck do
    url "https://github.com/etkecc/komai/releases/latest"
    strategy :github_latest
  end

  # Komai only ships an Apple Silicon DMG, and it targets macOS 13.3+.
  depends_on arch: :arm64
  depends_on macos: :ventura

  app "komai.app"
end
