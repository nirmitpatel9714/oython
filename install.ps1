Write-Host "🚀 Installing Oython..." -ForegroundColor Cyan

# Check if oython.py exists in the current directory
if (-Not (Test-Path ".\oython.py")) {
    Write-Host "❌ Error: oython.py not found in the current directory." -ForegroundColor Red
    Write-Host "Please run this script from the Oython repository root."
    exit
}

# Create installation directory
$InstallDir = "$env:USERPROFILE\.oython"
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
Copy-Item -Path ".\oython.py" -Destination "$InstallDir\oython.py" -Force

# Create wrapper script in ~/.local/bin
$BinDir = "$env:USERPROFILE\.local\bin"
New-Item -ItemType Directory -Force -Path $BinDir | Out-Null

$WrapperPath = "$BinDir\oython.bat"
$WrapperContent = "@echo off`npython `"$InstallDir\oython.py`" %*"
Set-Content -Path $WrapperPath -Value $WrapperContent

Write-Host "✅ Oython installed successfully!" -ForegroundColor Green
Write-Host "============================================================"
Write-Host "⚠️ IMPORTANT: Please ensure that $BinDir is in your system PATH environment variable." -ForegroundColor Yellow
Write-Host "You can add it by searching 'Environment Variables' in Windows Search."
Write-Host "After adding it, restart your terminal and you can run '.oy' files by typing:"
Write-Host "oython your_file.oy" -ForegroundColor Cyan
Write-Host "============================================================"
