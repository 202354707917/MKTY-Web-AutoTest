[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$script:readonlyPipelineFailure = $false

function Report-ReadonlyFailure {
    param([Parameter(Mandatory = $true)][string]$Message)

    Write-Error $Message -ErrorAction Continue
    $script:readonlyPipelineFailure = $true
}

$pythonPath = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $pythonPath -PathType Leaf)) {
    Report-ReadonlyFailure "Project virtual-environment Python was not found: $pythonPath"
    exit 2
}

$missingCredentials = $false
foreach ($name in @(
    "MKTY_UI_TEST_USERNAME",
    "MKTY_UI_TEST_PASSWORD",
    "MKTY_DOCTOR_USERNAME",
    "MKTY_DOCTOR_PASSWORD"
)) {
    $value = [Environment]::GetEnvironmentVariable($name, "Process")
    if ([string]::IsNullOrWhiteSpace($value)) {
        Write-Host "$name=MISSING"
        $missingCredentials = $true
    }
    else {
        Write-Host "$name=SET"
    }
}
if ($missingCredentials) {
    Report-ReadonlyFailure "One or more readonly UI test credential variables are missing."
    exit 2
}

try {
    $response = Invoke-WebRequest `
        -Uri "http://localhost:8088" `
        -Method Get `
        -TimeoutSec 10 `
        -UseBasicParsing
}
catch {
    Report-ReadonlyFailure "Frontend http://localhost:8088 is not accessible."
    exit 2
}

