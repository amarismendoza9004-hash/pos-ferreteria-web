' Apaga el punto de venta Mostrador.
Option Explicit

Dim shell, fso, carpeta, archivoPid, pid
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

carpeta = fso.GetParentFolderName(WScript.ScriptFullName)
archivoPid = carpeta & "\instance\servidor.pid"

If Not fso.FileExists(archivoPid) Then
  MsgBox "Mostrador no esta encendido.", vbInformation, "Mostrador"
  WScript.Quit
End If

pid = Trim(fso.OpenTextFile(archivoPid).ReadAll())
shell.Run "taskkill /PID " & pid & " /F", 0, True
fso.DeleteFile archivoPid
MsgBox "Mostrador se apago.", vbInformation, "Mostrador"
