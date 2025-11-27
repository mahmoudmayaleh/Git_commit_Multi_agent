@echo off
echo ========================================
echo  Git Commit Writer - Quick Install
echo ========================================
echo.

echo Installing CORE dependencies...
pip install GitPython requests python-dotenv colorama

echo.
echo ========================================
echo  Core installation complete!
echo ========================================
echo.
echo For LOCAL LLM mode (optional):
echo   pip install torch torchvision torchaudio transformers accelerate
echo.
echo For API mode:
echo   Just update .env with LLM_MODE=api
echo.
echo Next: Run 'python quickstart.py' to verify
echo.
pause