if ($response.StatusCode -ne 200) {
    Report-ReadonlyFailure "Frontend http://localhost:8088 returned HTTP $($response.StatusCode), expected 200."
    exit 2
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$baseResultsDirectory = Join-Path $projectRoot "artifacts\junit-readonly-regression-$timestamp"
$resultsDirectory = $baseResultsDirectory
$baseAllureResultsDirectory = Join-Path $projectRoot "artifacts\allure-results-readonly-regression-$timestamp"
$allureResultsDirectory = $baseAllureResultsDirectory
$baseReportDirectory = Join-Path $projectRoot "artifacts\allure-report-readonly-regression-$timestamp"
$reportDirectory = $baseReportDirectory
$suffix = 1
while (
    (Test-Path -LiteralPath $resultsDirectory) -or
    (Test-Path -LiteralPath $allureResultsDirectory) -or
    (Test-Path -LiteralPath $reportDirectory)
) {
    $resultsDirectory = "$baseResultsDirectory-$suffix"
    $allureResultsDirectory = "$baseAllureResultsDirectory-$suffix"
    $reportDirectory = "$baseReportDirectory-$suffix"
    $suffix++
}
New-Item -ItemType Directory -Path $resultsDirectory | Out-Null
New-Item -ItemType Directory -Path $allureResultsDirectory | Out-Null
$junitPath = Join-Path $resultsDirectory "junit.xml"

# Restrict collection to UI readonly tests and explicitly exclude write tests.
$pytestExitCode = 1
$pytestStarted = $false
try {
    & $pythonPath -m pytest -v `
        --junitxml="$junitPath" `
        --alluredir="$allureResultsDirectory" `
        -m "ui and readonly and not write" `
        "tests/ui"
    $pytestStarted = $true
    $pytestExitCode = $LASTEXITCODE
}
catch {
    Report-ReadonlyFailure "pytest could not be started: $($_.Exception.Message)"
}

Write-Host "pytest exit code: $pytestExitCode"
if ($pytestStarted -and $pytestExitCode -ne 0) {
    Write-Host "pytest failed; the original pytest output and traceback are preserved above."
    $script:readonlyPipelineFailure = $true
}

$resultValidationFailed = $false
if (Test-Path -LiteralPath $junitPath -PathType Leaf) {
    Write-Host "JUnit XML report: $junitPath"
}
else {
    Report-ReadonlyFailure "JUnit XML report was not generated: $junitPath"
    $resultValidationFailed = $true
}

$allureFiles = @(Get-ChildItem -LiteralPath $allureResultsDirectory -File -ErrorAction SilentlyContinue)
if ($allureFiles.Count -gt 0) {
    Write-Host "Allure raw results directory: $allureResultsDirectory"
}
else {
    Report-ReadonlyFailure "Allure raw results were not generated: $allureResultsDirectory"
    $resultValidationFailed = $true
}

$junitXml = $null
$junitTestCount = $null
$junitStats = @{}
if (-not (Test-Path -LiteralPath $junitPath -PathType Leaf)) {
    $resultValidationFailed = $true
}
else {
    try {
        $junitXml = [xml](Get-Content -LiteralPath $junitPath -Raw)
        $junitRoot = $junitXml.testsuites
        if ($null -eq $junitRoot) {
            throw "JUnit XML does not contain a testsuites root element."
        }

        $statNames = @("tests", "failures", "errors", "skipped")
        $statsNodes = @()
        if ($junitRoot.HasAttribute("tests")) {
            $statsNodes = @($junitRoot)
        }
        else {
            $statsNodes = @($junitRoot.SelectNodes("./testsuite"))
            if ($statsNodes.Count -eq 0) {
                throw "JUnit XML has no root tests attribute or direct testsuite nodes."
            }
        }

        foreach ($statsNode in $statsNodes) {
            foreach ($statName in $statNames) {
                $statAttribute = $statsNode.GetAttribute($statName)
                if ($statName -eq "tests" -and [string]::IsNullOrWhiteSpace($statAttribute)) {
                    throw "JUnit XML testsuite tests attribute must be a non-negative integer."
                }
                if (-not [string]::IsNullOrWhiteSpace($statAttribute)) {
                    if ($statAttribute -notmatch '^\d+$') {
                        throw "JUnit XML $statName attribute must be a non-negative integer."
                    }
                    $value = [int]$statAttribute
                }
                else {
                    $value = 0
                }
                if (-not $junitStats.ContainsKey($statName)) {
                    $junitStats[$statName] = 0
                }
                $junitStats[$statName] += $value
            }
        }

        $junitTestCount = $junitStats["tests"]
        $testCases = @($junitRoot.SelectNodes(".//testcase"))
        if ($junitTestCount -gt 0 -and $testCases.Count -eq 0) {
            throw "JUnit XML reports tests but contains no testcase nodes."
        }
        if (($junitStats["failures"] + $junitStats["errors"] + $junitStats["skipped"]) -gt $junitTestCount) {
            throw "JUnit XML outcome counts exceed the tests count."
        }
    }
    catch {
        Report-ReadonlyFailure "JUnit XML is invalid: $($_.Exception.Message)"
        $resultValidationFailed = $true
    }
}
if ($null -ne $junitTestCount -and $junitTestCount -eq 0) {
    Report-ReadonlyFailure "JUnit XML is structurally valid but contains zero tests; this regression requires executed tests."
    $resultValidationFailed = $true
}

$allureResultFiles = @(
    Get-ChildItem -LiteralPath $allureResultsDirectory -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -like "*-result.json" -or $_.Name -like "*-container.json" }
)
if ($allureResultFiles.Count -eq 0) {
    Report-ReadonlyFailure "Allure raw results contain no result or container JSON files: $allureResultsDirectory"
    $resultValidationFailed = $true
}
else {
    $validAllureStatuses = @("passed", "failed", "broken", "skipped", "unknown")
    foreach ($resultFile in $allureResultFiles) {
        try {
            $rawResult = Get-Content -LiteralPath $resultFile.FullName -Raw
            if ([string]::IsNullOrWhiteSpace($rawResult)) {
                throw "file is empty"
            }
            $parsedResult = $rawResult | ConvertFrom-Json
            if ($null -eq $parsedResult -or [string]::IsNullOrWhiteSpace([string]$parsedResult.uuid)) {
                throw "missing required uuid"
            }
            if ($resultFile.Name -like "*-result.json") {
                if ([string]::IsNullOrWhiteSpace([string]$parsedResult.name)) {
                    throw "result file is missing required name"
                }
                if ([string]::IsNullOrWhiteSpace([string]$parsedResult.status) -or
                    $validAllureStatuses -notcontains ([string]$parsedResult.status).ToLowerInvariant()) {
                    throw "result file has an unsupported status"
                }
            }
            if ($resultFile.Name -like "*-container.json") {
                if (-not ($parsedResult.PSObject.Properties.Name -contains "children")) {
                    throw "container file is missing required children"
                }
                $children = @($parsedResult.children)
                foreach ($child in $children) {
                    if ($child -isnot [string] -or [string]::IsNullOrWhiteSpace($child)) {
                        throw "container children must be non-empty UUID strings"
                    }
                }
            }
        }
        catch {
            Report-ReadonlyFailure "Invalid Allure result JSON '$($resultFile.Name)': $($_.Exception.Message)"
            $resultValidationFailed = $true
        }
    }
}

