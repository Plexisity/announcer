#Requires -RunAsAdministrator

# --- Disclaimer ---
# Disabling Windows Defender significantly reduces your system's security
# and makes it vulnerable to malware. This script is provided for informational
# purposes only. Use it at your own risk and only if you understand the implications.
# In most cases, it is strongly recommended to keep Windows Defender enabled.
# ------------------

Write-Host "Checking current status of Windows Defender Real-time Monitoring..."

try {
    # Get the current preference object
    $DefenderStatusBefore = Get-MpPreference

    # Print the current value of DisableRealtimeMonitoring
    Write-Host "Before: DisableRealtimeMonitoring is set to $($DefenderStatusBefore.DisableRealtimeMonitoring)"

    Write-Host "Attempting to disable Windows Defender Real-time Monitoring..."

    # Attempt to disable Real-time Monitoring
    # NOTE: This may require Tamper Protection to be turned off manually first
    # and is often temporary.
    Set-MpPreference -DisableRealtimeMonitoring $true -Force

    Write-Host "Checking status after attempting to disable..."

    # Get the preference object again after the change
    $DefenderStatusAfter = Get-MpPreference

    # Print the new value of DisableRealtimeMonitoring
    Write-Host "After: DisableRealtimeMonitoring is set to $($DefenderStatusAfter.DisableRealtimeMonitoring)"

    Write-Host "Script execution finished."

} catch {
    Write-Host "An error occurred:"
    Write-Error $_
    Write-Host "Please ensure you are running this script as Administrator."
    Write-Host "Also, check if Tamper Protection is enabled in Windows Security settings."
}

# Keep the console window open until the user presses a key
Read-Host "Press Enter to exit"