# TLOU2 Discord Rich Presence

Source for the **The Last of Us Part II Remastered – Discord Rich Presence** mod
published on Nexus Mods.

It shows your chapter, the character you are playing, difficulty and run
modifiers, collectible count and playtime as a Discord status while you play.

```
The Last of Us Part II
  Seattle Day 2 · Hillcrest
  Playing as Ellie · Moderate · 23 collectibles
  02:14:07
  [ game art ]                    [ Ellie ]
```

The mod is published as a small ASI plugin. This repository contains everything
needed to rebuild the published archive byte for byte, and the notes on what
each file does.

## What the mod does, and does not do

- Reads the game's own save metadata: `params.json` (the save's title block) and
  the NTFS last-access time of each save slot, used to notice when you load a
  save from the load menu.
- Writes a Discord Rich Presence over Discord's local IPC named pipe
  (`\\.\pipe\discord-ipc-0`). Nothing leaves the machine.
- **Does not** inject into, hook, patch or modify the game or its files. **Does
  not** read process memory. **Does not** write to or alter saves. There is no
  network traffic other than the local Discord pipe.

  This describes the shipped v1.2.0: story mode is unchanged, and No Return is
  detected from save metadata for a placeholder status (one large image and
  `Playing NO RETURN`). Full No Return support will use guarded live memory
  reads and will update this section in that release. See `README.md`.

`avrt.dll` only forwards Windows AVRT calls and loads the `.asi`; the `.asi`
only starts a Python process and then exits its own thread. Neither hooks the
game.

### Mission artwork

The large image follows the mission in the save: `MISSION_ASSETS` in
`tlou2_rpc.py` maps all 46 story missions to Discord asset keys (for example
`Seattle Day 2 - Hillcrest` -> `hillcrest`, `Santa Barbara - The Resort` ->
`the_resort`). `DISCORD-ASSETS.txt` is the upload checklist. "The Farm" uses a
single shared key, `the_farm`, in both campaigns. The hover text is
the mission name by default (`large_text_template = "{subchapter}"`). An
unknown or not-yet-uploaded key falls back to `tlou2`; the presence never
loses its text because of missing art.

### No Return placeholder (v1.2.0)

The trailing 12-byte struct in a save's `params.json` carries the mode flag at
bytes 4-5: `00 80` means No Return, `00 00` means Story. v1.2.0 uses that flag
alone - no memory reads, no save edits and no mode picker. A No Return save
publishes exactly two things: `Playing NO RETURN` and the `no_return` large
image (hover `No Return`). There is no second text line, small image or timer.

`assets\no_return.png` is a real 512×512 PNG converted from the original
400×400 WebP (`assets\raw\no_return.webp`) and is ready to upload to the Discord
app under the exact key `no_return`. If that key is missing, the helper drops
images for the No Return status rather than falling back to Story art; the text
line still works.

## What is in the release archive

```
avrt.dll                   44,858 bytes   built from dll/avrt_proxy.c + avrt_stubs.S
TLOU2DiscordRPC.asi        81,689 bytes   built from dll/launcher.c
TLOU2DiscordRPC/tlou2_rpc.py  generated  tlou2_rpc.py with settings embedded
README.txt                                mod/README.txt
```

Four files. No third-party binaries ship in the archive: no bundled Python
runtime, no third-party DLLs, no nested archives. `avrt.dll` is our own tiny
proxy, needed because this game has no ASI loader. The mod requires Python 3 to be installed
by the user (`python.org`, standard library only), and the launcher finds it via
`pythonw.exe` beside the script, `pythonw.exe` on `PATH`, or the `pyw.exe`
launcher.

## Building

Requirements:

