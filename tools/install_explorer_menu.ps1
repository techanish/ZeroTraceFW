param(
  [Parameter(Mandatory = $false)]
  [string]$ProjectRoot
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-ProjectRoot {
  param([string]$ProjectRoot)

  if (-not [string]::IsNullOrWhiteSpace($ProjectRoot)) {
    return (Resolve-Path -LiteralPath $ProjectRoot).Path
  }

  $scriptDir = Split-Path -Parent $PSCommandPath
  return (Resolve-Path -LiteralPath (Join-Path $scriptDir "..")).Path
}

function Set-MenuCommand {
  param(
    [string]$BaseKey,
    [string]$VerbName,
    [string]$MenuText,
    [string]$Command
  )

  $verbPath = "$BaseKey\$VerbName"
  $cmdPath = "$verbPath\command"

  & reg.exe add $verbPath /v "MUIVerb" /t REG_SZ /d $MenuText /f | Out-Null
  & reg.exe add $cmdPath /ve /t REG_SZ /d $Command /f | Out-Null
}

$root = Resolve-ProjectRoot -ProjectRoot $ProjectRoot
$cmdScript = Join-Path $root "tools\ztfs_cmd.ps1"
$panelScript = Join-Path $root "tools\ztfs_control_panel.ps1"
if (-not (Test-Path -LiteralPath $cmdScript)) {
  throw "Missing command script: $cmdScript"
}
if (-not (Test-Path -LiteralPath $panelScript)) {
  throw "Missing control panel script: $panelScript"
}

$dq = '""'
$psPrefix = "powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File $dq$cmdScript$dq -ProjectRoot $dq$root$dq"
$panelPrefix = "powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File $dq$panelScript$dq -ProjectRoot $dq$root$dq"

Set-MenuCommand -BaseKey "HKCU\Software\Classes\*\shell" -VerbName "ZeroTraceFWImport" -MenuText "ZeroTraceFW: Import into Vault" -Command "$psPrefix -Action import -TargetPath $dq%1$dq"
Set-MenuCommand -BaseKey "HKCU\Software\Classes\*\shell" -VerbName "ZeroTraceFWOpenSecure" -MenuText "ZeroTraceFW: Open Securely (Password)" -Command "$psPrefix -Action open-secure -TargetPath $dq%1$dq"
Set-MenuCommand -BaseKey "HKCU\Software\Classes\*\shell" -VerbName "ZeroTraceFWDestroy" -MenuText "ZeroTraceFW: Destroy in Vault" -Command "$psPrefix -Action destroy -TargetPath $dq%1$dq"
Set-MenuCommand -BaseKey "HKCU\Software\Classes\*\shell" -VerbName "ZeroTraceFWSetTTL" -MenuText "ZeroTraceFW: Set TTL" -Command "$psPrefix -Action set-ttl -TargetPath $dq%1$dq"
Set-MenuCommand -BaseKey "HKCU\Software\Classes\*\shell" -VerbName "ZeroTraceFWSetReads" -MenuText "ZeroTraceFW: Set Read Limit" -Command "$psPrefix -Action set-reads -TargetPath $dq%1$dq"
Set-MenuCommand -BaseKey "HKCU\Software\Classes\*\shell" -VerbName "ZeroTraceFWSetDeadline" -MenuText "ZeroTraceFW: Set Deadline" -Command "$psPrefix -Action set-deadline -TargetPath $dq%1$dq"
Set-MenuCommand -BaseKey "HKCU\Software\Classes\*\shell" -VerbName "ZeroTraceFWRead" -MenuText "ZeroTraceFW: Read Preview" -Command "$psPrefix -Action read -TargetPath $dq%1$dq"
Set-MenuCommand -BaseKey "HKCU\Software\Classes\*\shell" -VerbName "ZeroTraceFWExport" -MenuText "ZeroTraceFW: Export from Vault" -Command "$psPrefix -Action export -TargetPath $dq%1$dq"

Set-MenuCommand -BaseKey "HKCU\Software\Classes\Directory\shell" -VerbName "ZeroTraceFWDestroyAll" -MenuText "ZeroTraceFW: Destroy Entire Vault" -Command "$psPrefix -Action destroy-all"
Set-MenuCommand -BaseKey "HKCU\Software\Classes\Directory\shell" -VerbName "ZeroTraceFWLock" -MenuText "ZeroTraceFW: Lock Vault" -Command "$psPrefix -Action lock"
Set-MenuCommand -BaseKey "HKCU\Software\Classes\Directory\shell" -VerbName "ZeroTraceFWQuit" -MenuText "ZeroTraceFW: Quit Vault" -Command "$psPrefix -Action quit"
Set-MenuCommand -BaseKey "HKCU\Software\Classes\Directory\shell" -VerbName "ZeroTraceFWControlPanel" -MenuText "ZeroTraceFW: Open Control Panel" -Command $panelPrefix
Set-MenuCommand -BaseKey "HKCU\Software\Classes\Directory\shell" -VerbName "ZeroTraceFWStatus" -MenuText "ZeroTraceFW: Queue Status Snapshot" -Command "$psPrefix -Action status"
Set-MenuCommand -BaseKey "HKCU\Software\Classes\Directory\shell" -VerbName "ZeroTraceFWList" -MenuText "ZeroTraceFW: Queue List Files" -Command "$psPrefix -Action list"
Set-MenuCommand -BaseKey "HKCU\Software\Classes\Directory\shell" -VerbName "ZeroTraceFWAudit" -MenuText "ZeroTraceFW: Queue Recent Audit" -Command "$psPrefix -Action audit"

Set-MenuCommand -BaseKey "HKCU\Software\Classes\Directory\Background\shell" -VerbName "ZeroTraceFWDestroyAll" -MenuText "ZeroTraceFW: Destroy Entire Vault" -Command "$psPrefix -Action destroy-all"
Set-MenuCommand -BaseKey "HKCU\Software\Classes\Directory\Background\shell" -VerbName "ZeroTraceFWLock" -MenuText "ZeroTraceFW: Lock Vault" -Command "$psPrefix -Action lock"
Set-MenuCommand -BaseKey "HKCU\Software\Classes\Directory\Background\shell" -VerbName "ZeroTraceFWQuit" -MenuText "ZeroTraceFW: Quit Vault" -Command "$psPrefix -Action quit"
Set-MenuCommand -BaseKey "HKCU\Software\Classes\Directory\Background\shell" -VerbName "ZeroTraceFWControlPanel" -MenuText "ZeroTraceFW: Open Control Panel" -Command $panelPrefix
Set-MenuCommand -BaseKey "HKCU\Software\Classes\Directory\Background\shell" -VerbName "ZeroTraceFWStatus" -MenuText "ZeroTraceFW: Queue Status Snapshot" -Command "$psPrefix -Action status"
Set-MenuCommand -BaseKey "HKCU\Software\Classes\Directory\Background\shell" -VerbName "ZeroTraceFWList" -MenuText "ZeroTraceFW: Queue List Files" -Command "$psPrefix -Action list"
Set-MenuCommand -BaseKey "HKCU\Software\Classes\Directory\Background\shell" -VerbName "ZeroTraceFWAudit" -MenuText "ZeroTraceFW: Queue Recent Audit" -Command "$psPrefix -Action audit"

Write-Host "ZeroTraceFW Explorer menu installed for current user." -ForegroundColor Green
Write-Host "If Explorer is open, close/reopen File Explorer windows to refresh context menus."