if ($null -ne $junitTestCount) {
    $totalTests = $junitStats["tests"]
    $failedTests = $junitStats["failures"]
    $errorTests = $junitStats["errors"]
    $skippedTests = $junitStats["skipped"]
    $passedTests = $totalTests - $failedTests - $errorTests - $skippedTests
    Write-Host "Test summary: total=$totalTests passed=$passedTests failed=$failedTests errors=$errorTests skipped=$skippedTests"
}

if ($resultValidationFailed) {
    Report-ReadonlyFailure "Test result validation failed; Allure HTML generation was skipped."
    $script:readonlyPipelineFailure = $true
    if ($pytestExitCode -ne 0) {
        exit $pytestExitCode
    }
    exit 1
}

$allureCli = Join-Path $projectRoot "tools\allure\allure-2.46.1\bin\allure.bat"
if (-not (Test-Path -LiteralPath $allureCli -PathType Leaf)) {
    Report-ReadonlyFailure "Allure CLI was not found: $allureCli"
    if ($pytestExitCode -ne 0) {
        exit $pytestExitCode
    }
    exit 1
}

$allureGenerateExitCode = 1
$allureGenerateStarted = $false
try {
    & $allureCli generate $allureResultsDirectory --output $reportDirectory
    $allureGenerateStarted = $true
    $allureGenerateExitCode = $LASTEXITCODE
}
catch {
    Report-ReadonlyFailure "Allure HTML generation could not be started: $($_.Exception.Message)"
}

if (-not $allureGenerateStarted -or $allureGenerateExitCode -ne 0) {
    Report-ReadonlyFailure "Allure HTML generation failed with exit code $allureGenerateExitCode."
    if ($pytestExitCode -ne 0) {
        exit $pytestExitCode
    }
    exit 1
}

$indexPath = Join-Path $reportDirectory "index.html"
if (-not (Test-Path -LiteralPath $indexPath -PathType Leaf)) {
    Report-ReadonlyFailure "Allure HTML report index.html was not generated: $indexPath"
    if ($pytestExitCode -ne 0) {
        exit $pytestExitCode
    }
    exit 1
}
Write-Host "Allure HTML report: $reportDirectory"

