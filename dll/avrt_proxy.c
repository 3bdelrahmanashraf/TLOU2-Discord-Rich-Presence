/*
 * avrt.dll - minimal proxy loader for TLOU2DiscordRPC.asi
 *
 * The game imports AVRT.dll but the install has no ASI loader, so the .asi is
 * never loaded. This proxy forwards every AVRT export to the real System32
 * DLL and then loads the .asi from the game folder. The .asi itself starts the
 * Python helper; no runtime is bundled.
 *
 * Build (mingw-w64 x64):
 *   x86_64-w64-mingw32-gcc -O2 -shared -static-libgcc \
 *     -Wl,--image-base=0x140000000 \
 *     -o avrt.dll avrt_proxy.c avrt_stubs.S avrt_proxy.def
 */

#define WIN32_LEAN_AND_MEAN
#include <windows.h>

/* Order must match avrt_stubs.S and avrt_proxy.def. */
static const char *const export_names[20] = {
    "AvCreateTaskIndex",
    "AvQuerySystemResponsiveness",
    "AvQueryTaskIndexValue",
    "AvRevertMmThreadCharacteristics",
    "AvRtCreateThreadOrderingGroup",
    "AvRtCreateThreadOrderingGroupExA",
    "AvRtCreateThreadOrderingGroupExW",
    "AvRtDeleteThreadOrderingGroup",
    "AvRtJoinThreadOrderingGroup",
    "AvRtLeaveThreadOrderingGroup",
    "AvRtWaitOnThreadOrderingGroup",
    "AvSetMmMaxThreadCharacteristicsA",
    "AvSetMmMaxThreadCharacteristicsW",
    "AvSetMmThreadCharacteristicsA",
    "AvSetMmThreadCharacteristicsW",
    "AvSetMmThreadPriority",
    "AvSetMultimediaMode",
    "AvTaskIndexYield",
    "AvTaskIndexYieldCancel",
    "AvThreadOpenTaskIndex"
};

/* Written once during DLL_PROCESS_ATTACH; the naked stubs in avrt_stubs.S
 * tail-jump through these entries. */
void *g_real[20];

static DWORD WINAPI LoadPlugin(LPVOID param)
{
    wchar_t self[MAX_PATH];
    wchar_t dir[MAX_PATH];
    wchar_t plugin[MAX_PATH];
    wchar_t *slash;

    Sleep(500);
    if (!GetModuleFileNameW((HMODULE)param, self, MAX_PATH))
        return 0;
    slash = wcsrchr(self, L'\\');
    if (!slash)
        return 0;
    *slash = L'\0';
    wcscpy(dir, self);
    wsprintfW(plugin, L"%s\\TLOU2DiscordRPC.asi", dir);
    LoadLibraryW(plugin);
    return 0;
}

BOOL WINAPI DllMain(HINSTANCE instance, DWORD reason, LPVOID reserved)
{
    (void)reserved;
    if (reason == DLL_PROCESS_ATTACH) {
        wchar_t system_dir[MAX_PATH];
        wchar_t real_path[MAX_PATH];
        HMODULE real;
        DWORD i;

        if (!GetSystemDirectoryW(system_dir, MAX_PATH))
            return FALSE;
        wsprintfW(real_path, L"%s\\avrt.dll", system_dir);
        real = LoadLibraryW(real_path);
        if (!real)
            return FALSE;
        for (i = 0; i < 20; i++)
            g_real[i] = (void *)GetProcAddress(real, export_names[i]);

        DisableThreadLibraryCalls(instance);
        CreateThread(NULL, 0, LoadPlugin, (LPVOID)instance, 0, NULL);
    }
    return TRUE;
}