- Windows 10/11, x64.
- mingw-w64 gcc (tested with w64devkit's `x86_64-w64-mingw32-gcc`, GCC 16.2.0),
  or any gcc that targets x86_64-w64-mingw32.
- PowerShell 5.1 (built into Windows).
- Any Python 3 on `PATH` (used only for the build's smoke test; it is not
  packaged).

```powershell
git clone <this repository>
cd <repository>
copy config.json.example config.json     # then set client_id
powershell -NoProfile -ExecutionPolicy Bypass -File .\pack.ps1 `
  -Gcc "C:\path\to\x86_64-w64-mingw32-gcc.exe"
```

Output: `dist\TLOU2-Discord-Rich-Presence-1.2.0.zip`.

`client_id` is the Discord application ID that owns the presence name and art
assets. The published build points at the author's application; the repository
ships only a placeholder so the published application ID is not republished
here. Any Discord application ID works for testing (the images are not required
— the helper falls back to text-only when the assets are missing).

### What the build does

1. Compiles `dll/launcher.c` to `TLOU2DiscordRPC.asi` and the proxy sources to
   `avrt.dll`:

   ```
   x86_64-w64-mingw32-gcc -O2 -shared -static-libgcc -Wl,--image-base=0x140000000 -o TLOU2DiscordRPC.asi dll/launcher.c
   x86_64-w64-mingw32-gcc -O2 -shared -static-libgcc -Wl,--image-base=0x140000000 -o avrt.dll dll/avrt_proxy.c dll/avrt_stubs.S dll/avrt_proxy.def
   ```

2. Reads `config.json`, XORs the bytes with `0x5A`, base64-encodes the result,
   and substitutes it for the `EMBEDDED_CONFIG = ""` placeholder in
   `tlou2_rpc.py`. The result is the shipped `tlou2_rpc.py`. The packaged mod
   therefore carries no `config.json`, and a `config.json` dropped next to it is
   ignored.
3. Runs the shipped script once (`--once`) as a smoke test and fails the build
   if it cannot build a presence. On a machine with no TLOU2 saves the script
   exits 1 with `no usable save found`; the build accepts that, because it means
   the script and its embedded settings loaded fine and there is just nothing to
   read - the normal state of a reviewer's PC.
4. Refuses to package if a `config.json`, a `runtime\` folder or a nested archive
   is present.
4. Zips the staging folder with pinned file timestamps, so the same sources
   produce the same archive.

The shipped `.py` is the script itself rather than a `.pyc`, because bytecode is
tied to the Python version that compiled it and users install their own Python.

### Reproducible builds

The compiled plugin is byte-for-byte reproducible. Two things had to be pinned:

- **Paths.** gcc records the path passed on the command line in the output, so
  `pack.ps1` compiles from the project root with relative paths.
- **Image base.** w64devkit's linker randomises the PE `ImageBase` on every run,
  which changes the header checksum and every absolute pointer in `.data`.
  `-Wl,--image-base=0x140000000` fixes it. The DLL is still relocatable and
  still gets `DYNAMIC_BASE`, so ASLR at load time is unaffected.

The archive is then zipped with pinned file timestamps. A build of this
repository at the published revision produces:

```
TLOU2DiscordRPC.asi   SHA-256 CD8685FE54DDFF3824DFC92CB75E42CE81C0608B9ECEC75AE54FC6EDEC84F27E
avrt.dll              SHA-256 5486A747329FC3DA69726CDCDFFA57ACCD946A290E97B719B5B72286F9DA2F5E
```

Neither binary depends on `config.json`, so those hashes match the files in the
published download. The zip hash will not match unless the published Discord
application ID is restored in `config.json`, because that ID is a string inside
the embedded settings blob.

## Verifying a build

- Smoke test without Discord: `py -3 TLOU2DiscordRPC\tlou2_rpc.py --once` prints
  the payload it would publish.
- Both binaries link against `kernel32`, `user32` and `msvcrt` only (no network,
  no Python import): `dumpbin /imports TLOU2DiscordRPC.asi` or
  `objdump -p TLOU2DiscordRPC.asi` (and the same for `avrt.dll`).

## Layout

| Path | What it is |
| --- | --- |
| `tlou2_rpc.py` | The helper: save discovery/parsing, character and chapter detection, Discord IPC, CLI. |
| `dll/launcher.c` | The ASI plugin: a thread that waits, locates the script, and spawns the interpreter with `CREATE_NO_WINDOW`. |
| `dll/avrt_proxy.c`, `dll/avrt_stubs.S`, `dll/avrt_proxy.def` | The `avrt.dll` proxy: forwards 20 Windows AVRT exports and loads the plugin. |
| `pack.ps1` | Build script described above. |
| `config.json.example` | Settings template. Copy to `config.json`. |
| `DISCORD-ASSETS.txt` | Checklist of every Discord art asset key: base, characters and 46 missions. |
| `mod/README.txt` | README shipped inside the archive. |

## Notes

- Obfuscating the settings (XOR + base64) is not encryption. The Discord
  application ID is readable by anyone who decodes the blob or watches the
  process; it is embedded so that users cannot accidentally change or break the
  display, not to keep a secret.
- Discord Rich Presence requires the desktop Discord client; the browser client
  has no Rich Presence support.
- Unofficial fan tool. The Last of Us is a trademark of Sony Interactive
  Entertainment. No game files are included.
