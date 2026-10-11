[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot

$pythonPath = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $pythonPath -PathType Leaf)) {
    Write-Error "Project virtual-environment Python was not found: $pythonPath"
    exit 2
}

foreach ($name in @("MKTY_DOCTOR_USERNAME", "MKTY_DOCTOR_PASSWORD")) {
    $value = [Environment]::GetEnvironmentVariable($name, "Process")
    if ([string]::IsNullOrWhiteSpace($value)) {
        Write-Host "$name=MISSING"
        exit 2
    }
    Write-Host "$name=SET"
}

try {
    $response = Invoke-WebRequest `
        -Uri "http://localhost:8088" `
        -Method Get `
        -TimeoutSec 10 `
        -UseBasicParsing
}
catch {
    Write-Error "Frontend http://localhost:8088 is not accessible."
    exit 2
}

if ($response.StatusCode -ne 200) {
    Write-Error "Frontend http://localhost:8088 returned HTTP $($response.StatusCode), expected 200."
    exit 2
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$baseResultsDirectory = Join-Path $projectRoot "artifacts\junit-doctor-readonly-$timestamp"
$resultsDirectory = $baseResultsDirectory
$suffix = 1
while (Test-Path -LiteralPath $resultsDirectory) {
    $resultsDirectory = "$baseResultsDirectory-$suffix"
    $suffix++
}
New-Item -ItemType Directory -Path $resultsDirectory | Out-Null
$junitPath = Join-Path $resultsDirectory "junit.xml"

$testPaths = @(
    "tests/ui/test_doctor_dashboard.py",
    "tests/ui/test_doctor_appointments.py",
    "tests/ui/test_doctor_appointment_detail.py"
)

$pytestExitCode = 1
$pytestStarted = $false
try {
    & $pythonPath -m pytest -v --junitxml="$junitPath" @testPaths
    $pytestStarted = $true
    $pytestExitCode = $LASTEXITCODE
}
catch {
    Write-Error "pytest could not be started: $($_.Exception.Message)"
}

Write-Host "pytest exit code: $pytestExitCode"
if ($pytestStarted -and $pytestExitCode -ne 0) {
    Write-Host "pytest failed; the original pytest output and traceback are preserved above."
}

if (Test-Path -LiteralPath $junitPath -PathType Leaf) {
    Write-Host "JUnit XML report: $junitPath"
}
else {
    Write-Error "JUnit XML report was not generated: $junitPath"
    if ($pytestExitCode -eq 0) {
        $pytestExitCode = 1
    }
}

exit $pytestExitCode
