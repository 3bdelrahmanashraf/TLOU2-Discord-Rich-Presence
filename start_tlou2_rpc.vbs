' Silent launcher for TLOU2 Discord Rich Presence.
' Double-click this file (or a shortcut to it). No console window appears.
Option Explicit

Dim fso, shell, base, script, candidates, i, exe, started

Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

base = fso.GetParentFolderName(WScript.ScriptFullName)
script = fso.BuildPath(base, "tlou2_rpc.py")

If Not fso.FileExists(script) Then
    MsgBox "tlou2_rpc.py was not found next to this launcher.", 16, "TLOU2 Discord RPC"
    WScript.Quit 1
End If

' First entry matches the Python install on this PC; the rest are fallbacks.
candidates = Array( _
    "F:\TV\tools\python\pythonw.exe", _
    "pythonw.exe", _
    "python.exe" _
)

started = False
For i = 0 To UBound(candidates)
    exe = candidates(i)
    On Error Resume Next
    shell.Run """" & exe & """ """ & script & """", 0, False
    If Err.Number = 0 Then
        started = True
    End If
    Err.Clear
    On Error GoTo 0
    If started Then Exit For
Next

If Not started Then
    MsgBox "Could not start Python." & vbCrLf & vbCrLf & _
           "Install Python 3 or edit the paths at the top of this file.", _
           16, "TLOU2 Discord RPC"
    WScript.Quit 1
End If
