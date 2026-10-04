' Crea el icono "Mostrador" en el escritorio y, si quieres,
' hace que se encienda solo al prender la computadora.
Option Explicit

Dim shell, fso, carpeta, acceso, respuesta
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
carpeta = fso.GetParentFolderName(WScript.ScriptFullName)

CrearAcceso shell.SpecialFolders("Desktop") & "\Mostrador.lnk", _
            "abrir_mostrador.vbs", "", "Abrir el punto de venta", ""
CrearAcceso shell.SpecialFolders("Desktop") & "\Apagar Mostrador.lnk", _
            "cerrar_mostrador.vbs", "", "Apagar el punto de venta", "%SystemRoot%\System32\shell32.dll,27"

respuesta = MsgBox("Listo: se crearon los iconos ""Mostrador"" y ""Apagar Mostrador"" en tu escritorio." & _
                   vbCrLf & vbCrLf & _
                   "Quieres que Mostrador se encienda solo cada vez que prendas la computadora?", _
                   vbYesNo + vbQuestion, "Mostrador")

If respuesta = vbYes Then
  CrearAcceso shell.SpecialFolders("Startup") & "\Mostrador.lnk", _
              "abrir_mostrador.vbs", "/inicio", "Encender el punto de venta", ""
  MsgBox "Listo. Mostrador se encendera solo al prender la computadora." & vbCrLf & _
         "Para usarlo, da doble clic en el icono Mostrador del escritorio.", vbInformation, "Mostrador"
End If

Sub CrearAcceso(ruta, script, argumentos, descripcion, icono)
  Set acceso = shell.CreateShortcut(ruta)
  acceso.TargetPath = shell.ExpandEnvironmentStrings("%SystemRoot%") & "\System32\wscript.exe"
  acceso.Arguments = """" & carpeta & "\" & script & """ " & argumentos
  acceso.WorkingDirectory = carpeta
  acceso.Description = descripcion
  If icono <> "" Then
    acceso.IconLocation = shell.ExpandEnvironmentStrings(icono)
  ElseIf fso.FileExists(carpeta & "\mostrador.ico") Then
    acceso.IconLocation = carpeta & "\mostrador.ico"
  End If
  acceso.Save
End Sub
