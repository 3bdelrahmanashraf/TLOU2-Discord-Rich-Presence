# Rebuilds the installable Nexus package.
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File pack.ps1
#   powershell -NoProfile -ExecutionPolicy Bypass -File pack.ps1 -Version 1.2.0
#
# Needs:
#   - mingw-w64 on PATH, or -Gcc "C:\path\to\x86_64-w64-mingw32-gcc.exe"
#   - any Python 3 on PATH (only for the smoke test; it is NOT shipped)
#
# The package carries no Python runtime: the user installs Python themselves.
# config.json is baked into the shipped script, encoded, and never copied to the
# package, so users get no settings file to read, edit or re-point at another
# Discord application. Edit config.json locally, then rebuild.
param(
    [string]$Version = "1.2.0",
    [string]$Gcc = "x86_64-w64-mingw32-gcc"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$asi = Join-Path $root "TLOU2DiscordRPC.asi"
$distRoot = Join-Path $root "dist"
$stage = Join-Path $distRoot "TLOU2-Discord-Rich-Presence"
$app = Join-Path $stage "TLOU2DiscordRPC"

Write-Host "== building plugin"
# Two things make an otherwise identical build differ byte for byte, both
# removed here:
#   - relative paths, because gcc records the compile path in the output;
#   - w64devkit's linker picks a random PE image base on every run, which
#     changes ImageBase, the checksum and every absolute pointer in .data.
# Pinning the base keeps ASLR (the DLL is still relocatable; the loader picks
# the real address) while making the file identical on any machine.
Push-Location $root
try {
    & $Gcc -O2 -shared -static-libgcc '-Wl,--image-base=0x140000000' `
        -o "TLOU2DiscordRPC.asi" "dll\launcher.c"
    if ($LASTEXITCODE -ne 0) { throw "compiler failed (plugin)" }
    & $Gcc -O2 -shared -static-libgcc '-Wl,--image-base=0x140000000' `
        -o "avrt.dll" "dll\avrt_proxy.c" "dll\avrt_stubs.S" "dll\avrt_proxy.def"
    if ($LASTEXITCODE -ne 0) { throw "compiler failed (proxy)" }
} finally {
    Pop-Location
}

Write-Host "== staging"
Remove-Item $stage -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $app | Out-Null
Copy-Item $asi $stage
Copy-Item (Join-Path $root "dll\avrt.dll") $stage
Copy-Item (Join-Path $root "mod\README.txt") $stage

Write-Host "== embedding settings"
# XOR the JSON with a fixed key, then base64 it, so the shipped file contains no
# readable application id, templates or asset keys.
$text = Get-Content (Join-Path $root "config.json") -Raw
$bytes = [System.Text.Encoding]::UTF8.GetBytes($text)
for ($i = 0; $i -lt $bytes.Length; $i++) { $bytes[$i] = $bytes[$i] -bxor 0x5A }
$blob = [Convert]::ToBase64String($bytes)

$source = Get-Content (Join-Path $root "tlou2_rpc.py") -Raw
if ($source -notmatch 'EMBEDDED_CONFIG = ""') {
    throw 'EMBEDDED_CONFIG marker missing from tlou2_rpc.py'
}
$source = $source.Replace('EMBEDDED_CONFIG = ""', "EMBEDDED_CONFIG = `"$blob`"")
[System.IO.File]::WriteAllText((Join-Path $app "tlou2_rpc.py"), $source,
    (New-Object System.Text.UTF8Encoding($false)))

Write-Host "== verify"
if (Test-Path (Join-Path $app "config.json")) { throw "config.json must not ship" }
if (Test-Path (Join-Path $app "runtime")) { throw "the package must not bundle Python" }
if (-not (Test-Path (Join-Path $stage "avrt.dll"))) { throw "AVRT proxy is missing" }
if (-not (Test-Path (Join-Path $stage "TLOU2DiscordRPC.asi"))) { throw "plugin is missing" }
$nested = Get-ChildItem $stage -Recurse -File |
    Where-Object { $_.Extension -match '^\.(zip|7z|rar|tar|gz|bz2|xz)$' }
if ($nested) { throw ("archive inside the package: " + ($nested.FullName -join ", ")) }

# Smoke test with whatever Python the machine has - the point is that the
# shipped script is not tied to one interpreter version.
$probeExe = $null
$probeArgs = @()
foreach ($cand in @(@("py", "-3"), @("python", $null))) {
    try {
        & $cand[0] --version *> $null
        if ($LASTEXITCODE -eq 0) {
            $probeExe = $cand[0]
            if ($cand[1]) { $probeArgs += $cand[1] }
            break
        }
    } catch { }
}
if (-not $probeExe) { throw "no Python 3 on PATH - needed only to smoke-test the build" }

$probe = & $probeExe @probeArgs (Join-Path $app "tlou2_rpc.py") --once 2>&1
$probeText = ($probe | Out-String)
# Exit 0 means a save was found and a payload was built. Exit 1 with this
# message means the script and its embedded settings loaded fine but the machine
# simply has no TLOU2 saves - which is the normal case for a reviewer's PC.
if ($LASTEXITCODE -ne 0) {
    if ($probeText -match '"no usable save found"') {
        Write-Host "   no TLOU2 saves on this machine - config loaded, nothing to read"
    } else {
        throw "shipped script failed to run: $probeText"
    }
} elseif (-not ($probe | Select-String -SimpleMatch '"details"')) {
    throw "shipped script produced no presence"
}
Remove-Item (Join-Path $app "rpc.log"), (Join-Path $app "rpc.log.1"),
    (Join-Path $app "launcher.log") -Force -ErrorAction SilentlyContinue

Write-Host "== zip"
$zip = Join-Path $distRoot "TLOU2-Discord-Rich-Presence-$Version.zip"
Remove-Item $zip -Force -ErrorAction SilentlyContinue
# Pin timestamps so the same sources produce the same archive, not just the
# same contents. (Zip stores DOS times, so this is exact within one timezone.)
$stamp = [datetime]::SpecifyKind([datetime]"2026-11-19T00:00:00", [System.DateTimeKind]::Local)
Get-ChildItem $stage -Recurse -File | ForEach-Object { $_.LastWriteTime = $stamp }
Compress-Archive -Path (Join-Path $stage "*") -DestinationPath $zip -CompressionLevel Optimal
"{0}  ({1:N1} KB)" -f $zip, ((Get-Item $zip).Length / 1KB)
