# PowerShell script for Raspberry Pi Calendar App remote management
# Run with: powershell -ExecutionPolicy Bypass -File .\pi_manager.ps1

param(
    [string]$PiIP = "",
    [string]$Action = "menu"
)

# Configuration file
$configFile = "pi_config.json"

# Load or create configuration
function Load-Config {
    if (Test-Path $configFile) {
        return Get-Content $configFile | ConvertFrom-Json
    } else {
        return @{
            pi_ip = ""
            username = "pi"
            dev_path = "/home/pi/calendar-app-dev"
            prod_path = "/home/pi/calendar-app"
        }
    }
}

# Save configuration
function Save-Config($config) {
    $config | ConvertTo-Json | Set-Content $configFile
}

# Main menu
function Show-Menu {
    Clear-Host
    Write-Host "Raspberry Pi Calendar App - Remote Manager" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "1.  Configure Pi Connection" -ForegroundColor Yellow
    Write-Host "2.  Test Connection" -ForegroundColor Cyan
    Write-Host "3.  SSH to Pi" -ForegroundColor Cyan
    Write-Host "4.  Open VNC Viewer" -ForegroundColor Cyan
    Write-Host "5.  Open File Share" -ForegroundColor Cyan
    Write-Host "6.  Upload Current Files" -ForegroundColor Magenta
    Write-Host "7.  Download Pi Files" -ForegroundColor Magenta
    Write-Host "8.  Sync Dev to Production" -ForegroundColor Red
    Write-Host "9.  View Production Logs" -ForegroundColor White
    Write-Host "10. Restart Pi Service" -ForegroundColor Red
    Write-Host "11. Stop Pi Service" -ForegroundColor Red
    Write-Host "12. Check Pi Service Status" -ForegroundColor White
    Write-Host "13. Run Development Mode" -ForegroundColor Green
    Write-Host "14. Create Backup" -ForegroundColor Yellow
    Write-Host "15. Exit" -ForegroundColor Gray
    Write-Host ""
}

# Configure connection
function Set-PiConnection {
    $config = Load-Config
    
    Write-Host "Current Configuration:" -ForegroundColor Yellow
    Write-Host "Pi IP: $($config.pi_ip)"
    Write-Host "Username: $($config.username)"
    Write-Host ""
    
    $newIp = Read-Host "Enter Pi IP address (or press Enter to keep current)"
    if ($newIp -ne "") { $config.pi_ip = $newIp }
    
    $newUser = Read-Host "Enter username (or press Enter to keep current)"
    if ($newUser -ne "") { $config.username = $newUser }
    
    Save-Config $config
    Write-Host "Configuration saved!" -ForegroundColor Green
}

# Test connection
function Test-Connection($config) {
    Write-Host "Testing connection to $($config.pi_ip)..." -ForegroundColor Yellow
    
    $pingResult = Test-NetConnection -ComputerName $config.pi_ip -Port 22 -WarningAction SilentlyContinue
    if ($pingResult.TcpTestSucceeded) {
        Write-Host "✓ SSH connection successful" -ForegroundColor Green
    } else {
        Write-Host "✗ SSH connection failed" -ForegroundColor Red
        return $false
    }
    
    try {
        $result = ssh "$($config.username)@$($config.pi_ip)" "echo 'Connection OK'"
        if ($result -eq "Connection OK") {
            Write-Host "✓ SSH authentication successful" -ForegroundColor Green
            return $true
        }
    } catch {
        Write-Host "✗ SSH authentication failed" -ForegroundColor Red
        Write-Host "Make sure you've set up SSH keys or can login with password" -ForegroundColor Yellow
    }
    return $false
}

# SSH to Pi
function Connect-SSH($config) {
    Write-Host "Opening SSH connection to Pi..." -ForegroundColor Green
    ssh "$($config.username)@$($config.pi_ip)"
}

# Open VNC
function Open-VNC($config) {
    Write-Host "Opening VNC connection..." -ForegroundColor Green
    Write-Host "Connect your VNC viewer to: $($config.pi_ip):5900" -ForegroundColor Yellow
    Start-Process "vnc://$($config.pi_ip):5900"
}

# Open file share
function Open-FileShare($config) {
    Write-Host "Opening file share..." -ForegroundColor Green
    $sharePath = "\\$($config.pi_ip)\calendar-app"
    Start-Process "explorer" $sharePath
}

