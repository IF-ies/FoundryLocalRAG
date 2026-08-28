<#
.SYNOPSIS
    FoundryLocalRAG baslaticisi.

.DESCRIPTION
    venv'deki Python'u kullanir ve Turkce karakterler icin cikti kodlamasini
    ayarlar. Argumanlar oldugu gibi main.py'ye gecer.

.EXAMPLE
    .\rag.ps1 chat
    .\rag.ps1 ask "AGI tanimlanabilir mi?"
    .\rag.ps1 ingest --reset
    .\rag.ps1 status
#>

$ErrorActionPreference = "Stop"

$kok = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $kok ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Error "venv bulunamadi: $python`nKurulum: python -m venv .venv; .\.venv\Scripts\python.exe -m pip install -r requirements.txt"
    exit 1
}

$env:PYTHONIOENCODING = "utf-8"
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch {}

if ($args.Count -eq 0) {
    # Arguman verilmediyse en sik kullanilan komutu ac.
    & $python (Join-Path $kok "main.py") chat
} else {
    & $python (Join-Path $kok "main.py") @args
}
exit $LASTEXITCODE
