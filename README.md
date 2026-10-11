# MKTY Web UI 自动化测试

本项目是独立的 Selenium Web UI 自动化测试工程，用于验证本地运行的 Hospital-main 患者端和医生端页面。测试通过 Page Object Model 组织页面操作，使用显式等待处理 React 页面，并将只读回归与写操作分开。项目不修改被测业务项目，也不包含真实账号、密码、Token、Cookie 或业务数据。

被测前端默认地址为 `http://localhost:8088`。本仓库只负责测试，不负责启动 Hospital-main；业务前后端、数据库和测试数据需要按 Hospital-main 自身文档准备。

## 项目亮点

- 患者端和医生端使用独立的登录凭据环境变量。
- 患者只读测试共享 session 级浏览器登录状态，减少重复登录。
- Chrome 使用临时隔离 profile，并配置密码管理弹窗禁用参数。
- 页面对象使用显式等待和动态定位，避免长期持有 React 动态元素。
- pytest marker 区分 `smoke`、`ui`、`readonly`、`regression` 和 `write`。
- 预约创建、预约闭环和取消预约测试默认排除，只有显式开启写操作开关才会执行。
- 统一 PowerShell 入口生成独立 JUnit XML、Allure 原始结果和 HTML 报告，并检查报告服务 HTTP 可达性。

## 技术栈

- Python 3.11
- pytest 8.4.2
- Selenium 4.38.0
- Chrome WebDriver（优先使用 Selenium Manager）
- Allure Pytest 2.15.0
- Allure Report CLI 2.46.1

当前浏览器 fixture 使用 Chrome。Edge 和其他浏览器尚未实现。

## 目录结构

```text
.
├── conftest.py                       # Chrome fixture、显式清理、失败截图和 Allure 附件
├── pytest.ini                        # pytest 测试发现、marker 和日志配置
├── requirements.txt                  # Python 依赖及固定版本
├── pages/
│   ├── base_page.py                  # 通用显式等待和基础页面操作
│   ├── patient_entry_page.py         # 患者入口页面和登录跳转等待
│   ├── login_page.py                 # 登录页定位器、输入和提交操作
│   ├── patient_appointments_page.py  # 患者预约页面和列表状态检查
│   ├── patient_doctor_page.py        # 医生查询页面和医生详情链接
│   ├── patient_doctor_detail_page.py # 医生详情只读检查
│   ├── patient_booking_page.py       # 排班选择和受保护的预约提交
│   ├── patient_department_page.py    # 科室列表和医生筛选入口
│   ├── patient_medical_record_page.py # 病历列表和详情入口
│   ├── patient_profile_page.py       # 患者个人中心
│   ├── doctor_dashboard_page.py      # 医生工作台
│   ├── doctor_appointments_page.py   # 医生预约列表和状态筛选
│   └── doctor_appointment_detail_page.py # 医生预约详情
├── tests/
│   ├── smoke/
│   │   └── test_patient_entry.py     # 患者入口只读冒烟测试
│   └── ui/
│       ├── test_patient_login.py         # 患者登录成功页面检查
│       ├── test_patient_appointments.py  # 预约页面和列表只读检查
│       ├── test_patient_doctor_*.py      # 医生、科室和筛选只读检查
│       ├── test_patient_medical_*.py     # 病历列表和详情只读检查
│       ├── test_patient_profile.py       # 个人中心只读检查
│       ├── test_doctor_*.py              # 医生工作台和预约只读检查
│       └── test_*booking.py/test_appointment_cancel.py # 受保护写测试
├── artifacts/
│   └── screenshots/                  # 测试失败时保存的 PNG 截图
├── allure-results/                   # pytest 生成的 Allure 原始结果
├── allure-report/                    # Allure CLI 生成的静态 HTML 报告
├── tools/allure/allure-2.46.1/       # 可选的项目内 Allure CLI
├── .venv/                            # 项目独立 Python 虚拟环境
└── .selenium-cache/                  # Selenium Manager 的项目内缓存
```

`.pytest_cache` 和 `__pycache__` 是测试或语法检查产生的运行缓存。`allure-results`、`allure-report` 和截图目录都是运行产物，不是测试源码。

## 环境要求

