# =========================================
# PowerShell "умный" скрипт для GitHub
# =========================================

# Путь к локальному проекту
$localPath = "C:\Users\Gherw\Desktop\Stable-deffusion-BOT"

# Переходим в папку проекта
Set-Location $localPath

# --- Создаём .gitignore ---
$gitignorePath = Join-Path $localPath ".gitignore"
$gitignoreContent = @"
# Python
__pycache__/
*.py[cod]
*.pyo
*.pyd
*.pkl
*.log
*.sqlite3
.env
.venv/
env/
venv/
*.egg-info/
dist/
build/

# Jupyter
.ipynb_checkpoints

# IDEs
.vscode/
.idea/

# System
.DS_Store
Thumbs.db

# Large files
*.zip
*.tar
*.tar.gz
*.tgz
*.mp4
*.mp3
*.mov
*.avi
*.mkv
*.7z

# Python virtual environments
*.egg
*.whl
"@

$gitignoreContent | Out-File -Encoding UTF8 -FilePath $gitignorePath
Write-Host ".gitignore создан ✅"

# --- Инициализация Git, если ещё не инициализирован ---
if (-not (Test-Path "$localPath\.git")) {
    git init
    Write-Host "Git репозиторий инициализирован ✅"
}

# --- Запрос данных GitHub ---
$githubUser = Read-Host "Введите ваш GitHub username"
$repoName = Read-Host "Введите имя репозитория на GitHub (например GPUOptimizedAvatar)"
$pat = Read-Host "Введите Personal Access Token (PAT)" -AsSecureString
$ptr = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($pat))

# --- Настройка origin ---
if (git remote get-url origin 2>$null) {
    git remote remove origin
    Write-Host "Старый origin удалён."
}

# ИСПРАВЛЕНО: Используем фигурные скобки для переменных
$remoteUrl = "https://${githubUser}:${ptr}@github.com/${githubUser}/${repoName}.git"
git remote add origin $remoteUrl
Write-Host "Новый origin добавлен ✅"

# --- Добавляем файлы и коммит ---
git add .
git commit -m "Initial commit with .gitignore"

# --- Устанавливаем ветку main и пуш ---
git branch -M main
Write-Host "Ветка main установлена."

Write-Host "Пушим на GitHub..."
git push -u origin main

Write-Host "✅ Все действия выполнены. Репозиторий готов на GitHub!"
