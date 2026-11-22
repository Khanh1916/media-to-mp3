@echo off
setlocal

rem 1. Pre-built binary in same directory (release archive)
if exist "%~dp0media-to-mp3.exe" (
    "%~dp0media-to-mp3.exe" %*
    exit /b %ERRORLEVEL%
)
if exist "%~dp0MediaToMP3.exe" (
    "%~dp0MediaToMP3.exe" %*
    exit /b %ERRORLEVEL%
)

rem 2. Development mode: locate Cargo and build from source
if defined CARGO_HOME (
    set "PATH=%CARGO_HOME%\bin;%PATH%"
) else if exist "E:\tools\rust\cargo\bin" (
    set "RUSTUP_HOME=E:\tools\rust\rustup"
    set "CARGO_HOME=E:\tools\rust\cargo"
    set "PATH=E:\tools\rust\cargo\bin;%PATH%"
)

if not exist "%~dp0target\release\media-to-mp3.exe" (
    echo [media-to-mp3] Building release binary...
    pushd "%~dp0"
    cargo build --release
    popd
)

"%~dp0target\release\media-to-mp3.exe" %*