需要安装并可用的环境包括：

- Python 3.11，并使用项目根目录下的 `.venv`；
- 已安装的 Chrome 浏览器；
- Java，用于运行 Allure CLI；
- Allure CLI 2.46.1：项目内工具、`MKTY_ALLURE_CLI` 或 PATH 中的外部安装版本三者之一。

在 PowerShell 中进入项目目录后激活虚拟环境：

```powershell
.\.venv\Scripts\Activate.ps1
```

也可以始终直接调用 `.venv\Scripts\python.exe`，避免误用系统 Python。

### Allure CLI 安装

Allure CLI 不包含在 `allure-pytest` Python 依赖中。新电脑建议从 Allure 官方发布渠道获取固定版本 2.46.1：

<https://github.com/allure-framework/allure2/releases>

需要先确认 Java 可用：

```powershell
java -version
```

示例安装目录为：

```text
%LOCALAPPDATA%\Allure\2.46.1
```

在 PowerShell 中检查外部 CLI：

```powershell
$allureCli = Join-Path $env:LOCALAPPDATA "Allure\2.46.1\bin\allure.bat"
& $allureCli --version
```

如果 CLI 不在 PATH 中，可以在当前 PowerShell 会话中指定完整路径：

```powershell
$env:MKTY_ALLURE_CLI = Join-Path $env:LOCALAPPDATA "Allure\2.46.1\bin\allure.bat"
& $env:MKTY_ALLURE_CLI --version
```

`scripts\run_readonly_regression.ps1` 的查找顺序是：项目内 `tools\allure\allure-2.46.1\bin\allure.bat`、`MKTY_ALLURE_CLI`、PATH 中的 `allure.bat` 或 `allure`。找到后必须通过 `--version` 验证为 2.46.1；显式设置的 `MKTY_ALLURE_CLI` 路径无效时不会静默切换到其他版本。

本项目尚未下载或核验官方发布包的 SHA-256，哈希值待实际获取发布包后再记录。

## 统一运行入口

以下命令均应在项目根目录的 PowerShell 中执行，并使用已激活的 `.venv`。

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

只运行写操作测试：

```powershell
$env:MKTY_ENABLE_WRITE_TEST = "true"
.\.venv\Scripts\python.exe -m pytest -m write
```

运行完整业务回归：

```powershell
.\.venv\Scripts\python.exe -m pytest -m regression
```

`smoke`、`ui`、`regression`、`write` 和 `readonly` 都已在 `pytest.ini` 中注册。冒烟测试同时带有 `smoke`、`ui`、`readonly` 和 `regression` 标记。只读 UI 测试带有 `ui`、`readonly` 和 `regression` 标记；两个预约写操作测试带有 `ui`、`write` 和 `regression` 标记。

pytest 默认参数包含 `-m "not write"`，因此普通的 `python -m pytest` 不会执行写操作测试。显式使用 `-m write` 或 `-m regression` 时会按命令选择测试；开启写操作前仍必须设置 `MKTY_ENABLE_WRITE_TEST=true`。

统一只读回归入口会额外检查 Python、四个账号变量和前端 HTTP 200，并只选择 `ui and readonly and not write`：

```powershell
.\scripts\run_readonly_regression.ps1
```

只运行医生端三个只读文件：

```powershell
.\scripts\run_doctor_readonly.ps1
```

代码中已有 16 个 `test_*.py` 模块，实际收集数量和跳过数量以本次 pytest 输出为准；本 README 不固定历史通过数。

## 当前测试范围

患者端只读覆盖：

- 未登录患者入口和患者登录后的患者中心。
- 我的预约页面与预约列表只读状态。
- 查询医生、医生详情、找科室和按科室筛选医生。
- 我的病历列表、病历详情和个人中心。

医生端只读覆盖：

- 医生工作台。
- 医生预约列表、已完成/待接诊状态筛选和预约详情字段。

受保护的写操作覆盖：

- 创建预约后验证我的预约。
- 取消一条待取消预约。

预约、病历、科室或医生详情数据为空时，相关只读测试可能按设计 `pytest.skip`。测试代码中的页面覆盖不等于每次环境都具备对应业务数据。

## CI 自动化执行

