# Create OGCAI Desktop Shortcut
$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Desktop)
$ShortcutPath = Join-Path $DesktopPath "OGCAI AI Assistant.lnk"

$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "wscript.exe"
$Shortcut.Arguments = '"D:\OGCAI\scripts\launch_desktop.vbs"'
$Shortcut.WorkingDirectory = "D:\OGCAI"
$Shortcut.Description = "OGCAI - Personal Local AI Assistant"

$edgePath = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
if (-not (Test-Path $edgePath)) {
    $edgePath = "C:\Program Files\Microsoft\Edge\Application\msedge.exe"
}
if (Test-Path $edgePath) {
    $Shortcut.IconLocation = "$edgePath,0"
}

$Shortcut.Save()
Write-Host "Launcher shortcut created successfully at: $ShortcutPath"

# Create Stop OGCAI Shortcut
$StopShortcutPath = Join-Path $DesktopPath "Stop OGCAI.lnk"
$StopShortcut = $WshShell.CreateShortcut($StopShortcutPath)
$StopShortcut.TargetPath = "cmd.exe"
$StopShortcut.Arguments = '/c "D:\OGCAI\stop_ogcai.bat"'
$StopShortcut.WorkingDirectory = "D:\OGCAI"
$StopShortcut.Description = "Stop all OGCAI services"
$StopShortcut.Save()
Write-Host "Stop shortcut created successfully at: $StopShortcutPath"
