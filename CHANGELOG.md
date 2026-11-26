# Changelog

All notable changes to The Last of Us Part II Discord Rich Presence are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-11-26

### Added
- Automatic No Return detection from the save's own metadata: the trailing
  12-byte struct in `params.json` has a mode flag at bytes 4-5 (`00 80` for
  No Return, `00 00` for Story). No picker, config change or save edit.
- A deliberately small No Return status: `Playing NO RETURN` on the only text
  line, with the `no_return` large image (hover: `No Return`) and no state line,
  no timestamps and no small image yet.
- `assets\no_return.png`: the placeholder art, kept as a real 512×512 RGB PNG
  that Discord accepts. The original 400×400 WebP is no longer bundled.
- `no_return` added to `DISCORD-ASSETS.txt`; the upload checklist is now 51 keys.

### Changed
- A missing `no_return` asset drops images entirely for that status instead of
  falling back to the Story `tlou2` art. The text line still works.
- The mode flag is part of the state key, so switching between a Story save and
  a No Return save updates the presence immediately.
- README, source README, Nexus page text, progress chart, security policy,
  contributing guide and issue templates updated for v1.2.0.

### Notes
- The `no_return` image must be uploaded manually to the Discord application
  (`1402372564365475861`) under Rich Presence → Art Assets. Until then, No
  Return shows text only; Story art and status are unchanged.
- This is a placeholder step, not full No Return support. Operator, location,
  mode, kills and score are still in development and are not guessed.

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
