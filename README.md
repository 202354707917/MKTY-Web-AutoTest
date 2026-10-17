# MKTY Web UI 自动化测试

本项目是独立的 Selenium Web UI 自动化测试工程，用于验证本地运行的 Hospital-main 患者端和医生端页面。测试通过 Page Object Model（POM）组织页面操作，使用显式等待处理 React 页面，并将只读回归与写操作分开。项目只负责测试，不修改被测业务项目，也不包含真实账号、密码、Token、Cookie 或业务数据。

被测前端默认地址为 `http://localhost:8088`。本仓库不负责启动 Hospital-main；业务前后端、数据库和测试数据需要按 Hospital-main 自身文档准备。

## 项目亮点

- 患者端和医生端使用独立的登录凭据环境变量。
- 患者只读测试共享 session 级浏览器登录状态，减少重复登录。
- Chrome 使用临时隔离 profile，并配置密码管理弹窗禁用参数。
- 页面对象使用显式等待和动态定位，避免长期持有 React 动态元素。
- pytest marker 区分 `smoke`、`ui`、`readonly`、`regression` 和 `write`。
- 预约创建、预约闭环和取消预约测试默认排除，只有显式开启写操作开关才会执行。
- Python 统一只读回归入口负责检查运行环境、执行指定测试、验证 JUnit 与 Allure 原始结果，并生成独立 HTML 报告。
- Jenkins Pipeline 通过 Windows agent 调用项目虚拟环境中的 Python 入口，并归档 JUnit、Allure 原始结果和 HTML 报告。
- GitHub Actions 工作流可用于独立的只读 CI 流程；其实际行为以 `.github/workflows/ui-test.yml` 为准。

## 技术栈

- Python 3.11
- pytest 8.4.2
- Selenium 4.38.0
- Chrome WebDriver（优先使用 Selenium Manager）
- Allure Pytest 2.15.0
- Allure Report CLI 2.46.1
- Jenkins Pipeline、Windows `bat`、PowerShell（本地环境管理及手动排查）
- Git、GitHub Actions

当前浏览器 fixture 使用 Chrome。Edge 和其他浏览器尚未实现。

## 目录结构

```text
.
├── .agents/                         # 本地开发辅助 Skill（是否纳入版本控制按项目策略决定）
├── conftest.py                      # Chrome fixture、显式清理、失败截图和 Allure 附件
├── pytest.ini                       # pytest 测试发现、marker 和日志配置
├── requirements.txt                 # Python 依赖及固定版本
├── Jenkinsfile                      # Jenkins Windows Pipeline
├── scripts/
│   ├── run_readonly_regression.py   # Python 统一只读回归入口
│   └── run_readonly_regression.py   # 当前正式入口：Python 只读回归测试
├── pages/
│   ├── base_page.py
│   ├── patient_entry_page.py
│   ├── login_page.py
│   ├── patient_appointments_page.py
│   ├── patient_doctor_page.py
│   ├── patient_doctor_detail_page.py
│   ├── patient_booking_page.py
│   ├── patient_department_page.py
│   ├── patient_medical_record_page.py
│   ├── patient_profile_page.py
│   ├── doctor_dashboard_page.py
│   ├── doctor_appointments_page.py
│   └── doctor_appointment_detail_page.py
├── tests/
│   ├── smoke/
│   │   └── test_patient_entry.py
│   └── ui/
│       ├── test_patient_login.py
│       ├── test_patient_appointments.py
│       ├── test_patient_doctor_*.py
│       ├── test_patient_medical_*.py
│       ├── test_patient_profile.py
│       ├── test_doctor_*.py
│       └── test_*booking.py / test_appointment_cancel.py
├── artifacts/                       # 运行结果、报告和截图等产物
├── tools/allure/allure-2.46.1/      # 可选的项目内 Allure CLI（通常不提交）
├── .venv/                           # 项目虚拟环境（不提交）
└── .selenium-cache/                 # Selenium Manager 缓存（不提交）
```