# Upload files
function Upload-Files($config) {
    Write-Host "Uploading files to Pi development directory..." -ForegroundColor Magenta
    
    if (Test-Path "calendar_app.py") {
        scp "calendar_app.py" "$($config.username)@$($config.pi_ip):$($config.dev_path)/"
        Write-Host "✓ calendar_app.py uploaded" -ForegroundColor Green
    }
    
    if (Test-Path "start_calendar.sh") {
        scp "start_calendar.sh" "$($config.username)@$($config.pi_ip):$($config.dev_path)/"
        Write-Host "✓ start_calendar.sh uploaded" -ForegroundColor Green
    }
    
    if (Test-Path "calendar-app.service") {
        scp "calendar-app.service" "$($config.username)@$($config.pi_ip):$($config.dev_path)/"
        Write-Host "✓ calendar-app.service uploaded" -ForegroundColor Green
    }
    
    Write-Host "Upload complete! Run option 8 to sync to production." -ForegroundColor Yellow
}

# Download files
function Download-Files($config) {
    Write-Host "Downloading files from Pi..." -ForegroundColor Magenta
    
    # Create local backup directory
    $backupDir = "pi_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    New-Item -ItemType Directory -Name $backupDir -Force | Out-Null
    
    scp "$($config.username)@$($config.pi_ip):$($config.dev_path)/*" "$backupDir/"
    Write-Host "✓ Files downloaded to $backupDir" -ForegroundColor Green
}

# Sync to production
function Sync-ToProduction($config) {
    Write-Host "Syncing development to production on Pi..." -ForegroundColor Red
    ssh "$($config.username)@$($config.pi_ip)" "/home/pi/sync-from-dev.sh"
}

# View logs
function View-Logs($config) {
    Write-Host "Viewing production service logs (Ctrl+C to exit)..." -ForegroundColor White
    ssh "$($config.username)@$($config.pi_ip)" "sudo journalctl -u calendar-app.service -f"
}

# Service control functions
function Restart-Service($config) {
    Write-Host "Restarting calendar service on Pi..." -ForegroundColor Red
    ssh "$($config.username)@$($config.pi_ip)" "sudo systemctl restart calendar-app.service"
    Write-Host "Service restarted!" -ForegroundColor Green
}

function Stop-Service($config) {
    Write-Host "Stopping calendar service on Pi..." -ForegroundColor Red
    ssh "$($config.username)@$($config.pi_ip)" "sudo systemctl stop calendar-app.service"
    Write-Host "Service stopped!" -ForegroundColor Yellow
}

function Get-ServiceStatus($config) {
    Write-Host "Checking service status..." -ForegroundColor White
    ssh "$($config.username)@$($config.pi_ip)" "sudo systemctl status calendar-app.service --no-pager"
}

# Run in development mode
function Start-DevMode($config) {
    Write-Host "Starting calendar app in development mode on Pi..." -ForegroundColor Green
    ssh "$($config.username)@$($config.pi_ip)" "cd $($config.dev_path) && python3 calendar_app.py"
}

# Create backup
function Create-Backup($config) {
    Write-Host "Creating backup on Pi..." -ForegroundColor Yellow
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    ssh "$($config.username)@$($config.pi_ip)" "cp -r $($config.prod_path) /home/pi/calendar-app-backup/manual-$timestamp"
    Write-Host "✓ Backup created: manual-$timestamp" -ForegroundColor Green
}

# Main execution
if ($Action -eq "menu") {
    $config = Load-Config
    
    if ($config.pi_ip -eq "") {
        Write-Host "Pi IP not configured. Please configure connection first." -ForegroundColor Red
        Set-PiConnection
        $config = Load-Config
    }
    
    do {
        Show-Menu
        $choice = Read-Host "Select option (1-15)"
        
        switch ($choice) {
            "1" { Set-PiConnection; $config = Load-Config }
            "2" { Test-Connection $config }
            "3" { Connect-SSH $config }
            "4" { Open-VNC $config }
            "5" { Open-FileShare $config }
            "6" { Upload-Files $config }
            "7" { Download-Files $config }
            "8" { Sync-ToProduction $config }
            "9" { View-Logs $config }
            "10" { Restart-Service $config }
            "11" { Stop-Service $config }
            "12" { Get-ServiceStatus $config }
            "13" { Start-DevMode $config }
            "14" { Create-Backup $config }
            "15" { exit }
            default { Write-Host "Invalid option. Please try again." -ForegroundColor Red }
        }
        
        if ($choice -ne "15") {
            Write-Host ""
            Read-Host "Press Enter to continue"
        }
    } while ($choice -ne "15")
} else {
    Write-Host "Use -Action 'menu' to run interactively" -ForegroundColor Yellow
}
