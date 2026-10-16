cask "komai" do
  version "2026.10.16.0"
  sha256 "cf3ba6b8efd203c1c35e8366868ea827b243818d64112225f7d88f84ed893847"

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