`.pytest_cache`、`__pycache__` 和 `.selenium-cache` 是运行缓存。JUnit、Allure 原始结果、HTML 报告和失败截图都是运行产物，不是测试源码。实际目录和文件以仓库当前内容为准。

## 环境要求

需要准备：

- Python 3.11，并使用项目根目录下的 `.venv`。
- 已安装的 Chrome 浏览器。
- Java，用于运行 Allure CLI。
- Allure CLI 2.46.1：可使用 `MKTY_ALLURE_CLI` 指定的路径，或项目内 `tools/allure/allure-2.46.1/bin/allure.bat`。Python 统一入口的查找顺序和版本校验以脚本实现为准。
- 可访问的 Hospital-main 测试环境，默认前端地址为 `http://localhost:8088`。
- 患者端、医生端的专用测试账号；不要使用真实用户账号。

在 PowerShell 中进入项目目录并激活虚拟环境：

```powershell
Set-Location "D:\APPS\MKTY-Web-AutoTest"
.\.venv\Scripts\Activate.ps1
```

也可以始终直接调用 `.venv\Scripts\python.exe`，避免误用系统 Python。

安装依赖：

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
```

检查 Python 和 Java：

```powershell
.\.venv\Scripts\python.exe --version
java -version
```

## Allure CLI

Allure CLI 不包含在 `allure-pytest` Python 依赖中。需要 Java 和 Allure CLI 2.46.1。官方发布渠道：

<https://github.com/allure-framework/allure2/releases>

示例外部安装目录：

```text
%LOCALAPPDATA%\Allure\2.46.1
```

在 PowerShell 中检查外部 CLI：

```powershell
$allureCli = Join-Path $env:LOCALAPPDATA "Allure\2.46.1\bin\allure.bat"
& $allureCli --version
```

如果 CLI 不在默认路径中，可以在当前 PowerShell 会话中指定完整路径：

```powershell
$env:MKTY_ALLURE_CLI = Join-Path $env:LOCALAPPDATA "Allure\2.46.1\bin\allure.bat"
& $env:MKTY_ALLURE_CLI --version
```

项目内 CLI 路径为：

```text
tools\allure\allure-2.46.1\bin\allure.bat
```

统一 Python 入口为 `scripts\run_readonly_regression.py`。脚本会检查 Allure CLI 版本是否为 2.46.1；如果显式设置的 `MKTY_ALLURE_CLI` 路径无效或版本不匹配，应按脚本报错进行处理，不要静默切换到未知版本。项目内的 Allure CLI 发行目录通常不纳入 Git 跟踪。

## 测试账号与环境变量

登录 fixture 从当前进程环境中读取专用测试账号：

```text
MKTY_UI_TEST_USERNAME=<patient-test-username>
MKTY_UI_TEST_PASSWORD=<patient-test-password>
MKTY_DOCTOR_USERNAME=<doctor-test-username>
MKTY_DOCTOR_PASSWORD=<doctor-test-password>
```

不要把真实值写入 README、源码、`.env`、日志、测试数据或 Allure 附件。

在 PowerShell 中可以通过交互方式设置变量：

```powershell
$env:MKTY_UI_TEST_USERNAME = Read-Host "Patient test username"
$patientPassword = Read-Host "Patient test password" -AsSecureString
$env:MKTY_UI_TEST_PASSWORD = [System.Net.NetworkCredential]::new("", $patientPassword).Password