项目使用 GitHub Actions，配置文件为 `.github/workflows/ui-test.yml`。工作流会在推送、Pull Request 或手动触发时运行，使用 Ubuntu、Python 3.11 和稳定版 Chrome。

CI 默认将 `MKTY_ENABLE_WRITE_TEST` 设置为 `false`，只执行 `ui and readonly` 测试，不执行预约创建等写操作。登录所需的 `MKTY_UI_TEST_USERNAME` 和 `MKTY_UI_TEST_PASSWORD` 通过 GitHub Actions Secrets 注入，不写入仓库文件或日志。

每次 CI 执行都会将 Allure 原始结果写入 `artifacts/allure-results`，并上传为名为 `allure-results` 的构建产物。工作流不生成或发布 HTML 报告，也不启动 Allure Server。

## Allure 结果和报告

为避免混淆历史结果，建议每次执行都创建新的结果目录和报告目录：

```powershell
$runId = Get-Date -Format "yyyyMMdd_HHmmss"
$junitDir = ".\artifacts\junit-readonly-$runId"
$resultDir = ".\artifacts\allure-results-$runId"
$reportDir = ".\artifacts\allure-report-$runId"
.\.venv\Scripts\python.exe -m pytest -m "ui and readonly and not write" `
  --junitxml="$junitDir\junit.xml" --alluredir=$resultDir tests/ui
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
& $allureCli generate $resultDir --output $reportDir
```

需要生成全部测试的结果时，将上面命令中的 `-m ui` 删除；需要只生成冒烟结果时改为 `-m smoke`。当前 `pytest.ini` 没有默认配置 `--alluredir`，因此必须显式传入结果目录。

不要把新的结果写入已有的 `allure-results`，也不要把报告输出到已有的 `allure-report` 或历史报告目录。固定目录中的结果可能来自不同执行批次，固定报告目录也可能保留旧页面资源。

打开本次报告：

```text
项目目录\artifacts\allure-report-<runId>\index.html
```

将 `<runId>` 替换为命令输出中实际生成的时间戳目录，在 Windows 文件资源管理器中进入该目录并双击 `index.html`。手工生成的报告可以直接查看静态 HTML；统一入口还会使用 `allure open` 启动服务并检查 HTTP 200。

每次重新执行测试后，都应使用新的结果目录重新生成报告，不能把旧报告当作最新测试结果。

## 测试账号

登录 fixture 从当前 PowerShell 进程读取专用测试账号：

```text
MKTY_UI_TEST_USERNAME=<patient-test-username>
MKTY_UI_TEST_PASSWORD=<patient-test-password>
MKTY_DOCTOR_USERNAME=<doctor-test-username>
MKTY_DOCTOR_PASSWORD=<doctor-test-password>
```

不要把真实值写入 README、源码、`.env`、日志、测试数据或 Allure 附件。示例设置方式：

```powershell
$env:MKTY_UI_TEST_USERNAME = Read-Host "Patient test username"
$patientPassword = Read-Host "Patient test password" -AsSecureString
$env:MKTY_UI_TEST_PASSWORD = [System.Net.NetworkCredential]::new("", $patientPassword).Password

