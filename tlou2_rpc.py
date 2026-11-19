#!/usr/bin/env python3
"""
Discord Rich Presence for The Last of Us Part II Remastered.

Reads the newest live autosave's params.json (chapter, playtime, difficulty,
collectibles) and publishes it to Discord as a Rich Presence. No memory
reading, no game file edits, no third-party packages.

Run silently with start_tlou2_rpc.vbs, or debug with:
    py -3 tlou2_rpc.py --console
    py -3 tlou2_rpc.py --once
"""

import argparse
import base64
import ctypes
import ctypes.wintypes
import json
import msvcrt
import os
import re
import struct
import sys
import time
import uuid

APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(APP_DIR, "config.json")
MUTEX_NAME = "Local\\TLOU2DiscordRichPresence"

# pack.ps1 replaces the empty string below with the real settings, encoded, when
# it builds the release. A release therefore carries no config.json at all, and
# any config.json a user drops next to it is ignored, so the presence cannot be
# re-pointed at another Discord application or reconfigured.
EMBEDDED_CONFIG = ""
_XOR_KEY = 0x5A


def _pick_log_path():
    """Log beside the app; fall back to LOCALAPPDATA on read-only installs."""
    local = os.path.join(APP_DIR, "rpc.log")
    try:
        with open(local, "a", encoding="utf-8"):
            pass
        return local
    except OSError:
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        folder = os.path.join(base, "TLOU2DiscordRPC")
        try:
            os.makedirs(folder, exist_ok=True)
            return os.path.join(folder, "rpc.log")
        except OSError:
            return local


LOG_PATH = _pick_log_path()

DEFAULTS = {
    "client_id": "",
    "game_process": "tlou-ii.exe",
    "save_dir": "",
    "poll_seconds": 5,
    "idle_exit_seconds": 900,
    "exit_when_game_closes": True,
    "relaunch_grace_seconds": 180,
    "detect_loaded_save": True,
    "presence": {
        "show_chapter": True,
        "show_character": True,
        "show_difficulty": True,
        "show_modifier": True,
        "show_collectibles": True,
        "show_playtime": True,
        "details_template": "{chapter}",
        "state_template": "{character} \u00b7 {difficulty} \u00b7 {collectibles}",
        "character_prefix": "Playing as ",
        "large_image": "tlou2",
        "large_text": "The Last of Us Part II",
        "small_image_from_character": True,
        "character_assets": {
            "Ellie": "ellie",
            "Abby": "abby",
            "Joel": "joel",
            "Ellie & Abby": "ellie",
        },
    },
    "character": "auto",
    "character_overrides": {},
}

# Subchapters that only exist in Abby's campaign.
ABBY_SUBCHAPTERS = {
    "the stadium", "on foot", "the forward base", "the aquarium",
    "hostile territory", "winter visit", "the forest", "the coast",
    "return to the coast", "the shortcut", "the descent", "ground zero",
    "return to the aquarium", "the marina", "the island", "the escape",
    "the confrontation", "the flooded city",
}
JOEL_SUBCHAPTERS = {"prologue"}

PLAYTIME_RE = re.compile(
    r"(?:(\d+)\s*hr\s*)?(?:(\d+)\s*min\s*)?(\d+)\s*sec", re.IGNORECASE
)

# Slot titles the game writes while a save is being created/rotated. They carry
# no chapter, so showing them for a second looks like a glitch.
PLACEHOLDER_CHAPTERS = {
    "new manual save", "new autosave", "new save", "empty", "no data", "---",
}


def usable_detail(detail):
    first = (detail or "").strip().split("\n", 1)[0].strip().lower()
    return bool(first) and first not in PLACEHOLDER_CHAPTERS

DEBUG = False


# --------------------------------------------------------------------------- #
# logging
# --------------------------------------------------------------------------- #
def log(msg):
    line = time.strftime("%Y-%m-%d %H:%M:%S") + "  " + msg
    try:
        if os.path.exists(LOG_PATH) and os.path.getsize(LOG_PATH) > 512 * 1024:
            os.replace(LOG_PATH, LOG_PATH + ".1")
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except OSError:
        pass
    if DEBUG and sys.stdout:
        try:
            print(line, flush=True)
        except Exception:
            pass


