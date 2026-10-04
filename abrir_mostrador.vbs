' Abre el punto de venta Mostrador sin mostrar la ventana negra.
' Si ya esta encendido, solo abre la ventana.
' Con el argumento /inicio (al prender la computadora) solo lo enciende.
Option Explicit

Dim shell, fso, carpeta, pythonw, url, i, soloEncender
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

carpeta = fso.GetParentFolderName(WScript.ScriptFullName)
pythonw = carpeta & "\.venv\Scripts\pythonw.exe"
url = "http://127.0.0.1:5000"
soloEncender = (WScript.Arguments.Count > 0)

If Not fso.FileExists(pythonw) Then
  MsgBox "Falta preparar el programa." & vbCrLf & vbCrLf & _
         "Da doble clic una vez en iniciar.bat (en la carpeta del programa), " & _
         "cierra esa ventana y vuelve a abrir Mostrador.", vbExclamation, "Mostrador"
  WScript.Quit
End If

If Not EstaEncendido() Then
  shell.CurrentDirectory = carpeta
  shell.Run """" & pythonw & """ """ & carpeta & "\servidor.py""", 0, False
  For i = 1 To 40
    WScript.Sleep 500
    If EstaEncendido() Then Exit For
  Next
  If Not EstaEncendido() Then
    MsgBox "Mostrador no pudo encenderse." & vbCrLf & vbCrLf & _
           "Abre iniciar.bat para ver el mensaje de error, o revisa el archivo " & _
           "instance\servidor.log.", vbCritical, "Mostrador"
    WScript.Quit
  End If
End If

If Not soloEncender Then AbrirVentana

Function EstaEncendido()
  Dim http
  EstaEncendido = False
  On Error Resume Next
  Set http = CreateObject("MSXML2.ServerXMLHTTP.6.0")
  http.setTimeouts 1000, 1000, 1000, 1000
  http.Open "GET", url & "/salud", False
  http.Send
  If Err.Number = 0 Then
    If http.Status = 200 Then EstaEncendido = True
  End If
  On Error GoTo 0
End Function

Sub AbrirVentana()
  ' Microsoft Edge en modo aplicacion: ventana propia, sin barra de direcciones.
  ' Si Edge no esta, usa el navegador normal.
  On Error Resume Next
  shell.Run "msedge --app=" & url, 1, False
  If Err.Number <> 0 Then
    Err.Clear
    shell.Run url, 1, False
  End If
  On Error GoTo 0
End Sub
