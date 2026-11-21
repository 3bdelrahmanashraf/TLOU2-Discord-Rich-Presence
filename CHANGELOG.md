# Changelog

All notable changes to The Last of Us Part II Discord Rich Presence are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-11-21

### Added
- Mission-specific game art for the large image: all 46 story missions map to
  their own Discord asset key (`waking_up`, `the_overlook`, `the_birthday_gift`,
  `the_confrontation`, `the_beach`, ...).
- `DISCORD-ASSETS.txt`: upload checklist of all 50 Discord art keys (1 base,
  3 characters, 46 missions), grouped into the 11 chapters.
- Large-image hover text now shows the current mission name by default via
  `presence.large_text_template = "{subchapter}"`.
- Graceful fallback: an unknown or not-yet-uploaded mission key falls back to
  the base `tlou2` image, then to text-only if the base asset is unavailable.
  Presence text never breaks because of missing art.

### Changed
- Added `prologue` as its own mission key; removed `the_park`, which is a
  chapter name rather than a mission. "Tracking Lesson" is its own key.
- "The Farm" uses one shared key in both campaigns; the extra `the_farm_abby`
  key was removed.
- Updated the repository README, source README, shipped README and Nexus page
  to describe mission art and the new upload checklist.

### Fixed
- A fresh save whose playtime reads "less than 1 sec" no longer appends that
  phrase to the difficulty (e.g. "Moderate less than"). It is now read as zero
  playtime with no modifier and no meaningless elapsed timer.

### Notes
- This release still requires the artwork to be uploaded to the Discord
  application (`1402372564365475861`) before mission art appears. The helper
  works with the text and four original assets in the meantime.

## [1.0.0] - 2026-11-19

### Added
- First release: chapter, character, difficulty and run modifiers, collectible
  count and playtime as a Discord Rich Presence status.
- Immediate update when a save is loaded from the load menu.
- Starts with the game via a tiny `avrt.dll` proxy; no ASI loader and no bundled
  Python runtime needed.
