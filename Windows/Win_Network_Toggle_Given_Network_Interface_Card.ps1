<#
.SYNOPSIS
   Toggle Network Interface Card (NIC) Status
   This script alternates between enabling and disabling the specified NIC.

.DESCRIPTION
   This PowerShell script will toggle the status of the specified Network Interface Card (NIC).

.PARAMETER NICName
   The name of the Network Interface Card (NIC) to toggle.

.NOTES
   This script is intended to be used with Tactical RMM.

.EXEMPLE
    -NICName 'Embedded LOM 1 Port 2'

#>

param (
    [string]$NICName
)

# Function to get a list of available NICs with information
function Get-NICList {
    Get-NetAdapter | Select-Object Name, Status, InterfaceDescription
}

# Check if NICName is provided
if (-not $NICName) {
    Write-Error "NICName parameter is required. Available NICs:"
    Get-NICList
    Exit 1
}

$up = "Up"
$disabled = "Disabled"

# Check the current status of the specified NIC
$lanStatus = Get-NetAdapter | Select-Object Name, Status | Where-Object { $_.Status -match $up -and $_.Name -match $NICName }

# Toggle the NIC status based on the current state
if ($lanStatus) {
    Write-Output ("Disabling $NICName")
    Disable-NetAdapter -Name $NICName -Confirm:$false
} else {
    Write-Output ("Enabling $NICName")
    Enable-NetAdapter -Name $NICName -Confirm:$false
}

Exit