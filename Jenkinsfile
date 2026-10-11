pipeline {
    agent { label 'windows' }

    options {
        timestamps()
        skipDefaultCheckout(false)
    }

    parameters {
        string(
            name: 'PATIENT_CREDENTIALS_ID',
            defaultValue: 'mkty-patient',
            description: 'Jenkins Username/password credential ID for the patient test account.'
        )
        string(
            name: 'DOCTOR_CREDENTIALS_ID',
            defaultValue: 'mkty-doctor',
            description: 'Jenkins Username/password credential ID for the doctor test account.'
        )
    }

    stages {
        stage('Prepare Python environment') {
            steps {
                script {
                    if (!env.WORKSPACE) {
                        error('Jenkins WORKSPACE is not available.')
                    }

                    def pythonPath = "${env.WORKSPACE}\\.venv\\Scripts\\python.exe"
                    if (!fileExists(pythonPath)) {
                        powershell(
                            label: 'Create project virtual environment',
                            script: '''
$ErrorActionPreference = 'Stop'
$venvPython = Join-Path $env:WORKSPACE '.venv\\Scripts\\python.exe'
if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
    $systemPython = Get-Command python -CommandType Application -ErrorAction SilentlyContinue
    if ($null -eq $systemPython) {
        throw 'Python was not found on the Jenkins Windows agent; install Python 3.11+ first.'
    }
    & $systemPython.Source -m venv (Join-Path $env:WORKSPACE '.venv')
    $venvExitCode = [int]$LASTEXITCODE
    if ($venvExitCode -ne 0) {
        exit $venvExitCode
    }
    & $venvPython -m pip install -r (Join-Path $env:WORKSPACE 'requirements.txt')
    $pipExitCode = [int]$LASTEXITCODE
    if ($pipExitCode -ne 0) {
        exit $pipExitCode
    }
}
'''
                        )
                    } else {
                        echo 'Reusing existing project virtual environment.'
                    }

                    if (!fileExists("${env.WORKSPACE}\\scripts\\run_readonly_regression.ps1")) {
                        error('scripts/run_readonly_regression.ps1 was not found in the workspace.')
                    }
                }
            }
        }

        stage('Run read-only regression') {
            steps {
                script {
                    env.READONLY_RUN_STARTED_UTC = powershell(
                        returnStdout: true,
                        script: "[DateTime]::UtcNow.ToString('o')"
                    ).trim()
                    withCredentials([
                        usernamePassword(
                            credentialsId: params.PATIENT_CREDENTIALS_ID,
                            usernameVariable: 'MKTY_UI_TEST_USERNAME',
                            passwordVariable: 'MKTY_UI_TEST_PASSWORD'
                        ),
                        usernamePassword(
                            credentialsId: params.DOCTOR_CREDENTIALS_ID,
                            usernameVariable: 'MKTY_DOCTOR_USERNAME',
                            passwordVariable: 'MKTY_DOCTOR_PASSWORD'
                        )
                    ]) {
                        powershell(
                            label: 'Run unified read-only regression',
                            script: '''
$ErrorActionPreference = 'Stop'
$scriptPath = Join-Path $env:WORKSPACE 'scripts\\run_readonly_regression.ps1'
& $scriptPath
'''
                        )
                    }
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts(
                artifacts: 'artifacts/**',
                allowEmptyArchive: true,
                fingerprint: false
            )

            script {
                def latestJunitPath = powershell(
                    returnStdout: true,
                    script: '''
$startText = $env:READONLY_RUN_STARTED_UTC
if ([string]::IsNullOrWhiteSpace($startText)) { exit 0 }
$start = $null
if (-not [DateTime]::TryParse($startText, [ref]$start)) { exit 0 }
$start = $start.ToUniversalTime()
$dir = Get-ChildItem -LiteralPath (Join-Path $env:WORKSPACE 'artifacts') -Directory -Filter 'junit-readonly-regression-*' -ErrorAction SilentlyContinue |
    Where-Object { $_.LastWriteTimeUtc -ge $start } |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
if ($null -ne $dir) {
    $file = Join-Path $dir.FullName 'junit.xml'
    if (Test-Path -LiteralPath $file -PathType Leaf) {
        Write-Output ("artifacts/{0}/junit.xml" -f $dir.Name)
    }
}
'''
                ).trim()
                if ([string]::IsNullOrWhiteSpace(latestJunitPath)) {
                    echo 'No current read-only JUnit XML report was found; archived artifacts remain available.'
                } else {
                    junit(
                        testResults: latestJunitPath,
                        allowEmptyResults: true,
                        skipPublishingChecks: true
                    )
                }

                def latestAllurePath = powershell(
                    returnStdout: true,
                    script: '''
$startText = $env:READONLY_RUN_STARTED_UTC
if ([string]::IsNullOrWhiteSpace($startText)) { exit 0 }
$start = $null
if (-not [DateTime]::TryParse($startText, [ref]$start)) { exit 0 }
$start = $start.ToUniversalTime()
$dir = Get-ChildItem -LiteralPath (Join-Path $env:WORKSPACE 'artifacts') -Directory -Filter 'allure-results-readonly-regression-*' -ErrorAction SilentlyContinue |
    Where-Object { $_.LastWriteTimeUtc -ge $start } |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
if ($null -ne $dir) {
    Write-Output ("artifacts/{0}" -f $dir.Name)
}
'''
                ).trim()
                if ([string]::IsNullOrWhiteSpace(latestAllurePath)) {
                    echo 'No read-only Allure raw-results directory was found; archived artifacts remain available.'
                } else {
                    try {
                        // The Allure Jenkins plugin is optional. Keep artifact archival independent of it.
                        allure([
                            includeProperties: false,
                            jdk: '',
                            results: [[path: latestAllurePath]]
                        ])
                    } catch (Throwable pluginError) {
                        echo "Allure Jenkins plugin is unavailable or failed: ${pluginError.message}"
                        echo 'Install/configure the Allure Jenkins plugin to publish the archived raw results in Jenkins.'
                    }
                }
            }
        }
    }
}
