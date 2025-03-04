# Use SID instead of "Everyone" (works across all languages)
$FolderPath = "C:\Users\hi\puzzles"
$Acl = Get-Acl $FolderPath
$EveryoneSid = New-Object System.Security.Principal.SecurityIdentifier "S-1-1-0"
$AccessRule = New-Object System.Security.AccessControl.FileSystemAccessRule($EveryoneSid, "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow")
$Acl.SetAccessRule($AccessRule)
Set-Acl $FolderPath $Acl