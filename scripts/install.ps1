# Installation Script for Windows
# Run this script in PowerShell to install all dependencies

Write-Host "=================================" -ForegroundColor Cyan
Write-Host " Git Commit Writer Pipeline Setup" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
Write-Host "  $pythonVersion" -ForegroundColor Green

# Step 1: Install core dependencies
Write-Host ""
Write-Host "Step 1: Installing CORE dependencies..." -ForegroundColor Yellow
pip install GitPython requests python-dotenv colorama

# Step 2: Ask about LLM mode
Write-Host ""
Write-Host "Step 2: Choose your LLM mode:" -ForegroundColor Yellow
Write-Host "  1. Local inference (requires PyTorch + transformers, ~7GB download)"
Write-Host "  2. API mode (minimal install, requires running API server)"
Write-Host "  3. Skip LLM setup for now (install manually later)"
Write-Host ""

$choice = Read-Host "Enter your choice (1/2/3)"

if ($choice -eq "1") {
    Write-Host ""
    Write-Host "Installing PyTorch and transformers..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Choose PyTorch version:" -ForegroundColor Cyan
    Write-Host "  1. CUDA 11.8 (for NVIDIA GPUs)"
    Write-Host "  2. CUDA 12.1 (for newer NVIDIA GPUs)"
    Write-Host "  3. CPU only (no GPU)"
    Write-Host ""
    
    $torchChoice = Read-Host "Enter your choice (1/2/3)"
    
    if ($torchChoice -eq "1") {
        Write-Host "Installing PyTorch with CUDA 11.8..." -ForegroundColor Green
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
    }
    elseif ($torchChoice -eq "2") {
        Write-Host "Installing PyTorch with CUDA 12.1..." -ForegroundColor Green
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
    }
    else {
        Write-Host "Installing PyTorch CPU only..." -ForegroundColor Green
        pip install torch torchvision torchaudio
    }
    
    Write-Host "Installing transformers and accelerate..." -ForegroundColor Green
    pip install transformers accelerate
    
    Write-Host ""
    Write-Host "Creating .env file with LOCAL mode..." -ForegroundColor Green
    if (Test-Path .env) {
        Write-Host "  .env already exists, skipping" -ForegroundColor Yellow
    } else {
        Copy-Item .env.example .env
        (Get-Content .env) -replace 'LLM_MODE=local', 'LLM_MODE=local' | Set-Content .env
    }
}
elseif ($choice -eq "2") {
    Write-Host ""
    Write-Host "API mode selected." -ForegroundColor Green
    Write-Host "Note: You'll need to run an API server separately." -ForegroundColor Yellow
    Write-Host ""
    
    Write-Host "Creating .env file with API mode..." -ForegroundColor Green
    if (Test-Path .env) {
        Write-Host "  .env already exists, updating to API mode..." -ForegroundColor Yellow
        (Get-Content .env) -replace 'LLM_MODE=local', 'LLM_MODE=api' | Set-Content .env
    } else {
        Copy-Item .env.example .env
        (Get-Content .env) -replace 'LLM_MODE=local', 'LLM_MODE=api' | Set-Content .env
    }
}
else {
    Write-Host ""
    Write-Host "Skipping LLM setup." -ForegroundColor Yellow
    Write-Host "You can install later with:" -ForegroundColor Cyan
    Write-Host "  pip install torch torchvision torchaudio transformers accelerate" -ForegroundColor Cyan
    
    if (-not (Test-Path .env)) {
        Write-Host ""
        Write-Host "Creating .env file..." -ForegroundColor Green
        Copy-Item .env.example .env
    }
}

# Step 3: Verify installation
Write-Host ""
Write-Host "Step 3: Verifying installation..." -ForegroundColor Yellow
python quickstart.py

Write-Host ""
Write-Host "=================================" -ForegroundColor Cyan
Write-Host " Setup Complete!" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Edit .env file if needed: notepad .env"
Write-Host "  2. Try the example: python tests\example_usage.py"
Write-Host "  3. Use with your code: git add . && python main.py"
Write-Host ""
