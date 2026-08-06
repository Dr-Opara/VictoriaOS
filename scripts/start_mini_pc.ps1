<#
.SYNOPSIS
    Launch the VictoriaOS backend (the "Mini PC brain") on Windows, bound
    for LAN access so a Raspberry Pi voice node can reach it.

.DESCRIPTION
    - Validates that required environment variables are set, WITHOUT ever
      printing their values (only presence/absence).
    - Checks whether a Windows Firewall rule allows inbound traffic on the
      target port, and offers to create one if running elevated.
    - Starts uvicorn bound to 0.0.0.0 (not just localhost) so the LAN
      Raspberry Pi voice node can reach it, per docs/DEPLOYMENT.md.

.PARAMETER Port
    Port to bind. Defaults to 8000.

.PARAMETER SkipFirewallCheck
    Skip the Windows Firewall rule check/prompt.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\start_mini_pc.ps1

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\start_mini_pc.ps1 -Port 8080
#>

param(
    [int]$Port = 8000,
    [switch]$SkipFirewallCheck
)

$ErrorActionPreference = "Stop"

function Write-Section($Title) {
    Write-Host ""
    Write-Host "== $Title ==" -ForegroundColor Cyan
}

# ---------------------------------------------------------------------------
# 1. Validate required environment variables (presence only - never values)
# ---------------------------------------------------------------------------
Write-Section "Validating environment"

$envFile = Join-Path $PSScriptRoot "..\.env"
if (Test-Path $envFile) {
    Write-Host "Loading $envFile"
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$') {
            $name = $Matches[1]
            $value = $Matches[2]
            if (-not [System.Environment]::GetEnvironmentVariable($name, "Process")) {
                [System.Environment]::SetEnvironmentVariable($name, $value, "Process")
            }
        }
    }
} else {
    Write-Warning "No .env file found at $envFile - relying on already-set environment variables."
}

$required = @("OPENAI_API_KEY")
$recommended = @("API_KEY", "YAHOO_EMAIL", "YAHOO_APP_PASSWORD")

$missingRequired = @()
foreach ($name in $required) {
    $isSet = [bool][System.Environment]::GetEnvironmentVariable($name, "Process")
    Write-Host ("  {0,-20} {1}" -f $name, $(if ($isSet) { "set" } else { "MISSING" })) `
        -ForegroundColor $(if ($isSet) { "Green" } else { "Red" })
    if (-not $isSet) { $missingRequired += $name }
}

foreach ($name in $recommended) {
    $isSet = [bool][System.Environment]::GetEnvironmentVariable($name, "Process")
    Write-Host ("  {0,-20} {1}" -f $name, $(if ($isSet) { "set" } else { "not set (optional)" })) `
        -ForegroundColor $(if ($isSet) { "Green" } else { "Yellow" })
}

if ($missingRequired.Count -gt 0) {
    Write-Host ""
    Write-Error "Missing required environment variable(s): $($missingRequired -join ', '). Set them in .env and re-run."
    exit 1
}

if (-not [System.Environment]::GetEnvironmentVariable("API_KEY", "Process")) {
    Write-Warning "API_KEY is not set - the API will be unauthenticated. Fine for a purely local test, NOT fine once the Pi (or anything else) reaches this over the LAN."
}

# ---------------------------------------------------------------------------
# 2. Windows Firewall check
# ---------------------------------------------------------------------------
if (-not $SkipFirewallCheck) {
    Write-Section "Checking Windows Firewall"

    $ruleName = "VictoriaOS Backend ($Port/TCP)"
    $existingRule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue

    if ($existingRule) {
        Write-Host "Firewall rule '$ruleName' already exists." -ForegroundColor Green
    } else {
        Write-Warning "No inbound firewall rule found for port $Port. The Raspberry Pi will not be able to reach this backend over the LAN until one is added."
        $isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

        if ($isAdmin) {
            $answer = Read-Host "Add an inbound firewall rule for TCP port $Port now? (y/N)"
            if ($answer -eq "y" -or $answer -eq "Y") {
                New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Protocol TCP -LocalPort $Port -Action Allow | Out-Null
                Write-Host "Firewall rule created." -ForegroundColor Green
            }
        } else {
            Write-Warning "Not running as Administrator - can't create the firewall rule automatically. Run this once, elevated:`n  New-NetFirewallRule -DisplayName '$ruleName' -Direction Inbound -Protocol TCP -LocalPort $Port -Action Allow"
        }
    }
}

# ---------------------------------------------------------------------------
# 3. Show the LAN address the Pi should use
# ---------------------------------------------------------------------------
Write-Section "LAN address for the Raspberry Pi's MINI_PC_URL"
$lanAddresses = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254.*" }
foreach ($addr in $lanAddresses) {
    Write-Host "  http://$($addr.IPAddress):$Port"
}
if (-not $lanAddresses) {
    Write-Warning "Could not detect a LAN IPv4 address. Run 'ipconfig' manually to find one."
}

# ---------------------------------------------------------------------------
# 4. Start the backend, bound to 0.0.0.0 for LAN access
# ---------------------------------------------------------------------------
Write-Section "Starting VictoriaOS backend on 0.0.0.0:$Port"
Write-Host "Health check will be available at http://localhost:$Port/health"
Write-Host ""

python -m uvicorn backend.app:app --host 0.0.0.0 --port $Port
