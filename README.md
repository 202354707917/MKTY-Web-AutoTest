# MKTY Web UI 自动化测试

本项目是独立的 Web UI 自动化测试工程，用于测试本地运行的慧医通患者端页面。项目不修改被测业务项目，也不包含真实账号、密码或业务数据。

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
│   └── patient_booking_page.py       # 排班选择和受保护的预约提交
├── tests/
│   ├── smoke/
│   │   └── test_patient_entry.py     # 患者入口只读冒烟测试
│   └── ui/
│       ├── test_patient_login.py         # 患者登录成功页面检查
│       ├── test_patient_appointments.py  # 预约页面和列表只读检查
│       ├── test_patient_doctor_search.py # 医生查询只读检查
│       ├── test_patient_doctor_detail.py # 医生详情只读检查
│       ├── test_patient_booking.py       # 受保护的预约写操作
│       └── test_booking_flow.py          # 预约创建后列表验证
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

运行全部测试：

```powershell
python -m pytest
```

只运行冒烟测试：

```powershell
python -m pytest -m smoke
```

只运行 UI 测试：

```powershell
python -m pytest -m ui
```

只运行只读 UI 回归：

```powershell
python -m pytest -m "ui and readonly"
```

只运行写操作测试：

```powershell
python -m pytest -m write
```

运行完整业务回归：

```powershell
python -m pytest -m regression
```

`smoke`、`ui`、`regression`、`write` 和 `readonly` 都已在 `pytest.ini` 中注册。冒烟测试同时带有 `smoke`、`ui`、`readonly` 和 `regression` 标记。只读 UI 测试带有 `ui`、`readonly` 和 `regression` 标记；两个预约写操作测试带有 `ui`、`write` 和 `regression` 标记。

pytest 默认参数包含 `-m "not write"`，因此普通的 `python -m pytest` 不会执行写操作测试。显式使用 `-m write` 或 `-m regression` 时会按命令选择测试；开启写操作前仍必须设置 `MKTY_ENABLE_WRITE_TEST=true`。

## CI 自动化执行

项目使用 GitHub Actions，配置文件为 `.github/workflows/ui-test.yml`。工作流会在推送、Pull Request 或手动触发时运行，使用 Ubuntu、Python 3.11 和稳定版 Chrome。

CI 默认将 `MKTY_ENABLE_WRITE_TEST` 设置为 `false`，只执行 `ui and readonly` 测试，不执行预约创建等写操作。登录所需的 `MKTY_UI_TEST_USERNAME` 和 `MKTY_UI_TEST_PASSWORD` 通过 GitHub Actions Secrets 注入，不写入仓库文件或日志。

每次 CI 执行都会将 Allure 原始结果写入 `artifacts/allure-results`，并上传为名为 `allure-results` 的构建产物。工作流不生成或发布 HTML 报告，也不启动 Allure Server。

## Allure 结果和报告

为避免混淆历史结果，建议每次执行都创建新的结果目录和报告目录：

```powershell
$runId = Get-Date -Format "yyyyMMdd_HHmmss"
$resultDir = ".\artifacts\allure-results-$runId"
$reportDir = ".\artifacts\allure-report-$runId"
python -m pytest -m ui --alluredir=$resultDir
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

将 `<runId>` 替换为命令输出中实际生成的时间戳目录，在 Windows 文件资源管理器中进入该目录并双击 `index.html`。本项目使用静态文件报告，不需要启动 Allure 报告服务器。

每次重新执行测试后，都应使用新的结果目录重新生成报告，不能把旧报告当作最新测试结果。

## 测试凭据

登录和预约 UI 测试从当前 PowerShell 进程环境变量读取专用测试账号：

```powershell
$env:MKTY_UI_TEST_USERNAME = Read-Host "UI test username"
$securePassword = Read-Host "UI test password" -AsSecureString
$env:MKTY_UI_TEST_PASSWORD = [System.Net.NetworkCredential]::new("", $securePassword).Password
```

这些变量只在当前 PowerShell 会话及其启动的测试进程中有效。关闭窗口后需要重新设置；不要使用 `setx` 持久化账号密码，也不要把值写入源码、日志、测试数据或 Allure 附件。测试结束后可清除当前会话中的变量：

```powershell
Remove-Item Env:MKTY_UI_TEST_USERNAME, Env:MKTY_UI_TEST_PASSWORD -ErrorAction SilentlyContinue
```

## 失败截图和 Allure 附件

当测试调用阶段或测试前置阶段失败，且 Chrome 已成功启动时，fixture 会尝试：

1. 将 PNG 截图保存到 `artifacts\screenshots`；
2. 将同一截图以 `image/png` 类型附加到当前 Allure 测试的 fixture teardown 结果。

截图或附件操作失败只记录日志，不应覆盖原始测试失败原因。浏览器结束时会执行 `driver.quit()` 清理。通过测试不会生成失败截图。

## 当前范围和未实现内容

当前已完成并曾实际验证：未登录患者入口冒烟、患者登录成功后的患者中心检查、患者预约页面基础检查，以及预约列表的只读状态检查。

预约创建闭环已实现为受保护的写操作测试，但默认不会执行；取消预约、修改患者信息等其他有副作用流程尚未实现。运行写操作前，需要先核实测试环境、测试账号来源、数据准备方式和清理策略。

## 安全注意事项

- 不要在源码、测试数据或提交记录中硬编码账号密码。
- 账号和密码应通过受控的运行时凭据注入，并避免写入日志或 Allure 附件。
- 新增预约、取消预约等有副作用的测试前，应先明确隔离的测试环境、数据准备方式和清理策略。
- 保持测试只读时，不输入账号密码、不提交表单、不修改业务数据。
