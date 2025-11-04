# CareSense Setup Notes

## Installation Issues and Resolutions

### 1. Pydantic v2 Compatibility (FIXED)

**Issue**: The project was using Pydantic v2 but importing `BaseSettings` from the old Pydantic v1 API.

**Resolution**:
- Added `pydantic-settings>=2.0.0` to requirements.txt
- Updated `caresense/config.py` to import from `pydantic_settings` instead of `pydantic`
- Changed `Config` class to `model_config` dict (Pydantic v2 pattern)

### 2. Pyfhel Installation (BLOCKED on macOS)

**Issue**: Pyfhel requires OpenMP support which is not available in Apple's default clang compiler.

**Error**:
```
clang++: error: unsupported option '-fopenmp'
fatal error: 'omp.h' file not found
```

**Workarounds**:

Option A - Install OpenMP via Homebrew:
```bash
brew install libomp
export CC=/usr/bin/clang
export CXX=/usr/bin/clang++
export CPPFLAGS="-I/opt/homebrew/opt/libomp/include"
export LDFLAGS="-L/opt/homebrew/opt/libomp/lib"
pip install pyfhel
```

Option B - Use Docker (Recommended):
```bash
docker compose up --build
```

Option C - Make biometric features optional (for testing):
Create a stub for development that skips FHE encryption temporarily.

### 3. Python Environment

The system has multiple Python versions:
- System Python 3.9.6 at `/usr/bin/python3`
- Pyenv Python 3.11.9 at `/Users/nessakodo/.pyenv/versions/3.11.9`

**Use Python 3.11 for this project**:
```bash
python3.11 -m venv venv
source venv/activate
pip install -r requirements.txt
```

Or use pyenv:
```bash
pyenv shell 3.11.9
```

## Running the Application

### Without Pyfhel (Testing Mode)

For basic testing without homomorphic encryption:

1. Comment out pyfhel imports temporarily
2. Mock the biometric endpoints
3. Run: `python3.11 -m uvicorn app:app --reload --port 8080`

### With Docker (Full Features)

```bash
docker compose up --build
# Backend: http://localhost:8080
# Frontend: http://localhost:4173
```

### Local Development (After fixing pyfhel)

```bash
# Backend
make serve
# or
python3.11 -m uvicorn app:app --reload --port 8080

# Frontend (separate terminal)
cd frontend && npm run dev
```

## Quick Health Check

```bash
curl http://localhost:8080/v1/health
```

Expected response:
```json
{"status": "ok"}
```
