# Update Calendar App on Raspberry Pi
# This script pushes the updated calendar app to your Pi

param(
    [Parameter(Mandatory=$true)]
    [string]$PiAddress,
    [string]$Username = "payto"
)

Write-Host "Updating Calendar App on Raspberry Pi..." -ForegroundColor Green

# Copy the updated calendar_app.py, classes.txt, and any ICS files to the Pi
$calendarSource = "calendar_app.py"
$classesSource = "classes.txt"
$destination = "${Username}@${PiAddress}:/home/${Username}/calendar-app/"

Write-Host "Copying updated files to Pi..."
scp $calendarSource $destination
scp $classesSource $destination

# Copy any ICS files
$icsFiles = Get-ChildItem -Path "." -Filter "*.ics"
foreach ($file in $icsFiles) {
    Write-Host "Copying $($file.Name)..."
    scp $file.Name $destination
}

# Copy auto-generated class templates if they exist
if (Test-Path "classes_from_ics.txt") {
    Write-Host "Copying classes_from_ics.txt..."
    scp "classes_from_ics.txt" $destination
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "Files copied successfully!" -ForegroundColor Green
    
    # Restart the calendar service
    Write-Host "Restarting calendar service..."
    ssh "${Username}@${PiAddress}" "sudo systemctl restart calendar-app"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Calendar app updated and restarted successfully!" -ForegroundColor Green
        Write-Host "The dialog windows should now be properly sized for your touchscreen." -ForegroundColor Yellow
    } else {
        Write-Host "Error restarting service. You may need to restart manually." -ForegroundColor Red
    }
} else {
    Write-Host "Error copying files to Pi." -ForegroundColor Red
}

Write-Host "`nUpdate complete. Test the calendar app on your Pi to verify the dialogs are now touchscreen-friendly."
