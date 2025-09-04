# Export Outlook Calendar to ICS
# This PowerShell script helps you export your Outlook calendar to ICS format

Write-Host "Outlook Calendar Export Helper" -ForegroundColor Green
Write-Host "=============================="
Write-Host ""

Write-Host "To export your Outlook calendar to ICS format:" -ForegroundColor Yellow
Write-Host ""
Write-Host "METHOD 1 - Outlook Desktop App:"
Write-Host "1. Open Outlook"
Write-Host "2. Go to File → Open & Export → Import/Export"
Write-Host "3. Select 'Export to a file'"
Write-Host "4. Choose 'iCalendar Format (.ics)'"
Write-Host "5. Select your calendar"
Write-Host "6. Choose date range"
Write-Host "7. Save to this folder as 'outlook-calendar.ics'"
Write-Host ""

Write-Host "METHOD 2 - Outlook Web (outlook.com):"
Write-Host "1. Go to outlook.com and sign in"
Write-Host "2. Click Calendar"
Write-Host "3. Right-click your calendar name in the left sidebar"
Write-Host "4. Select 'Export calendar'"
Write-Host "5. Choose date range"
Write-Host "6. Click 'Export' and save to this folder"
Write-Host ""

Write-Host "METHOD 3 - Copy existing ICS file:"
Write-Host "1. If you have an ICS file from your school/work system"
Write-Host "2. Copy it to this folder: $PWD"
Write-Host "3. The calendar app will automatically detect it"
Write-Host ""

Write-Host "After exporting:" -ForegroundColor Cyan
Write-Host "1. Run: .\update_pi.ps1 -PiAddress <your-pi-ip>"
Write-Host "2. On your Pi calendar app, click 'Import Calendar'"
Write-Host "3. Your Outlook events will be imported!"
Write-Host ""

# Check if we already have ICS files
$existingICS = Get-ChildItem -Path "." -Filter "*.ics"
if ($existingICS) {
    Write-Host "Found existing ICS files:" -ForegroundColor Green
    foreach ($file in $existingICS) {
        Write-Host "  - $($file.Name)" -ForegroundColor White
    }
    Write-Host ""
    Write-Host "These will be automatically copied to your Pi when you run update_pi.ps1"
}

Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
