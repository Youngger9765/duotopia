# Duotopia 快速環境檢查

Write-Host "`n═══════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  🚀 Duotopia 環境檢查" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Cyan

Write-Host "`n📍 當前目錄: $(Get-Location)" -ForegroundColor Yellow

# 顏色代碼
$ok = "Green"
$fail = "Red"
$warn = "Yellow"
$info = "Cyan"

# 檢查 1: Node.js & npm
Write-Host "`n[1] 檢查 Node.js..." -ForegroundColor $info
$node = node --version 2>$null
$npm = npm --version 2>$null

if ($node) { 
    Write-Host "  ✓ Node.js $node" -ForegroundColor $ok 
} else { 
    Write-Host "  ✗ Node.js 未安裝" -ForegroundColor $fail 
    Write-Host "    → 下載: https://nodejs.org/" -ForegroundColor $warn
}

if ($npm) { 
    Write-Host "  ✓ npm $npm" -ForegroundColor $ok 
} else { 
    Write-Host "  ✗ npm 未安裝" -ForegroundColor $fail 
}

# 檢查 2: Python
Write-Host "`n[2] 檢查 Python..." -ForegroundColor $info
$python = python --version 2>$null
$pip = python -m pip --version 2>$null

if ($python) { 
    Write-Host "  ✓ $python" -ForegroundColor $ok 
} else { 
    Write-Host "  ✗ Python 未在 PATH 中" -ForegroundColor $fail 
    Write-Host "    → 下載: https://www.python.org/" -ForegroundColor $warn
}

# 檢查 3: Git
Write-Host "`n[3] 檢查 Git..." -ForegroundColor $info
$git = git --version 2>$null

if ($git) { 
    Write-Host "  ✓ $git" -ForegroundColor $ok 
} else { 
    Write-Host "  ✗ Git 未安裝" -ForegroundColor $fail 
}

# 檢查 4: 專案結構
Write-Host "`n[4] 檢查專案結構..." -ForegroundColor $info

$dirs = @("backend", "frontend", ".github")
foreach ($dir in $dirs) {
    if (Test-Path $dir -PathType Container) {
        Write-Host "  ✓ $dir/" -ForegroundColor $ok
    } else {
        Write-Host "  ✗ $dir/ 未找到" -ForegroundColor $fail
    }
}

# 檢查 5: 依賴檔案
Write-Host "`n[5] 檢查依賴檔案..." -ForegroundColor $info

if (Test-Path "backend\requirements.txt") {
    Write-Host "  ✓ backend/requirements.txt" -ForegroundColor $ok
} else {
    Write-Host "  ✗ backend/requirements.txt 未找到" -ForegroundColor $fail
}

if (Test-Path "frontend\package.json") {
    Write-Host "  ✓ frontend/package.json" -ForegroundColor $ok
} else {
    Write-Host "  ✗ frontend/package.json 未找到" -ForegroundColor $fail
}

# 檢查 6: 環境變數檔案
Write-Host "`n[6] 檢查環境變數檔案..." -ForegroundColor $info

if (Test-Path "backend\.env") {
    Write-Host "  ✓ backend/.env 已存在" -ForegroundColor $ok
} else {
    Write-Host "  ○ backend/.env 不存在 (可建立)" -ForegroundColor $warn
}

if (Test-Path "frontend\.env.local") {
    Write-Host "  ✓ frontend/.env.local 已存在" -ForegroundColor $ok
} else {
    Write-Host "  ○ frontend/.env.local 不存在 (可建立)" -ForegroundColor $warn
}

# 檢查 7: 虛擬環境
Write-Host "`n[7] 檢查虛擬環境..." -ForegroundColor $info

if (Test-Path "backend\venv" -PathType Container) {
    Write-Host "  ✓ backend/venv 已存在" -ForegroundColor $ok
} else {
    Write-Host "  ○ backend/venv 不存在 (需要建立)" -ForegroundColor $warn
}

if (Test-Path "frontend\node_modules" -PathType Container) {
    Write-Host "  ✓ frontend/node_modules 已存在" -ForegroundColor $ok
} else {
    Write-Host "  ○ frontend/node_modules 不存在 (需要執行 npm install)" -ForegroundColor $warn
}

Write-Host "`n═══════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  📋 設置步驟" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Cyan

Write-Host "`n如果上面有紅色的 ✗，請先安裝所需軟體。

然後執行以下命令設置環境:

📌 後端設置 (在新 PowerShell 終端):
  cd backend
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  pip install -r requirements.txt

📌 前端設置 (在新 PowerShell 終端):
  cd frontend
  npm install

📌 啟動開發伺服器:
  
  Terminal 1 (後端):
    cd backend
    .\venv\Scripts\Activate.ps1
    uvicorn main:app --reload --port 8080
  
  Terminal 2 (前端):
    cd frontend
    npm run dev

📌 訪問應用:
  前端: http://localhost:5173
  API 文檔: http://localhost:8080/docs

" -ForegroundColor $info

Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Cyan