$env:MKTY_DOCTOR_USERNAME = Read-Host "Doctor test username"
$doctorPassword = Read-Host "Doctor test password" -AsSecureString
$env:MKTY_DOCTOR_PASSWORD = [System.Net.NetworkCredential]::new("", $doctorPassword).Password
```

只检查变量是否存在，不显示实际值：

```powershell
foreach ($name in @(
    "MKTY_UI_TEST_USERNAME", "MKTY_UI_TEST_PASSWORD",
    "MKTY_DOCTOR_USERNAME", "MKTY_DOCTOR_PASSWORD"
)) {
    $value = [Environment]::GetEnvironmentVariable($name, "Process")
    if ([string]::IsNullOrWhiteSpace($value)) {
        "$name=MISSING"
    } else {
        "$name=SET"
    }
}
```

这些变量只在当前 PowerShell 会话及其启动的进程中有效。不要使用 `setx` 保存密码。测试结束后可清除当前会话变量：

```powershell
Remove-Item Env:MKTY_UI_TEST_USERNAME, Env:MKTY_UI_TEST_PASSWORD -ErrorAction SilentlyContinue
Remove-Item Env:MKTY_DOCTOR_USERNAME, Env:MKTY_DOCTOR_PASSWORD -ErrorAction SilentlyContinue
```

Jenkins 中使用 Credentials 绑定账号密码，通过 `withCredentials` 将其注入构建步骤。GitHub Actions 则应通过仓库 Secrets 注入。不要将凭据写入 Jenkinsfile 或工作流文件。

## 统一只读回归入口

统一入口会检查 Python 环境、所需账号变量、前端可达性，并执行以下测试选择：

```text
ui and readonly and not write
```

在项目根目录运行：

```powershell
.\.venv\Scripts\python.exe .\scripts\run_readonly_regression.py
```

本地运行会执行只读回归并生成独立的 JUnit XML、Allure 原始结果和 HTML 报告；按脚本实现，成功后还可能启动本地 Allure 报告服务并检查 HTTP 可达性。

CI 调用方式：

```powershell
.\.venv\Scripts\python.exe .\scripts\run_readonly_regression.py --ci --report-run-id "<run-id>"
```

`--ci` 用于避免在 CI 中启动本地报告服务；`--report-run-id` 用于关联本次运行的结果目录。具体 ID 格式以 Python 脚本校验逻辑为准。不要自行复用历史运行 ID。

## 常用 pytest 命令

以下命令在项目根目录执行。

运行全部测试（默认排除 `write`）：

```powershell
.\.venv\Scripts\python.exe -m pytest
```

只运行冒烟测试：

```powershell
.\.venv\Scripts\python.exe -m pytest -m smoke
```

只运行 UI 测试：

```powershell
.\.venv\Scripts\python.exe -m pytest -m ui
```

只运行只读 UI 回归：

```powershell
.\.venv\Scripts\python.exe -m pytest -m "ui and readonly"
```

运行写操作测试：

```powershell
$env:MKTY_ENABLE_WRITE_TEST = "true"
.\.venv\Scripts\python.exe -m pytest -m write -v
```

运行完整业务回归：

```powershell
.\.venv\Scripts\python.exe -m pytest -m regression
```

`smoke`、`ui`、`regression`、`write` 和 `readonly` marker 应以 `pytest.ini` 的实际定义为准。普通 pytest 命令的默认 marker 过滤也由 `pytest.ini` 控制。显式使用 `-m write` 或包含写测试的选择条件前，应确认写操作保护逻辑和环境安全条件。

## 手动生成 JUnit 与 Allure 报告

如果需要单独排查 pytest 或 Allure，可以手动执行测试，再生成报告。每次运行都应使用新的目录，避免历史结果混入。

```powershell
$runId = Get-Date -Format "yyyyMMdd_HHmmss"
$junitDir = ".\artifacts\junit-readonly-$runId"
$resultDir = ".\artifacts\allure-results-$runId"
$reportDir = ".\artifacts\allure-report-$runId"

New-Item -ItemType Directory -Force -Path $junitDir, $resultDir | Out-Null

.\.venv\Scripts\python.exe -m pytest `
    -m "ui and readonly and not write" `
    --junitxml="$junitDir\junit.xml" `
    --alluredir="$resultDir" `
    tests/ui

if ($LASTEXITCODE -ne 0) {
    Write-Host "pytest exited with code $LASTEXITCODE"
}
```

生成 Allure HTML 报告时，使用已确认版本为 2.46.1 的 CLI：

```powershell
$projectAllureCli = ".\tools\allure\allure-2.46.1\bin\allure.bat"

