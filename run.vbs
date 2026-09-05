Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")

strScriptDir = FSO.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = strScriptDir

strPythonW = ""
strLocalApp = WshShell.ExpandEnvironmentStrings("%LOCALAPPDATA%")
If FSO.FileExists(strLocalApp & "\Programs\Python\Python314\pythonw.exe") Then
    strPythonW = """" & strLocalApp & "\Programs\Python\Python314\pythonw.exe"""
ElseIf FSO.FileExists(strLocalApp & "\Programs\Python\Python313\pythonw.exe") Then
    strPythonW = """" & strLocalApp & "\Programs\Python\Python313\pythonw.exe"""
ElseIf FSO.FileExists(strLocalApp & "\Programs\Python\Python310\pythonw.exe") Then
    strPythonW = """" & strLocalApp & "\Programs\Python\Python310\pythonw.exe"""
Else
    strPythonW = "pythonw.exe"
End If

strArgs = "--tray"
If WScript.Arguments.Count > 0 Then
    strArgs = ""
    For Each arg In WScript.Arguments
        strArgs = strArgs & " " & arg
    Next
End If

WshShell.Run strPythonW & " """ & strScriptDir & "\main.py"" " & strArgs, 0, False
