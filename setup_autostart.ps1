# Run in PowerShell as Admin to create auto-start task
$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument '/c cd /d "C:\Users\Prasanna\OneDrive\Desktop\attendance_system" && pythonw app.py' -WorkingDirectory "C:\Users\Prasanna\OneDrive\Desktop\attendance_system"
$trigger = New-ScheduledTaskTrigger -AtStartup
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName "AIAttendanceSystem" -Action $action -Trigger $trigger -Settings $settings -Description "AI Attendance System Flask App" -RunLevel Highest
