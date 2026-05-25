@echo off
rem ==============================================================================
rem ADHD Productivity MVP - Backend Test and Quality Runner (Windows)
rem ==============================================================================

echo =====================================================
echo Starting ADHD Productivity Backend Quality Pipeline...
echo =====================================================

python --version

echo.
echo [1/4] Checking imports formatting with isort...
python -m isort --check-only src
if %errorlevel% neq 0 (
    echo [ERROR] Import sorting check failed! Run "isort src" to fix.
    exit /b 1
)
echo [SUCCESS] Import sorting check passed!

echo.
echo [2/4] Checking code formatting with black...
python -m black --check src
if %errorlevel% neq 0 (
    echo [ERROR] Code formatting check failed! Run "black src" to fix.
    exit /b 1
)
echo [SUCCESS] Code formatting check passed!

echo.
echo [3/4] Linting code with flake8...
python -m flake8 src
if %errorlevel% neq 0 (
    echo [ERROR] Linter checks failed! Review the errors above.
    exit /b 1
)
echo [SUCCESS] Linter checks passed!

echo.
echo [4/4] Running automated tests with pytest...
set DATABASE_URL=sqlite:///:memory:
set GROQ_API_KEY=mock_groq_key_for_ci
python -m pytest
if %errorlevel% neq 0 (
    echo =====================================================
    echo [FAILURE] Automated tests failed. Please investigate.
    echo =====================================================
    exit /b 1
)

echo =====================================================
echo SUCCESS: All backend checks and tests passed!
echo =====================================================
exit /b 0
