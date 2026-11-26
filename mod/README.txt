The Last of Us Part II - Discord Rich Presence
==============================================

Shows what you are playing in The Last of Us Part II Remastered as a Discord
status, updating as you play:

    The Last of Us Part II                     <- app name
      Seattle Day 2 - Hillcrest                <- chapter / subchapter
      Playing as Ellie - Moderate - 23 collectibles
      2:14:07                                  <- playtime
      [ game art ]                    [ Ellie ]

It reads the game's own save metadata. Nothing is written to your saves, no
memory is touched, and it works in single player only (it is a status, not a
gameplay mod).

IMAGES
------
The large image follows the mission you are playing (Hillcrest, The Stadium,
The Resort, ...), and the small image follows the character (Ellie, Abby,
Joel). Artwork lives on the Discord application, not in this download, so the
mission art shows only once those art assets have been uploaded there. Until
then the box art is used; the status text works either way.

In No Return, v1.2.0 shows a smaller status: "Playing NO RETURN" with one large
image and no small image. It uses the separate Discord key "no_return". If that
key is not uploaded, the status is text-only - it never uses the Story box art.
The full No Return status (operator, location, mode, kills and score) is still
planned and is not in this version.


REQUIREMENTS
------------
- Discord desktop app running (the browser version has no Rich Presence).
- Windows 10 or 11, 64-bit.
- Python 3 for Windows. Get it from python.org/downloads and leave "Add
  python.exe to PATH" on the first screen as it is - either way works, because
  the plugin also uses the "py" launcher that Python installs. One time, about
  30 MB, no packages or pip commands.


INSTALL
-------
1. If you do not have Python yet, install it from python.org/downloads and let
   the installer finish. You do not need pip or any extra package.
2. Open your game folder, the one containing tlou-ii.exe
   (Steam: right-click the game > Manage > Browse local files).
3. Copy these three items into that folder:

       avrt.dll
       TLOU2DiscordRPC.asi
       TLOU2DiscordRPC\          (the whole folder)

   The result looks like:

       ...\The Last of Us Part II Remastered\tlou-ii.exe
       ...\The Last of Us Part II Remastered\avrt.dll
       ...\The Last of Us Part II Remastered\TLOU2DiscordRPC.asi
       ...\The Last of Us Part II Remastered\TLOU2DiscordRPC\tlou2_rpc.py

   avrt.dll is a 44 KB proxy. Windows loads it because the game asks for AVRT;
   it passes every AVRT call straight to the real Windows DLL and then loads
   TLOU2DiscordRPC.asi. No ASI loader is needed. If another mod already has an
   avrt.dll in the game folder, do not overwrite it - ask me for a version with
   a different proxy name instead.

4. Start Discord, then start the game. The status appears within a few seconds.

At launch the proxy loads the .asi, which starts the helper silently. Nothing
runs while the game is closed (it clears the status and exits ~3 minutes after
you quit).


VERIFY IT STARTED
-----------------
Open TLOU2DiscordRPC\launcher.log. A line like

    2026-11-19 02:16:10 [pid 24624]  started: "C:\...\pyw.exe" -3 "...\TLOU2DiscordRPC\tlou2_rpc.py"

means the plugin fired. TLOU2DiscordRPC\rpc.log shows what it published and
which save slot it used.

If the game folder is read-only (Program Files), both logs are written to
%LOCALAPPDATA%\TLOU2DiscordRPC\ instead.

If launcher.log says "no Python found", install Python 3 and start the game
again; nothing else is needed.


SETTINGS
--------
There is no settings file. Everything the helper shows is built into it, so
nothing has to be configured and nothing can be changed by accident. If a
default ever changes, it ships as a new version.


HOW THE SAVE IS PICKED
----------------------
- While you play, the current autosave is used; it is rewritten at checkpoints
  and chapter starts, so the status follows your progress.
- When you load a save from the load menu, the game does not rewrite the
  autosave immediately. The plugin also checks the last-access time of each
  save slot (Windows tracks it when the game reads the slot to load it) and
  switches to that slot within one poll. The next autosave takes over again.
- Save files that are mid-write (titles like "NEW MANUAL SAVE") are ignored so
  the status never flickers to a blank chapter.


UNINSTALL
---------
Delete avrt.dll, TLOU2DiscordRPC.asi and the TLOU2DiscordRPC folder from the
game folder. Nothing else is changed anywhere on your system. If a status is
still visible, quit and restart Discord.


TROUBLESHOOTING
---------------
- No status at all: is Discord running? Check launcher.log and rpc.log. If
  launcher.log is missing, make sure avrt.dll and the .asi are both in the game
  folder next to tlou-ii.exe.
- Text but no images: the Discord application's art assets are missing; the
  helper intentionally falls back to text-only instead of failing. For No
  Return, upload the 512x512 no_return.png asset under the key "no_return".
- Status shows the wrong save: send me rpc.log with the chapter names you saw.
- Game won't start: remove avrt.dll and TLOU2DiscordRPC.asi to confirm the mod
  is the cause, then report it. Neither file hooks or patches the game: the
  proxy forwards calls to Windows and the plugin only spawns a process.


CREDITS
-------
Data source: the game's own save metadata. No game files are included or
modified. The Last of Us is a trademark of Sony Interactive Entertainment;
this is an unofficial fan tool.