# --------------------------------------------------------------------------- #
# config
# --------------------------------------------------------------------------- #
def deep_merge(base, extra):
    out = dict(base)
    for key, value in (extra or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def load_config():
    if EMBEDDED_CONFIG:
        # Release build: settings live in the program, config.json is ignored.
        raw = base64.b64decode(EMBEDDED_CONFIG)
        data = json.loads(bytes(b ^ _XOR_KEY for b in raw).decode("utf-8"))
        return deep_merge(DEFAULTS, data)
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8-sig") as fh:
            return deep_merge(DEFAULTS, json.load(fh))
    except FileNotFoundError:
        log("config.json not found, using defaults")
    except (OSError, ValueError) as exc:
        log("config.json unreadable (%s), using defaults" % exc)
    return deep_merge(DEFAULTS, {})


# --------------------------------------------------------------------------- #
# save file discovery + parsing
# --------------------------------------------------------------------------- #
def save_roots(cfg):
    roots = []
    if cfg.get("save_dir"):
        roots.append(os.path.expandvars(os.path.expanduser(cfg["save_dir"])))
    home = os.path.expanduser("~")
    roots += [
        os.path.join(home, "Documents", "The Last of Us Part II"),
        os.path.join(home, "OneDrive", "Documents", "The Last of Us Part II"),
    ]
    seen, out = set(), []
    for root in roots:
        key = os.path.normcase(os.path.abspath(root))
        if key not in seen:
            seen.add(key)
            out.append(root)
    return out


def iter_save_params(root):
    """Yield every params.json that belongs to a save slot."""
    try:
        users = list(os.scandir(root))
    except OSError:
        return
    for user in users:
        savedata = None
        if user.is_dir():
            candidate = os.path.join(user.path, "savedata")
            if os.path.isdir(candidate):
                savedata = candidate
        if savedata is None:
            continue
        try:
            entries = list(os.scandir(savedata))
        except OSError:
            continue
        for entry in entries:
            if not entry.is_dir() or not entry.name.upper().startswith("SAVEFILE"):
                continue
            path = os.path.join(entry.path, "params.json")
            if os.path.isfile(path):
                yield path


def read_params(path):
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError:
        return None
    for encoding in ("utf-8", "cp1252", "latin-1"):
        try:
            return json.loads(raw.decode(encoding))
        except (UnicodeDecodeError, ValueError):
            continue
    return None


def collect_saves(cfg):
    """Every save slot with metadata, including its payload access time.

    USR-DATA is only read by the game when a slot is actually loaded, so its
    last-access time is the signal that a manual save was just loaded.
    """
    found = []
    for root in save_roots(cfg):
        for path in iter_save_params(root):
            data = read_params(path)
            if not isinstance(data, dict):
                continue
            slot_dir = os.path.dirname(path)
            slot = os.path.basename(slot_dir)
            try:
                mtime = os.path.getmtime(path)
            except OSError:
                mtime = 0
            atime = None
            usr_data = os.path.join(slot_dir, "USR-DATA")
            try:
                atime = os.path.getatime(usr_data)
            except OSError:
                atime = None
            found.append({
                "slot": slot,
                "path": path,
                "mtime": mtime,
                "atime": atime,
                "subtitle": str(data.get("subTitle", "") or ""),
                "detail": str(data.get("detail", "") or ""),
            })
    return found


def is_backup(save):
    return "BACKUP" in save["subtitle"].upper()


def is_profile(save):
    return (save["slot"].upper().endswith("0P")
            or save["subtitle"].strip().upper() == "PROFILE")


def parse_playtime(detail):
    match = PLAYTIME_RE.search(detail)
    if not match:
        return None, ""
    hours, minutes, seconds = match.groups()
    total = int(hours or 0) * 3600 + int(minutes or 0) * 60 + int(seconds or 0)
    return total, match


def parse_save(detail, cfg):
    """Turn a save's detail block into display fields."""
    lines = [line.strip() for line in detail.replace("\r\n", "\n").split("\n")]
    chapter_raw = lines[0] if lines and lines[0] else ""
    chapter_raw = re.sub(r"\s*\(CHRONOLOGICAL\)\s*$", "", chapter_raw).strip()

    playtime, pt_match = parse_playtime(detail)

    modifiers = ""
    if pt_match:
        start = detail.rfind("\n", 0, pt_match.start()) + 1
        end = detail.find("\n", pt_match.end())
        if end == -1:
            end = len(detail)
        modifiers = (detail[start:pt_match.start()] + " " + detail[pt_match.end():end])
        modifiers = re.sub(r"\(\s*\)", " ", modifiers)
        modifiers = re.sub(r"\s{2,}", " ", modifiers).strip()
        modifiers = re.sub(r"\(\s*$", "", modifiers).strip()

    diff_match = re.search(r"Challenge\s+([^\n]+)", detail)
    difficulty = ""
    if diff_match:
        difficulty = re.sub(r"\s*\(CHRONOLOGICAL\)\s*$", "", diff_match.group(1)).strip()

    coll_match = re.search(r"Collectibles\s+(\d+)", detail)
    collectibles = int(coll_match.group(1)) if coll_match else None

    if chapter_raw.upper() == "COMPLETE":
        chapter_display = "Story complete"
        character = "Ellie & Abby"
    elif chapter_raw.upper() == "NO CHAPTER NAMES":
        chapter_display = "Story in progress"
        character = guess_character("", cfg)
    else:
        chapter_display = chapter_raw.replace(" - ", " \u00b7 ") if chapter_raw else \
            "The Last of Us Part II"
        character = guess_character(chapter_raw, cfg)

    return {
        "chapter_raw": chapter_raw,
        "chapter": chapter_display,
        "character": character,
        "difficulty": difficulty,
        "modifiers": modifiers,
        "collectibles": collectibles,
        "playtime": playtime,
    }


def guess_character(chapter_raw, cfg):
    locked = str(cfg.get("character", "auto")).strip()
    if locked and locked.lower() != "auto":
        return locked

    raw = chapter_raw.strip()
    sub = raw.split(" - ", 1)[1] if " - " in raw else raw
    sub_key = sub.strip().lower()
    chapter_key = raw.lower()

    overrides = {
        str(k).strip().lower(): str(v).strip()
        for k, v in (cfg.get("character_overrides") or {}).items()
    }
    if chapter_key in overrides:
        return overrides[chapter_key]
    if sub_key in overrides:
        return overrides[sub_key]

    if sub_key in JOEL_SUBCHAPTERS:
        return "Joel"
    if sub_key in ABBY_SUBCHAPTERS:
        return "Abby"
    return "Ellie"


def read_state(cfg):
    """Pick the save the player is actually in.

    Rule: a non-backup slot whose USR-DATA was read more recently than the
    live autosave was written is the save that was just loaded. Otherwise the
    newest 'CURRENT AUTOSAVE' wins (normal play, checkpoints, quit save).
    """
    saves = collect_saves(cfg)

    live = [s for s in saves
            if s["subtitle"].upper().startswith("CURRENT AUTOSAVE")
            and not is_backup(s) and usable_detail(s["detail"])]
    live.sort(key=lambda s: s["mtime"], reverse=True)
    newest = live[0] if live else None

    loaded = None
    if cfg.get("detect_loaded_save", True):
        candidates = [s for s in saves
                      if s is not newest and s["atime"] is not None
                      and usable_detail(s["detail"])
                      and not is_backup(s) and not is_profile(s)]
        if candidates:
            loaded = max(candidates, key=lambda s: s["atime"])

    chosen, reason = None, ""
    if loaded is not None and (newest is None or loaded["atime"] > newest["mtime"]):
        chosen, reason = loaded, "loaded save"
    elif newest is not None:
        chosen, reason = newest, "newest autosave"
    if chosen is None:
        return None

    state = parse_save(chosen["detail"], cfg)
    state["source"] = chosen["path"]
    state["slot"] = chosen["slot"]
    state["mtime"] = chosen["mtime"]
    state["atime"] = chosen["atime"]
    state["selection"] = reason
    state["key"] = "|".join(str(state[k]) for k in (
        "chapter_raw", "character", "difficulty", "modifiers",
        "collectibles", "playtime", "selection",
    ))
    return state


# --------------------------------------------------------------------------- #
# presence text
# --------------------------------------------------------------------------- #
def pretty_difficulty(value):
    value = (value or "").strip()
    if not value:
        return ""
    return value.title()


def short_modifiers(value):
    value = (value or "").strip()
    if not value:
        return ""
    lowered = value.lower()
    if lowered.startswith("new game+"):
        inner = value[value.find("(") + 1:value.find(")")] if "(" in value else ""
        return ("NG+ " + inner).strip()
    if lowered.startswith("new game"):
        return "NG"
    return value


def build_activity(state, cfg):
    presence = cfg["presence"]
    if state is None:
        state = {
            "chapter": "The Last of Us Part II", "character": "",
            "difficulty": "", "modifiers": "", "collectibles": None,
            "playtime": None,
        }

    character_name = state["character"] if presence.get("show_character") else ""
    character = character_name
    if character:
        character = (presence.get("character_prefix") or "") + character
    difficulty = pretty_difficulty(state["difficulty"]) if presence.get("show_difficulty") else ""
    if presence.get("show_modifier") and difficulty:
        short = short_modifiers(state["modifiers"])
        if short:
            difficulty = (difficulty + " " + short).strip()
    elif presence.get("show_modifier") and not difficulty:
        difficulty = short_modifiers(state["modifiers"])

    collectibles = ""
    if presence.get("show_collectibles") and state["collectibles"] is not None:
        collectibles = "%d collectibles" % state["collectibles"]

    details = ""
    if presence.get("show_chapter"):
        details = (presence.get("details_template") or "{chapter}").format(
            chapter=state["chapter"], character=character,
            difficulty=difficulty, collectibles=collectibles,
        ).strip()

    state_line = (presence.get("state_template") or "{character}").format(
        chapter=state["chapter"], character=character,
        difficulty=difficulty, collectibles=collectibles,
    )
    state_line = " \u00b7 ".join(
        part.strip() for part in state_line.split("\u00b7") if part.strip()
    )

    activity = {"instance": True}
    if details:
        activity["details"] = details[:128]
    if state_line:
        activity["state"] = state_line[:128]

    if presence.get("show_playtime") and state["playtime"]:
        activity["timestamps"] = {"start": int(time.time()) - int(state["playtime"])}

    assets = {}
    large = (presence.get("large_image") or "").strip()
    if large:
        assets["large_image"] = large
        if presence.get("large_text"):
            assets["large_text"] = str(presence["large_text"])[:128]
    if presence.get("small_image_from_character") and character_name:
        key = (presence.get("character_assets") or {}).get(character_name, "")
        if key:
            assets["small_image"] = key
            assets["small_text"] = (character or character_name)[:128]
    if assets:
        activity["assets"] = assets

    return activity


# --------------------------------------------------------------------------- #
# Discord IPC (named pipe)
# --------------------------------------------------------------------------- #
class DiscordIPC:
    """Single-threaded Discord IPC client (no concurrent pipe reads/writes)."""

    def __init__(self, client_id):
        self.client_id = str(client_id)
        self.sock = None
        self.buf = b""
        self.closed = False

    # -- low level ---------------------------------------------------------- #
    def _available(self):
        """Bytes waiting in the pipe, or -1 when the pipe is gone."""
        if self.sock is None:
            return -1
        try:
            handle = msvcrt.get_osfhandle(self.sock.fileno())
        except (OSError, ValueError):
            return -1
        count = ctypes.wintypes.DWORD(0)
        ok = ctypes.windll.kernel32.PeekNamedPipe(
            ctypes.c_void_p(handle), None, 0, None, ctypes.byref(count), None
        )
        return count.value if ok else -1

    def _send_raw(self, opcode, payload):
        if self.sock is None:
            raise OSError("not connected")
        frame = struct.pack("<II", opcode, len(payload)) + payload
        self.sock.write(frame)
        self.sock.flush()

    def _send(self, opcode, obj):
        self._send_raw(opcode, json.dumps(obj).encode("utf-8"))

    def _drain(self, timeout, predicate):
        """Pump messages until predicate(message) is true or timeout expires."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            available = self._available()
            if available < 0:
                raise ConnectionError("Discord pipe closed")
            if available:
                chunk = self.sock.read(available)
                if not chunk:
                    raise ConnectionError("Discord pipe closed")
                self.buf += chunk
                while len(self.buf) >= 8:
                    opcode, length = struct.unpack("<II", self.buf[:8])
                    if len(self.buf) < 8 + length:
                        break
                    body = self.buf[8:8 + length]
                    self.buf = self.buf[8 + length:]
                    if opcode == 3:  # PING
                        self._send_raw(4, body)
                        continue
                    if opcode != 1:
                        continue
                    try:
                        message = json.loads(body.decode("utf-8"))
                    except ValueError:
                        continue
                    if predicate(message):
                        return message
                continue
            time.sleep(0.02)
        return None

    # -- connection --------------------------------------------------------- #
    def connect(self):
        self.close()
        self.closed = False
        self.buf = b""
        for index in range(10):
            path = r"\\.\pipe\discord-ipc-%d" % index
            try:
                sock = open(path, "r+b", buffering=0)
            except OSError:
                continue
            self.sock = sock
            break
        else:
            raise ConnectionError("Discord pipe not found (is Discord running?)")

        address = r"\\.\pipe\discord-ipc-%d" % index
        try:
            self._send(0, {"v": 1, "client_id": self.client_id})
        except OSError:
            self.close()
            raise ConnectionError("could not write to %s" % address)

        message = self._drain(
            10, lambda m: m.get("evt") in ("READY", "ERROR")
        )
        if message is None:
            self.close()
            raise ConnectionError("Discord handshake timed out")
        if message.get("evt") == "ERROR":
            self.close()
            raise ConnectionError("handshake rejected: %s" % message.get("data"))
        return True

    def close(self):
        self.closed = True
        if self.sock is not None:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None

    # -- activity ----------------------------------------------------------- #
    def set_activity(self, activity):
        """Returns (ok, error_text). activity=None clears the presence."""
        nonce = uuid.uuid4().hex
        payload = {
            "cmd": "SET_ACTIVITY",
            "args": {"pid": os.getpid(), "activity": activity},
            "nonce": nonce,
        }
        try:
            self._send(1, payload)
        except OSError as exc:
            return False, "send failed: %s" % exc

        message = self._drain(
            5, lambda m: m.get("evt") == "ERROR" or m.get("nonce") == nonce
        )
        if message is None:
            return False, "no response from Discord"
        if message.get("evt") == "ERROR":
            data = message.get("data") or {}
            return False, str(data.get("message") or data)
        return True, ""


# --------------------------------------------------------------------------- #
# game process detection
# --------------------------------------------------------------------------- #
class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", ctypes.wintypes.DWORD),
        ("cntUsage", ctypes.wintypes.DWORD),
        ("th32ProcessID", ctypes.wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
        ("th32ModuleID", ctypes.wintypes.DWORD),
        ("cntThreads", ctypes.wintypes.DWORD),
        ("th32ParentProcessID", ctypes.wintypes.DWORD),
        ("pcPriClassBase", ctypes.c_long),
        ("dwFlags", ctypes.wintypes.DWORD),
        ("szExeFile", ctypes.c_wchar * 260),
    ]


def game_running(exe_name):
    kernel32 = ctypes.windll.kernel32
    TH32CS_SNAPPROCESS = 0x00000002
    INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
    snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snapshot == INVALID_HANDLE_VALUE or snapshot is None:
        return False
    entry = PROCESSENTRY32W()
    entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
    target = exe_name.lower()
    try:
        if not kernel32.Process32FirstW(snapshot, ctypes.byref(entry)):
            return False
        while True:
            if entry.szExeFile.lower() == target:
                return True
            if not kernel32.Process32NextW(snapshot, ctypes.byref(entry)):
                return False
    finally:
        kernel32.CloseHandle(ctypes.c_void_p(snapshot))
    return False


# --------------------------------------------------------------------------- #
# single instance
# --------------------------------------------------------------------------- #
def acquire_mutex():
    kernel32 = ctypes.windll.kernel32
    kernel32.CreateMutexW.restype = ctypes.c_void_p
    handle = kernel32.CreateMutexW(None, False, MUTEX_NAME)
    if not handle:
        return None
    if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        kernel32.CloseHandle(ctypes.c_void_p(handle))
        return None
    return handle


# --------------------------------------------------------------------------- #
# main loop
# --------------------------------------------------------------------------- #
def run(cfg, force=False):
    client_id = str(cfg.get("client_id", "")).strip()
    if not client_id or client_id == "YOUR_APP_ID":
        log("no Discord application id available - this build is incomplete")
        return 2

    poll = max(2, int(cfg.get("poll_seconds", 5)))
    exe = str(cfg.get("game_process", "tlou-ii.exe")).strip() or "tlou-ii.exe"
    idle_exit = max(0, int(cfg.get("idle_exit_seconds", 900)))

    ipc = None
    assets_enabled = True
    last_key = None
    game_seen = bool(force)
    closed_at = None
    started = time.time()
    announce = True
    last_connect_error = None

    log("starting (exe=%s%s)" % (exe, ", forced" if force else ""))

    try:
        while True:
            running = True if force else game_running(exe)

            if not running:
                if game_seen:
                    log("game closed - clearing presence")
                    if ipc is not None:
                        try:
                            ipc.set_activity(None)
                        except Exception:
                            pass
                        ipc.close()
                        ipc = None
                    game_seen = False
                    last_key = None
                    closed_at = time.time()
                    if not cfg.get("exit_when_game_closes", True):
                        closed_at = None
                elif closed_at is not None:
                    grace = max(0, int(cfg.get("relaunch_grace_seconds", 0)))
                    if time.time() - closed_at >= grace:
                        log("game did not return within %ds - exiting" % grace)
                        return 0
                if idle_exit and closed_at is None and time.time() - started > idle_exit:
                    log("game not started within %ds - exiting" % idle_exit)
                    return 0
                time.sleep(2)
                continue

            if not game_seen:
                game_seen = True
                if closed_at is not None:
                    log("game restarted - watching again")
                    closed_at = None
                else:
                    log("game detected")

            state = None
            try:
                state = read_state(cfg)
            except Exception as exc:
                log("save read failed: %s" % exc)

            if state is None and last_key:
                # Save is mid-write (placeholder text) - keep what we are showing.
                time.sleep(poll)
                continue

            key = state["key"] if state else ""
            needs_send = key != last_key

            if ipc is not None and ipc._available() < 0:
                log("Discord pipe lost - reconnecting")
                ipc.close()
                ipc = None
                last_key = None
                continue

            if ipc is None:
                try:
                    ipc = DiscordIPC(client_id)
                    ipc.connect()
                    log("connected to Discord")
                    last_connect_error = None
                    needs_send = True
                except Exception as exc:
                    message = str(exc)
                    if message != last_connect_error:
                        log("Discord connect failed: %s" % message)
                        last_connect_error = message
                    ipc = None
                    time.sleep(min(poll, 5))
                    continue

            if needs_send:
                activity = build_activity(state, cfg)
                if not assets_enabled:
                    activity.pop("assets", None)
                ok, error = ipc.set_activity(activity)
                if not ok:
                    log("presence rejected: %s" % error)
                    if "asset" in error.lower() and "assets" in activity:
                        assets_enabled = False
                        log("asset key missing - retrying without images")
                        activity.pop("assets", None)
                        ok, error = ipc.set_activity(activity)
                    if not ok:
                        # Pipe probably died (Discord restarted); reconnect next loop.
                        log("dropping Discord connection")
                        ipc.close()
                        ipc = None
                        last_key = None
                        time.sleep(poll)
                        continue
                last_key = key
                if state:
                    log("presence: %s | %s  [%s: %s]" % (
                        activity.get("details"), activity.get("state"),
                        state["selection"], state["slot"]))
                elif announce:
                    log("waiting for first autosave")
                    announce = False
                if state:
                    announce = True

            time.sleep(poll)
    except KeyboardInterrupt:
        log("interrupted - clearing presence")
        if ipc is not None:
            try:
                ipc.set_activity(None)
            except Exception:
                pass
            ipc.close()
        return 0


def main():
    global DEBUG
    parser = argparse.ArgumentParser(description="TLOU2 -> Discord Rich Presence")
    parser.add_argument("--once", action="store_true",
                        help="print the detected save state as JSON and exit")
    parser.add_argument("--console", action="store_true",
                        help="keep running with a visible console")
    parser.add_argument("--no-mutex", action="store_true",
                        help="allow a second instance (for testing)")
    parser.add_argument("--force", action="store_true",
                        help="publish presence even if the game is not running")
    args = parser.parse_args()
    DEBUG = args.console

    cfg = load_config()

    if args.once:
        state = read_state(cfg)
        if state is None:
            print(json.dumps({"error": "no usable save found",
                              "roots": save_roots(cfg)}, indent=2))
            return 1
        print(json.dumps({
            "source": state["source"],
            "slot": state["slot"],
            "selection": state["selection"],
            "chapter": state["chapter"],
            "character": state["character"],
            "difficulty": state["difficulty"],
            "modifiers": state["modifiers"],
            "collectibles": state["collectibles"],
            "playtime_seconds": state["playtime"],
            "presence": build_activity(state, cfg),
        }, indent=2, ensure_ascii=True))
        return 0

    handle = None
    if not args.no_mutex:
        handle = acquire_mutex()
        if handle is None:
            log("another instance is already running")
            return 0
    try:
        return run(cfg, force=args.force)
    finally:
        if handle:
            ctypes.windll.kernel32.CloseHandle(ctypes.c_void_p(handle))


if __name__ == "__main__":
    raise SystemExit(main())
