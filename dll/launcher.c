/*
 * TLOU2DiscordRPC.asi - launches the Discord Rich Presence helper when the
 * game starts. Install next to tlou-ii.exe together with avrt.dll: the game
 * has no ASI loader, so that proxy is what loads this plugin.
 *
 * Build (mingw-w64 x64):
 *   x86_64-w64-mingw32-gcc -O2 -shared -static-libgcc -o TLOU2DiscordRPC.asi launcher.c
 */

#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdio.h>

#define APP_FOLDER_1 L"TLOU2DiscordRPC"
#define APP_FOLDER_2 L"discord-rpc"
#define SCRIPT_PYC   L"tlou2_rpc.pyc"
#define SCRIPT_PY    L"tlou2_rpc.py"
#define START_DELAY_MS 2500

static void Join(wchar_t *out, DWORD cch, const wchar_t *a, const wchar_t *b)
{
    wsprintfW(out, L"%s\\%s", a, b);
    (void)cch;
}

static void StripFile(wchar_t *path)
{
    wchar_t *slash = wcsrchr(path, L'\\');
    if (slash)
        *slash = L'\0';
}

static BOOL FileExists(const wchar_t *path)
{
    DWORD attr = GetFileAttributesW(path);
    return attr != INVALID_FILE_ATTRIBUTES && !(attr & FILE_ATTRIBUTE_DIRECTORY);
}

static void Log(const wchar_t *app_dir, const wchar_t *line, DWORD code)
{
    wchar_t path[MAX_PATH];
    FILE *fp;
    Join(path, MAX_PATH, app_dir, L"launcher.log");
    fp = _wfopen(path, L"a, ccs=UTF-8");
    if (!fp) {
        wchar_t base[MAX_PATH];
        if (GetEnvironmentVariableW(L"LOCALAPPDATA", base, MAX_PATH)) {
            wchar_t folder[MAX_PATH];
            Join(folder, MAX_PATH, base, L"TLOU2DiscordRPC");
            CreateDirectoryW(folder, NULL);
            Join(path, MAX_PATH, folder, L"launcher.log");
            fp = _wfopen(path, L"a, ccs=UTF-8");
        }
    }
    if (!fp)
        return;

    SYSTEMTIME st;
    GetLocalTime(&st);
    if (code)
        fwprintf(fp, L"%04d-%02d-%02d %02d:%02d:%02d [pid %lu]  %ls (error %lu)\n",
                 st.wYear, st.wMonth, st.wDay, st.wHour, st.wMinute, st.wSecond,
                 (unsigned long)GetCurrentProcessId(), line, (unsigned long)code);
    else
        fwprintf(fp, L"%04d-%02d-%02d %02d:%02d:%02d [pid %lu]  %ls\n",
                 st.wYear, st.wMonth, st.wDay, st.wHour, st.wMinute, st.wSecond,
                 (unsigned long)GetCurrentProcessId(), line);
    fclose(fp);
}

static DWORD WINAPI LaunchThread(LPVOID param)
{
    wchar_t self[MAX_PATH];
    wchar_t game_dir[MAX_PATH];
    wchar_t app_dir[MAX_PATH];
    wchar_t script[MAX_PATH];
    wchar_t exe[MAX_PATH];
    wchar_t cmd[3 * MAX_PATH];
    const wchar_t *folders[2] = { APP_FOLDER_1, APP_FOLDER_2 };
    int i;
    BOOL has_app_dir = FALSE;
    BOOL is_pyw = FALSE;

    Sleep(START_DELAY_MS);

    if (!GetModuleFileNameW((HMODULE)param, self, MAX_PATH))
        return 0;

    wsprintfW(game_dir, L"%s", self);
    StripFile(game_dir);

    for (i = 0; i < 2; i++) {
        Join(app_dir, MAX_PATH, game_dir, folders[i]);
        Join(script, MAX_PATH, app_dir, SCRIPT_PYC);
        if (!FileExists(script))
            Join(script, MAX_PATH, app_dir, SCRIPT_PY);
        if (FileExists(script)) {
            has_app_dir = TRUE;
            break;
        }
    }
    if (!has_app_dir) {
        Log(game_dir, L"helper folder not found next to the .asi, nothing to do", 0);
        return 0;
    }

    /* 1. interpreter beside the script, 2. pythonw.exe on PATH,
     * 3. the py launcher on PATH (installed by python.org into C:\Windows). */
    Join(exe, MAX_PATH, app_dir, L"pythonw.exe");
    if (!FileExists(exe)) {
        if (!SearchPathW(NULL, L"pythonw.exe", NULL, MAX_PATH, exe, NULL)) {
            if (!SearchPathW(NULL, L"pyw.exe", NULL, MAX_PATH, exe, NULL)) {
                Log(app_dir, L"no Python found - install Python 3 from "
                             L"python.org/downloads, then start the game again", 0);
                return 0;
            }
            is_pyw = TRUE;
        }
    }

    if (is_pyw)
        wsprintfW(cmd, L"\"%s\" -3 \"%s\"", exe, script);
    else
        wsprintfW(cmd, L"\"%s\" \"%s\"", exe, script);

    STARTUPINFOW si;
    PROCESS_INFORMATION pi;
    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);
    ZeroMemory(&pi, sizeof(pi));

    if (CreateProcessW(exe, cmd, NULL, NULL, FALSE, CREATE_NO_WINDOW,
                       NULL, app_dir, &si, &pi)) {
        wchar_t msg[3 * MAX_PATH];
        wsprintfW(msg, L"started: %s", cmd);
        Log(app_dir, msg, 0);
        CloseHandle(pi.hThread);
        CloseHandle(pi.hProcess);
    } else {
        Log(app_dir, L"CreateProcess failed", GetLastError());
    }
    return 0;
}

BOOL WINAPI DllMain(HINSTANCE instance, DWORD reason, LPVOID reserved)
{
    (void)reserved;
    if (reason == DLL_PROCESS_ATTACH) {
        HANDLE thread;
        DisableThreadLibraryCalls(instance);
        thread = CreateThread(NULL, 0, LaunchThread, (LPVOID)instance, 0, NULL);
        if (thread)
            CloseHandle(thread);
    }
    return TRUE;
}