$allureOpenProcess = $null
$allureOpenStarted = $false
$allureServiceReachable = $false
$allureOpenLog = Join-Path ([IO.Path]::GetTempPath()) "mkty-allure-open-$([guid]::NewGuid().ToString('N')).out.log"
$allureOpenErrorLog = Join-Path ([IO.Path]::GetTempPath()) "mkty-allure-open-$([guid]::NewGuid().ToString('N')).err.log"
try {
    $allureOpenProcess = Start-Process `
        -FilePath $allureCli `
        -ArgumentList @("open", $reportDirectory) `
        -RedirectStandardOutput $allureOpenLog `
        -RedirectStandardError $allureOpenErrorLog `
        -PassThru
    $allureOpenStarted = $true
}
catch {
    Report-ReadonlyFailure "Allure report service could not be started: $($_.Exception.Message)"
}

if (-not $allureOpenStarted) {
    if ($pytestExitCode -ne 0) {
        exit $pytestExitCode
    }
    exit 1
}

$serverUrl = $null
$startupDeadline = (Get-Date).AddSeconds(15)
$allureLogReadFailed = $false
$allureLogReadError = $null
$allureUrlParseError = $null
while ((Get-Date) -lt $startupDeadline -and -not $allureServiceReachable) {
    $allureOpenProcess.Refresh()
    if ($allureOpenProcess.HasExited -and $allureOpenProcess.ExitCode -ne 0) {
        Report-ReadonlyFailure "Allure report service exited during startup with code $($allureOpenProcess.ExitCode)."
        break
    }

    foreach ($logPath in @($allureOpenLog, $allureOpenErrorLog)) {
        if ($null -eq $serverUrl -and (Test-Path -LiteralPath $logPath -PathType Leaf)) {
            try {
                $logText = Get-Content -LiteralPath $logPath -Raw -ErrorAction Stop
                if ([string]::IsNullOrWhiteSpace($logText)) {
                    continue
                }
                $urlMatch = [regex]::Match($logText, 'https?://[^\s"''<>]+')
            }
            catch {
                $allureLogReadFailed = $true
                $allureLogReadError = $_.Exception.Message
                continue
            }
            if ($urlMatch.Success) {
                $candidateUrl = $urlMatch.Value.TrimEnd('.', ',', ';', ':', ')', ']', '}', '>', '"', '''')
                if ([string]::IsNullOrWhiteSpace($candidateUrl)) {
                    $allureUrlParseError = "Allure service startup log contained an empty URL candidate."
                    continue
                }
                $parsedUri = $null
                if (-not [Uri]::TryCreate($candidateUrl, [UriKind]::Absolute, [ref]$parsedUri)) {
                    $allureUrlParseError = "Allure service URL in startup log could not be parsed: $candidateUrl"
                }
                else {
                    $normalizedHost = $parsedUri.Host.Trim('[', ']').ToLowerInvariant()
                    $allowedLoopbackHosts = @("localhost", "127.0.0.1", "::1")
                    if ($parsedUri.Scheme -notin @("http", "https") -or
                        $parsedUri.UserInfo -or
                        $allowedLoopbackHosts -notcontains $normalizedHost -or
                        $parsedUri.Port -le 0) {
                        $allureUrlParseError = "Allure service URL is not an allowed local loopback URL: $candidateUrl"
                    }
                    else {
                        $serverUrl = $parsedUri.AbsoluteUri.TrimEnd('/')
                    }
                }
            }
        }
    }

    if ($null -ne $serverUrl) {
        try {
            $serverResponse = Invoke-WebRequest -Uri $serverUrl -Method Get -TimeoutSec 2 -UseBasicParsing
            if ($serverResponse.StatusCode -eq 200) {
                $allureServiceReachable = $true
            }
        }
        catch {
            # The service may still be binding its dynamically selected port.
        }
    }

    if (-not $allureServiceReachable) {
        Start-Sleep -Milliseconds 500
    }
}

if (-not $allureServiceReachable) {
    if ($null -ne $allureUrlParseError) {
        Report-ReadonlyFailure $allureUrlParseError
    }
    elseif ($allureLogReadFailed) {
        Report-ReadonlyFailure "Allure report service logs could not be read or parsed during startup: $allureLogReadError"
    }
    else {
        Report-ReadonlyFailure "Allure report service was not confirmed reachable within the startup window."
    }
    if ($pytestExitCode -ne 0) {
        exit $pytestExitCode
    }
    exit 1
}
Write-Host "Allure report service is reachable at $serverUrl; existing Allure services were not terminated."

if ($pytestExitCode -ne 0) {
    exit $pytestExitCode
}
if ($script:readonlyPipelineFailure) {
    exit 1
}
exit 0
