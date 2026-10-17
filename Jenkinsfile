pipeline {
    agent { label 'windows' }

    options {
        timestamps()
        skipDefaultCheckout(false)
    }

    environment {
        PYTHON_PATH = '.venv\\Scripts\\python.exe'
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
                        bat(
                            label: 'Create project virtual environment and install dependencies',
                            script: '''
@echo off
setlocal

where python >nul 2>nul
if errorlevel 1 (
    echo Python was not found on the Jenkins Windows agent.
    echo Install Python 3.11 or newer and ensure it is on PATH.
    endlocal & exit /b 1
)

python -m venv "%WORKSPACE%\\.venv"
if errorlevel 1 exit /b 1

"%WORKSPACE%\\.venv\\Scripts\\python.exe" -m pip install -r "%WORKSPACE%\\requirements.txt"
if errorlevel 1 exit /b 1

endlocal
'''
                        )
                    } else {
                        echo 'Reusing existing project virtual environment.'
                    }

                    if (!fileExists("${env.WORKSPACE}\\scripts\\run_readonly_regression.py")) {
                        error('scripts/run_readonly_regression.py was not found in the workspace.')
                    }

                    if (!fileExists("${env.WORKSPACE}\\requirements.txt")) {
                        error('requirements.txt was not found in the workspace.')
                    }
                }
            }
        }

        stage('Run read-only regression') {
            steps {
                script {
                    env.READONLY_REPORT_RUN_ID =
                        "${new Date().format('yyyyMMdd_HHmmss', TimeZone.getTimeZone('Asia/Shanghai'))}-${UUID.randomUUID().toString().replace('-', '')}"

                    if (!(env.READONLY_REPORT_RUN_ID ==~ /[0-9]{8}_[0-9]{6}-[a-f0-9]{32}/)) {
                        error('Invalid read-only report run ID.')
                    }

                    withCredentials([
                        usernamePassword(
                            credentialsId: 'mkty-patient',
                            usernameVariable: 'MKTY_UI_TEST_USERNAME',
                            passwordVariable: 'MKTY_UI_TEST_PASSWORD'
                        ),
                        usernamePassword(
                            credentialsId: 'mkty-doctor',
                            usernameVariable: 'MKTY_DOCTOR_USERNAME',
                            passwordVariable: 'MKTY_DOCTOR_PASSWORD'
                        )
                    ]) {
                        bat(
                            label: 'Run unified read-only regression',
                            script: '''
@echo off
setlocal

set "PYTHON=%WORKSPACE%\\.venv\\Scripts\\python.exe"

if not exist "%PYTHON%" (
    echo Project virtual-environment Python was not found.
    endlocal & exit /b 2
)

"%PYTHON%" "%WORKSPACE%\\scripts\\run_readonly_regression.py" --ci --report-run-id "%READONLY_REPORT_RUN_ID%"
set "REGRESSION_EXIT_CODE=%ERRORLEVEL%"

endlocal & exit /b %REGRESSION_EXIT_CODE%
'''
                        )
                    }
                }
            }
        }
    }

    post {
        always {
            script {
                def runId = env.READONLY_REPORT_RUN_ID

                if (!runId?.trim()) {
                    echo 'Regression did not start; no current report directories were allocated.'
                } else if (!(runId ==~ /[0-9]{8}_[0-9]{6}-[a-f0-9]{32}/)) {
                    currentBuild.result = 'FAILURE'
                    echo 'Invalid report run ID; refusing to select artifacts.'
                } else {
                    def junitDirectory = "artifacts/junit-readonly-regression-${runId}"
                    def allureDirectory = "artifacts/allure-results-readonly-regression-${runId}"
                    def htmlDirectory = "artifacts/allure-report-readonly-regression-${runId}"

                    try {
                        archiveArtifacts(
                            artifacts: "${junitDirectory}/**,${allureDirectory}/**,${htmlDirectory}/**",
                            allowEmptyArchive: true,
                            fingerprint: false
                        )
                    } catch (Exception archiveError) {
                        currentBuild.result = 'FAILURE'
                        echo "Report artifact archival failed: ${archiveError}"
                    }

                    def junitPath = "${junitDirectory}/junit.xml"

                    try {
                        if (fileExists(junitPath)) {
                            junit(
                                testResults: junitPath,
                                allowEmptyResults: false,
                                skipPublishingChecks: true
                            )
                        } else {
                            currentBuild.result = 'FAILURE'
                            echo 'No current read-only JUnit XML report was found.'
                        }
                    } catch (Exception junitError) {
                        currentBuild.result = 'FAILURE'
                        echo "JUnit report publication failed: ${junitError}"
                    }

                    if (fileExists("${htmlDirectory}/index.html")) {
                        echo "Allure HTML report archived: ${htmlDirectory}/index.html"
                        echo 'Open the Jenkins build page and use the archived artifacts to view the Allure report.'
                    } else {
                        currentBuild.result = 'FAILURE'
                        echo 'No current read-only Allure HTML report was found.'
                    }
                       try {
                        if (fileExists(allureDirectory)) {
                            allure(
                                includeProperties: false,
                                jdk: '',
                                results: [[path: allureDirectory]],
                                reportBuildPolicy: 'ALWAYS',
                                commandline: 'Allure-2.46.1'
                            )
                        } else {
                            currentBuild.result = 'FAILURE'
                            echo 'No current Allure results found; cannot publish the Allure report.'
                        }
                    } catch (Exception allureError) {
                        currentBuild.result = 'FAILURE'
                        echo "Allure report publication failed: ${allureError}"
                    }

                    if (fileExists(allureDirectory)) {
                        echo "Allure raw results archived: ${allureDirectory}"
                    } else {
                        currentBuild.result = 'FAILURE'
                        echo 'No current read-only Allure raw-results directory was found.'
                    }
                }
            }
        }
    }
}