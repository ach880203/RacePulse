# =============================================================================
# run_bulk_collect.ps1 — 일일 데이터 수집 자동화 스크립트
# Windows 작업 스케줄러에서 매일 새벽 3시에 실행됩니다.
# =============================================================================

$mlServerPath = "C:\Programmer\Work\horse racing\racepulse\ml-server"
$logFile = "C:\Programmer\Work\horse racing\racepulse\ml-server\scripts\collect_log.txt"
$pythonExe = "C:\Programmer\Work\horse racing\racepulse\ml-server\venv\Scripts\python.exe"
$script = "C:\Programmer\Work\horse racing\racepulse\ml-server\scripts\bulk_collect.py"

# 로그에 실행 시작 기록
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content $logFile "[$timestamp] 수집 시작"

# FastAPI 서버가 살아있는지 확인
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 5
    Add-Content $logFile "[$timestamp] FastAPI 서버 확인 완료"
} catch {
    Add-Content $logFile "[$timestamp] FastAPI 서버 미실행 — 수집 건너뜀"
    exit 1
}

# bulk_collect.py 실행
Set-Location $mlServerPath
$process = Start-Process -FilePath $pythonExe `
    -ArgumentList $script `
    -RedirectStandardOutput "$mlServerPath\scripts\collect_stdout.txt" `
    -RedirectStandardError "$mlServerPath\scripts\collect_stderr.txt" `
    -Wait -PassThru -NoNewWindow

$exitCode = $process.ExitCode
$endTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content $logFile "[$endTime] 수집 완료 (exit code: $exitCode)"

# 완료 여부 확인 (스크립트 출력에서 확인)
$output = Get-Content "$mlServerPath\scripts\collect_stdout.txt" -Raw -ErrorAction SilentlyContinue
if ($output -match "이미 전부 계산됨") {
    Add-Content $logFile "[$endTime] *** 전체 수집 완료 — 예약 작업 비활성화 권장 ***"
}
