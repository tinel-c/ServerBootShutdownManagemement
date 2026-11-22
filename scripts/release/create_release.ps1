#Requires -Version 5.1
<#
.SYNOPSIS
  Create a GitHub release from docs/releases/RELEASE_NOTES_vX.Y.Z.md

.EXAMPLE
  .\scripts\release\create_release.ps1 3.11.8
  .\scripts\release\create_release.ps1 v3.11.8 "v3.11.8 — Custom title"
#>
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string] $Version,

    [Parameter(Position = 1)]
    [string] $Title
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $RepoRoot

$Version = $Version -replace '^v', ''
$Tag = "v$Version"
$NotesFile = Join-Path $RepoRoot "docs/releases/RELEASE_NOTES_v$Version.md"

if (-not (Test-Path $NotesFile)) {
    Write-Error "Release notes not found: $NotesFile"
}

if (-not $Title) {
    $FirstLine = (Get-Content $NotesFile -TotalCount 1)
    if ($FirstLine -match '^# v[\d.]+ \(.+\)\s+(.+)$') {
        $subtitle = $Matches[1] -replace '^[-\u2014\s]+', ''
        $Title = "$Tag - $subtitle"
    }
    else {
        $Title = $Tag
    }
}

$env:HTTP_PROXY = $null
$env:HTTPS_PROXY = $null
$env:ALL_PROXY = $null

Write-Host "Creating GitHub release $Tag..."
Write-Host "  Title: $Title"
Write-Host "  Notes: docs/releases/RELEASE_NOTES_v$Version.md"

$ClientVersionFile = Join-Path $RepoRoot "client\VERSION"
$ClientVersion = (Get-Content $ClientVersionFile -TotalCount 1).Trim().TrimStart("v", "V")
if ($ClientVersion -ne $Version) {
    Write-Error "client/VERSION is $ClientVersion but the release tag is $Version. Keep them the same so installed PCs report the release they are running."
}

& gh release create $Tag --title $Title --notes-file $NotesFile
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "If gh failed (e.g. proxy), create release in browser:"
    Write-Host "  https://github.com/tinel-c/ServerBootShutdownManagemement/releases/new?tag=$Tag"
    Write-Host "  Title: $Title"
    Write-Host "  Paste content from docs/releases/RELEASE_NOTES_v$Version.md"
    exit 1
}

Write-Host "Packaging Windows client for installed PCs..."
python (Join-Path $RepoRoot "scripts\release\package_client.py")
if ($LASTEXITCODE -ne 0) {
    Write-Error "Client package failed. The GitHub release exists, but PCs will not see a client zip."
}
$ClientZip = Join-Path $RepoRoot "dist\client-v$Version.zip"
& gh release upload $Tag $ClientZip --clobber
if ($LASTEXITCODE -ne 0) {
    Write-Error "Could not upload $ClientZip. Installed PCs only update when a *client*.zip asset is on the release."
}

Write-Host "Done: https://github.com/tinel-c/ServerBootShutdownManagemement/releases/tag/$Tag"
Write-Host "Online PCs update within 24 hours, or immediately with:"
Write-Host "  python scripts/client/deploy_client_update.py --notify --status"