$env:MKTY_DOCTOR_USERNAME = Read-Host "Doctor test username"
$doctorPassword = Read-Host "Doctor test password" -AsSecureString
$env:MKTY_DOCTOR_PASSWORD = [System.Net.NetworkCredential]::new("", $doctorPassword).Password
```

变量只在当前 PowerShell 会话及其启动的测试进程中有效。可以只检查 `SET/MISSING` 而不显示值：

```powershell
foreach ($name in @(
    "MKTY_UI_TEST_USERNAME", "MKTY_UI_TEST_PASSWORD",
    "MKTY_DOCTOR_USERNAME", "MKTY_DOCTOR_PASSWORD"
)) {
    $value = [Environment]::GetEnvironmentVariable($name, "Process")
    if ([string]::IsNullOrWhiteSpace($value)) { "$name=MISSING" } else { "$name=SET" }
}
```

不要使用 `setx` 保存密码。测试结束后可清除当前会话变量：

```powershell
Remove-Item Env:MKTY_UI_TEST_USERNAME, Env:MKTY_UI_TEST_PASSWORD -ErrorAction SilentlyContinue
Remove-Item Env:MKTY_DOCTOR_USERNAME, Env:MKTY_DOCTOR_PASSWORD -ErrorAction SilentlyContinue
```

## 失败截图和 Allure 附件

当测试调用阶段或测试前置阶段失败，且 Chrome 已成功启动时，fixture 会尝试：

1. 将 PNG 截图保存到 `artifacts\screenshots`；
2. 将同一截图以 `image/png` 类型附加到当前 Allure 测试的 fixture teardown 结果。

截图或附件操作失败只记录日志，不应覆盖原始测试失败原因。浏览器结束时会执行 `driver.quit()` 清理。通过测试不会生成失败截图。

## 当前范围和验证边界

当前源码包含患者端和医生端的只读 Page Object 与测试模块，以及受保护的预约写操作模块。历史开发过程中曾分别验证过登录、患者预约页面、预约列表和医生端只读流程；本 README 不把历史结果当作当前环境的通过保证。

实际测试数量、通过数、跳过数和数据相关跳过原因，应以每次 `pytest` 输出为准。没有预约、病历、科室或详情数据时，部分只读测试可能按设计 `skip`。

## 写操作安全限制

预约创建、创建后列表验证和取消预约测试带有 `write` marker，并依赖显式环境变量：

```powershell
$env:MKTY_ENABLE_WRITE_TEST = "true"
.\.venv\Scripts\python.exe -m pytest -m write -v
```

默认不要设置该变量。只有在隔离测试环境、专用测试账号、数据准备和清理策略都确认后，才允许执行。写测试可能创建或取消真实业务数据，项目不会自动清理这些数据。只读入口使用 `ui and readonly and not write`，不会执行写测试。

## 常见问题排查

### 前端不可访问

确认 Hospital-main 已启动，并检查：

```powershell
Invoke-WebRequest http://localhost:8088 -UseBasicParsing
```

本项目不启动业务前端或后端；启动方式需要以 Hospital-main 文档为准。

### 登录凭据缺失

确认当前 PowerShell 会话中的患者或医生变量已设置。项目脚本只显示 `SET/MISSING`，不会显示变量值。

### Chrome 密码泄露弹窗

`conftest.py` 为每个浏览器 fixture 创建临时 profile，并配置密码管理禁用参数。不要复用真实 Chrome 用户目录，也不要用自动点击弹窗来规避问题。

### Allure CLI 找不到或版本不符

确认 Java 可用，执行 `allure.bat --version`，并检查项目内路径、`MKTY_ALLURE_CLI` 或 PATH。统一脚本只接受 2.46.1。

### JUnit 或 Allure 结果缺失

保留本次生成的结果目录，检查 pytest 原始输出和退出码。不要将旧 `allure-results*` 目录合并到本次结果中，也不要删除历史产物来掩盖失败。

### 测试被跳过

查看具体 pytest 输出。预约、病历、科室或医生详情为空时，测试可能按设计跳过；这与页面加载失败需要区分。

## GitHub 项目展示

本项目适合展示以下测试工程实践：

- POM 分层和稳定定位器。
- 显式等待、React 动态 DOM 和 stale 风险处理。
- session 级登录复用和临时 Chrome profile 隔离。
- `readonly`/`write` 分层及写操作默认保护。
- JUnit、Allure 原始结果、HTML 报告和失败截图。
- GitHub Actions 只读 CI 流程。

面试演示时可以从 `pytest.ini`、`conftest.py`、`pages/`、`tests/ui/` 和 `scripts/run_readonly_regression.ps1` 依次说明测试选择、fixture 生命周期、页面封装、只读边界和报告产物。账号、运行结果和业务数据属于受控环境，不应提交到 GitHub。

## 安全注意事项

- 不要在源码、测试数据或提交记录中硬编码账号密码。
- 账号和密码应通过受控的运行时凭据注入，并避免写入日志或 Allure 附件。
- 新增预约、取消预约等有副作用的测试前，应先明确隔离的测试环境、数据准备方式和清理策略。
- 保持测试只读时，不输入账号密码、不提交表单、不修改业务数据。
