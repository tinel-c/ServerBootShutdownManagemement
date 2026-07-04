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

& gh release create $Tag --title $Title --notes-file $NotesFile
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "If gh failed (e.g. proxy), create release in browser:"
    Write-Host "  https://github.com/tinel-c/ServerBootShutdownManagemement/releases/new?tag=$Tag"
    Write-Host "  Title: $Title"
    Write-Host "  Paste content from docs/releases/RELEASE_NOTES_v$Version.md"
    exit 1
}

Write-Host "Done: https://github.com/tinel-c/ServerBootShutdownManagemement/releases/tag/$Tag"
