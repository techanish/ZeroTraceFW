Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Remove-MenuVerb {
  param(
    [string]$BaseKey,
    [string]$VerbName
  )

  $path = "$BaseKey\$VerbName"
  & reg.exe delete $path /f | Out-Null
}

$fileBase = "HKCU\Software\Classes\*\shell"
$folderBase = "HKCU\Software\Classes\Directory\shell"
$dirBase = "HKCU\Software\Classes\Directory\Background\shell"

Remove-MenuVerb -BaseKey $fileBase -VerbName "ZeroTraceFWImport"
Remove-MenuVerb -BaseKey $fileBase -VerbName "ZeroTraceFWOpenSecure"
Remove-MenuVerb -BaseKey $fileBase -VerbName "ZeroTraceFWDestroy"
Remove-MenuVerb -BaseKey $fileBase -VerbName "ZeroTraceFWSetTTL"
Remove-MenuVerb -BaseKey $fileBase -VerbName "ZeroTraceFWSetReads"
Remove-MenuVerb -BaseKey $fileBase -VerbName "ZeroTraceFWSetDeadline"
Remove-MenuVerb -BaseKey $fileBase -VerbName "ZeroTraceFWRead"
Remove-MenuVerb -BaseKey $fileBase -VerbName "ZeroTraceFWExport"

Remove-MenuVerb -BaseKey $folderBase -VerbName "ZeroTraceFWDestroy"
Remove-MenuVerb -BaseKey $folderBase -VerbName "ZeroTraceFWSetTTL"
Remove-MenuVerb -BaseKey $folderBase -VerbName "ZeroTraceFWSetReads"
Remove-MenuVerb -BaseKey $folderBase -VerbName "ZeroTraceFWSetDeadline"
Remove-MenuVerb -BaseKey $folderBase -VerbName "ZeroTraceFWDestroyAll"
Remove-MenuVerb -BaseKey $folderBase -VerbName "ZeroTraceFWLock"
Remove-MenuVerb -BaseKey $folderBase -VerbName "ZeroTraceFWQuit"
Remove-MenuVerb -BaseKey $folderBase -VerbName "ZeroTraceFWControlPanel"
Remove-MenuVerb -BaseKey $folderBase -VerbName "ZeroTraceFWStatus"
Remove-MenuVerb -BaseKey $folderBase -VerbName "ZeroTraceFWList"
Remove-MenuVerb -BaseKey $folderBase -VerbName "ZeroTraceFWAudit"

Remove-MenuVerb -BaseKey $dirBase -VerbName "ZeroTraceFWDestroyAll"
Remove-MenuVerb -BaseKey $dirBase -VerbName "ZeroTraceFWLock"
Remove-MenuVerb -BaseKey $dirBase -VerbName "ZeroTraceFWQuit"
Remove-MenuVerb -BaseKey $dirBase -VerbName "ZeroTraceFWControlPanel"
Remove-MenuVerb -BaseKey $dirBase -VerbName "ZeroTraceFWStatus"
Remove-MenuVerb -BaseKey $dirBase -VerbName "ZeroTraceFWList"
Remove-MenuVerb -BaseKey $dirBase -VerbName "ZeroTraceFWAudit"

Write-Host "ZeroTraceFW Explorer menu removed for current user." -ForegroundColor Green
