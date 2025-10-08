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
Write-Host ".gitignore created successfully"

# --- Initialize Git if not already initialized ---
if (-not (Test-Path "$localPath\.git")) {
    git init
    Write-Host "Git repository initialized"
}

# --- Request GitHub credentials ---
$githubUser = Read-Host "Enter your GitHub username"
$repoName = Read-Host "Enter repository name (e.g. GPUOptimizedAvatar)"
$pat = Read-Host "Enter your Personal Access Token (PAT)" -AsSecureString
$ptr = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($pat))

# --- Setup origin ---
if (git remote get-url origin 2>$null) {
    git remote remove origin
    Write-Host "Old origin removed"
}

# Fixed: Using curly braces for variables
$remoteUrl = "https://${githubUser}:${ptr}@github.com/${githubUser}/${repoName}.git"
git remote add origin $remoteUrl
Write-Host "New origin added successfully"

# --- Add files and commit ---
git add .
git commit -m "Initial commit with .gitignore"

# --- Set main branch and push ---
git branch -M main
Write-Host "Main branch set"

Write-Host "Pushing to GitHub..."
git push -u origin main

Write-Host "Done! Repository is ready on GitHub!"
