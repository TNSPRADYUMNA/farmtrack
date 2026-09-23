param([Parameter(Mandatory=$true)][ValidatePattern('^[a-z0-9][a-z0-9_-]+$')][string]$DockerHubUser)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
foreach ($service in @('fields', 'activities')) {
    docker build -f "services/$service/Dockerfile" -t "${DockerHubUser}/farmtrack-${service}:1.0.0" .
    if ($LASTEXITCODE -ne 0) { throw 'Image build failed' }
    docker push "${DockerHubUser}/farmtrack-${service}:1.0.0"
    if ($LASTEXITCODE -ne 0) { throw 'Image push failed' }
}