if (Test-Path -LiteralPath $projectAllureCli -PathType Leaf) {
    $allureCli = (Resolve-Path -LiteralPath $projectAllureCli).Path
}
elseif (-not [string]::IsNullOrWhiteSpace($env:MKTY_ALLURE_CLI)) {
    if (-not (Test-Path -LiteralPath $env:MKTY_ALLURE_CLI -PathType Leaf)) {
        throw "MKTY_ALLURE_CLI must point to an existing allure.bat file."
    }
    $allureCli = (Resolve-Path -LiteralPath $env:MKTY_ALLURE_CLI).Path
}
else {
    $allureCommand = Get-Command allure.bat -CommandType Application -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($null -eq $allureCommand) {
        $allureCommand = Get-Command allure -CommandType Application -ErrorAction SilentlyContinue |
            Select-Object -First 1
    }
    if ($null -eq $allureCommand) {
        throw "Allure CLI 2.46.1 was not found."
    }
    $allureCli = $allureCommand.Path
    if ([string]::IsNullOrWhiteSpace($allureCli)) {
        $allureCli = $allureCommand.Source
    }
}

& $allureCli --version
if ($LASTEXITCODE -ne 0) {
    throw "Unable to check Allure CLI version."
}

& $allureCli generate $resultDir --output $reportDir
if ($LASTEXITCODE -ne 0) {
    throw "Allure HTML report generation failed."
}
```

上面的命令用于手动排查；统一入口的实际 CLI 查找逻辑以 `scripts\run_readonly_regression.py` 为准。报告生成后，检查 `index.html` 是否存在，再打开本次报告目录。不要把新结果写入已有结果目录，也不要将报告输出到历史报告目录。

## Jenkins 持续集成

项目的 `Jenkinsfile` 面向 Windows agent，使用项目虚拟环境中的 Python 运行统一只读回归脚本。

预期流程：

1. Jenkins 检出仓库。
2. 检查或准备项目 `.venv`，按 `requirements.txt` 安装依赖。
3. 从 Jenkins Credentials 注入患者端和医生端测试账号。
4. 调用 `scripts\run_readonly_regression.py --ci --report-run-id <run-id>`。
5. 在构建结束阶段归档本次 JUnit XML、Allure 原始结果和 HTML 报告。
6. 通过 Jenkins JUnit 测试结果发布步骤查看测试统计，并从构建产物中打开静态 Allure HTML 报告。

Jenkins 运行依赖 Windows agent、Python、Chrome、Java、可用的被测前端和 Allure CLI 2.46.1。Allure CLI 路径可通过 Jenkins 进程环境变量 `MKTY_ALLURE_CLI` 提供，也可以由脚本按其配置的回退逻辑查找。

本项目的 Pipeline 不依赖 Jenkins Allure 插件；报告作为构建产物归档。具体执行状态、测试数量和报告是否生成，应以对应 Jenkins 构建日志及产物为准。尚未成功运行的构建不得描述为已验证成功。

## GitHub Actions

如果仓库保留 `.github/workflows/ui-test.yml`，该工作流可作为独立的 GitHub Actions CI 流程。其触发条件、运行系统、依赖安装方式、测试筛选和产物上传行为，以工作流文件的实际内容为准。

工作流中使用的测试账号应存储在 GitHub Actions Secrets，不得写入仓库文件或日志。不要仅凭 README 描述推断工作流已经在当前版本成功执行。

## 测试范围

患者端只读覆盖：

- 未登录患者入口和患者登录后的患者中心。
- 我的预约页面与预约列表只读状态。
- 查询医生、医生详情、找科室和按科室筛选医生。
- 我的病历列表、病历详情和个人中心。

医生端只读覆盖：

- 医生工作台。
- 医生预约列表、状态筛选和预约详情字段。

受保护的写操作覆盖：

- 创建预约后验证我的预约。
- 取消一条待取消预约。

预约、病历、科室或医生详情数据为空时，相关只读测试可能按设计 `pytest.skip`。测试代码中的页面覆盖不代表每次环境都具备对应业务数据。实际测试数量、通过数、失败数、跳过数及原因，以本次 pytest 输出为准。

## 失败截图和 Allure 附件

当测试调用阶段或测试前置阶段失败，且 Chrome 已成功启动时，fixture 会尝试：

1. 将 PNG 截图保存到 `artifacts/screenshots`。
2. 将同一截图以 `image/png` 类型附加到当前 Allure 测试的 fixture teardown 结果。

截图或附件操作失败只记录日志，不应覆盖原始测试失败原因。浏览器结束时应执行 `driver.quit()` 清理。通过测试通常不会生成失败截图。

## 写操作安全限制

预约创建、创建后列表验证和取消预约测试属于有副作用的写操作。执行前必须确认：

- 使用隔离的测试环境和专用测试账号。
- 已准备测试数据并明确清理策略。
- 已了解测试可能创建或取消业务数据。
- 已确认 `MKTY_ENABLE_WRITE_TEST` 开关及 pytest marker 的实际保护逻辑。

示例：

```powershell
$env:MKTY_ENABLE_WRITE_TEST = "true"
.\.venv\Scripts\python.exe -m pytest -m write -v
```

默认不要设置该变量。只读统一入口使用 `ui and readonly and not write`，目的是排除带有 `write` marker 的测试。执行任何测试前，都应以当前源码中的 marker 和保护逻辑为准。

## 常见问题排查

### 前端不可访问

确认 Hospital-main 已启动，并检查：

```powershell
Invoke-WebRequest http://localhost:8088 -UseBasicParsing
```

本项目不启动业务前端或后端；启动方式以 Hospital-main 文档为准。

### 登录凭据缺失

检查当前 PowerShell 会话或 CI 凭据绑定中，患者端和医生端所需变量是否设置。项目脚本只应显示 `SET/MISSING`，不应输出变量值。

### Chrome 或 WebDriver 启动失败

确认 Chrome 已安装且可运行，并检查 Selenium Manager 的网络访问或驱动配置。不要将真实 Chrome 用户目录用于自动化测试；浏览器 fixture 应使用临时隔离 profile。

### Allure CLI 找不到或版本不符

确认 Java 可用，执行 `allure.bat --version`，并检查项目内路径、`MKTY_ALLURE_CLI` 或 PATH。统一 Python 入口要求 Allure CLI 2.46.1；CLI 的实际查找顺序以 Python 脚本为准。

### JUnit 或 Allure 结果缺失

保留本次生成的结果目录，检查 pytest 原始输出、退出码和脚本日志。不要将旧的 `allure-results` 目录合并到本次结果中，也不要删除历史产物来掩盖失败。

### 测试被跳过

查看具体 pytest 输出。预约、病历、科室或医生详情数据为空时，测试可能按设计跳过；这与页面加载失败需要区分。

## GitHub 项目展示

本项目适合展示以下测试工程实践：

- POM 分层和稳定定位器。
- 显式等待、React 动态 DOM 和 stale 风险处理。
- session 级登录复用和临时 Chrome profile 隔离。
- `readonly` / `write` 分层及写操作保护。
- Python 统一运行入口、JUnit、Allure 原始结果、HTML 报告和失败截图。
- Jenkins Windows Pipeline 与 GitHub Actions 的 CI 集成（以实际配置及执行记录为准）。

面试演示时可以从 `pytest.ini`、`conftest.py`、`pages/`、`tests/ui/`、`scripts/run_readonly_regression.py` 和 `Jenkinsfile` 依次说明测试选择、fixture 生命周期、页面封装、只读边界、报告产物和持续集成流程。

## 安全注意事项

- 不要在源码、测试数据或提交记录中硬编码账号密码。
- 账号和密码应通过受控的运行时凭据注入，并避免写入日志或 Allure 附件。
- 不要提交 `.venv/`、浏览器缓存、真实测试数据或包含敏感信息的运行产物。
- 新增预约、取消预约等有副作用的测试前，应先明确隔离的测试环境、数据准备方式和清理策略。
- 保持测试只读时，不输入账号密码、不提交表单、不修改业务数据。
