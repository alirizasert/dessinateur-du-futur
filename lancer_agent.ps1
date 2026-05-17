# Dessinateur du Futur - Script de lancement
$env:PYTHONUTF8 = "1"
$env:TEMP = "D:\tmp_pip"

Write-Host "Demarrage du Dessinateur du Futur..." -ForegroundColor Cyan
Set-Location $PSScriptRoot
python -c "import sys; sys.path.insert(0, 'D:\python_libs'); exec(open('agent.py', encoding='utf-8').read())"
