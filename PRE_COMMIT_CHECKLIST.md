# GitHub pre-commit checklist

## ✅ Completed inspections

### 1. Security of Sensitive Information
- [x] `.env` File added to `.gitignore`, will not be submitted
- [x] `.env.example` Reserved as a template file, using placeholders
- [x] `claude_desktop_config.json` Wait until the configuration file containing the real API key has been added to `.gitignore`
- [x] All API keys in the code/Tokens are read from environment variables
- [x] `cn_1688_crawler.py` in `API_KEY` and `APP_KEY` It is a 1688 public H5 API parameter, non-sensitive information

### 2. .gitignore configuration
The following have been excluded:
- Python: `__pycache__/`, `*.pyc`, `venv/`
- environment variables: `.env`, `.env.*.local`
- cache: `cache/`, `*.db`
- System files: `.DS_Store`
- test file: `test_*.py`, `demo_*.py`, `run_analysis_*.py`
- data file: `*.csv`, `*.xlsx`, `*.pdf`
- Configuration file: `claude_desktop_config*.json`, `.claude-mcp.json`
- Archive: `archive/`

### 3. Core file integrity
- [x] `README.md` - Complete project documentation
- [x] `LICENSE` - MIT license
- [x] `requirements.txt` - All dependencies (requests added)
- [x] `.env.example` - Environment variable template
- [x] `generate_report.py` - Standard process entry
- [x] `server.py` - MCP server
- [x] `src/` - core source code
- [x] `examples/` - Usage example
- [x] `docs/` - document

### 4. Code quality
- [x] Grammar check passed
- [x] No hard-coded sensitive information
- [x] print statements are user-friendly output information
- [x] Dynamic 30-60-90-day action plan (not hard-coded)

### 5. GitHub Actions
- [x] added `.github/workflows/python-check.yml` for CI checks

## 📋 Submit file list

```bash
# View documents to be submitted
git add -n .

# core file
git add README.md LICENSE requirements.txt .gitignore .env.example
git add generate_report.py server.py

# source code
git add src/

# Examples and documentation
git add examples/ docs/

# Configuration file example
git add mcp_config_example.json

# GitHub Actions
git add .github/
```

## ⚠️ Important reminder

1. **Confirm before first submission**:
   ```bash
   # Make sure .env is not committed
   git check-ignore -v .env
   
   # should show: .env is ignored by .gitignore line 37
   ```

2. **local configuration**:
   ```bash
   # Copy environment variable template
   cp .env.example .env
   # Edit .env and fill in your real API key
   ```

3. **Security advice**:
   - Change the Keepa API Key regularly
   - Do not share your real key with others
   - Using GitHub Secrets for CI/CD

## 🚀 Submit command

```bash
# Initialize the warehouse (if it is a new project)
git init

# Add files
git add .

# Check what will be submitted
git status

# Submit
git commit -m "Initial commit: Amz-Keepa-MCP v3.0

- Amazon FBA actuary analysis system
- 163 Keepa metrics collection
- Real FBA fee calculation
- Interactive HTML reports with profit calculator
- Dynamic 30-60-90 day action plans
- MCP server for Claude Code integration"

# Push to GitHub
git remote add origin https://github.com/yourusername/amz-keepa-mcp.git
git push -u origin main
```
