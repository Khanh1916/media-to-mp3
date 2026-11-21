@echo off
setlocal
set RUSTUP_HOME=E:\tools\rust\rustup
set CARGO_HOME=E:\tools\rust\cargo
set PATH=E:\tools\rust\cargo\bin;%PATH%

if not exist "%~dp0target\release\media-to-mp3.exe" (
    echo [media-to-mp3] Building release binary...
    pushd "%~dp0"
    cargo build --release
    popd
)

"%~dp0target\release\media-to-mp3.exe" %*
