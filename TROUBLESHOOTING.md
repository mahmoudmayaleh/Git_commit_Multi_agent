# Troubleshooting Guide

This document helps you resolve common issues with the Git Commit Writer Pipeline.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [LLM Issues](#llm-issues)
3. [Git Issues](#git-issues)
4. [Runtime Errors](#runtime-errors)
5. [Performance Issues](#performance-issues)

---

## Installation Issues

### "ModuleNotFoundError: No module named 'X'"

**Problem**: Missing Python dependencies.

**Solution**:

```powershell
pip install -r requirements.txt
```

If you get permission errors:

```powershell
pip install --user -r requirements.txt
```

### "ImportError: DLL load failed" (Windows)

**Problem**: Missing Visual C++ Redistributables for PyTorch.

**Solution**:

1. Download and install [Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)
2. Restart your terminal
3. Reinstall PyTorch:

```powershell
pip uninstall torch
pip install torch
```

---

## LLM Issues

### "CUDA out of memory"

**Problem**: GPU doesn't have enough memory for the model.

**Solutions**:

1. **Use 8-bit quantization** (recommended):

   ```env
   USE_8BIT=true
   ```

2. **Use CPU instead**:

   ```env
   DEVICE=cpu
   ```

3. **Use API mode** instead of local:
   ```env
   LLM_MODE=api
   ```

### "Model download is slow or fails"

**Problem**: HuggingFace model download issues.

**Solutions**:

1. **Pre-download the model**:

   ```powershell
   python -c "from transformers import AutoModelForCausalLM; AutoModelForCausalLM.from_pretrained('openchat/openchat-3.5-0106')"
   ```

2. **Use a mirror** (if in China or other regions):

   ```powershell
   $env:HF_ENDPOINT="https://hf-mirror.com"
   python main.py
   ```

3. **Download manually**:
   - Go to https://huggingface.co/openchat/openchat-3.5-0106
   - Click "Files and versions"
   - Download all files to a local directory
   - Update .env:
     ```env
     LOCAL_MODEL_PATH=C:\path\to\downloaded\model
     ```

### "API connection refused"

**Problem**: Can't connect to LLM API endpoint.

**Solutions**:

1. **Check if API server is running**:

   ```powershell
   curl http://localhost:8000/v1/models
   ```

2. **Update API URL in .env**:

   ```env
   API_BASE_URL=http://localhost:8000/v1
   ```

3. **Check firewall settings** - ensure port 8000 (or your API port) is open

---

## Git Issues

### "No staged changes found"

**Problem**: No files are staged for commit.

**Solution**:

```powershell
# Stage specific files
git add file1.py file2.py

# Or stage all changes
git add .

# Verify staged files
git status
```

### "fatal: not a git repository"

**Problem**: Current directory is not a Git repository.

**Solutions**:

1. **Navigate to your Git repo**:

   ```powershell
   cd path\to\your\repo
   python main.py
   ```

2. **Or specify repo path**:

   ```powershell
   python main.py --repo-path "C:\path\to\repo"
   ```

3. **Initialize a new repo**:
   ```powershell
   git init
   ```

### "GitPython command error"

**Problem**: GitPython can't execute Git commands.

**Solution**:

1. Ensure Git is in your PATH:

   ```powershell
   git --version
   ```

2. If not found, add Git to PATH:
   - Git is typically at: `C:\Program Files\Git\cmd`
   - Add to PATH in System Environment Variables

---

## Runtime Errors

### "Configuration Error: Invalid LLM_MODE"

**Problem**: .env file has invalid configuration.

**Solution**:

1. Check your .env file
2. Ensure `LLM_MODE` is either `local` or `api`
3. Example:
   ```env
   LLM_MODE=local
   ```

### "Pipeline failed with errors"

**Problem**: One or more agents failed during execution.

**Solutions**:

1. **Run with verbose mode** to see detailed errors:

   ```powershell
   python main.py --verbose
   ```

2. **Run with debug mode** to see all outputs:

   ```powershell
   python main.py --debug
   ```

3. **Check the specific error messages** and refer to relevant sections above

### "Commit message format validation failed"

**Problem**: Generated commit message doesn't follow conventional format.

**Solution**: This is usually auto-corrected. If it persists:

1. Try a different temperature:

   ```env
   TEMPERATURE=0.5
   ```

2. The pipeline will fall back to rule-based generation if LLM fails

---

## Performance Issues

### "Pipeline is very slow"

**Problem**: Pipeline takes too long to complete.

**Solutions**:

1. **For local inference**:

   - Use GPU instead of CPU:
     ```env
     DEVICE=cuda
     ```
   - Use 8-bit quantization:
     ```env
     USE_8BIT=true
     ```

2. **Switch to API mode**:

   ```env
   LLM_MODE=api
   ```

   Then run a fast inference server like vLLM:

   ```powershell
   pip install vllm
   vllm serve openchat/openchat-3.5-0106
   ```

3. **Reduce max tokens**:
   ```env
   MAX_NEW_TOKENS=256
   ```

### "High memory usage"

**Problem**: Process uses too much RAM.

**Solutions**:

1. **Use 8-bit quantization**:

   ```env
   USE_8BIT=true
   ```

2. **Close other applications**

3. **Use API mode** instead of local inference

---

## Getting Help

If you still have issues:

1. **Check the logs** - run with `--verbose` flag
2. **Review configuration** - ensure .env is correctly set up
3. **Test components individually**:

   ```powershell
   python tests/example_usage.py
   ```

4. **Check system requirements**:
   - Python 3.8+
   - Git CLI
   - 8GB+ RAM (16GB recommended for local inference)
   - CUDA-capable GPU (optional but recommended)

---

## Common Error Messages Reference

| Error                  | Likely Cause       | Quick Fix                                     |
| ---------------------- | ------------------ | --------------------------------------------- |
| `ModuleNotFoundError`  | Missing dependency | `pip install -r requirements.txt`             |
| `CUDA out of memory`   | GPU memory full    | Set `USE_8BIT=true` or `DEVICE=cpu`           |
| `No staged changes`    | Nothing to commit  | `git add .`                                   |
| `Not a git repository` | Wrong directory    | `cd` to your repo or use `--repo-path`        |
| `Connection refused`   | API not running    | Start your API server or use `LLM_MODE=local` |
| `Model not found`      | Download failed    | Pre-download model or check internet          |

---

**Still having issues?** Check the README.md for more information or create an issue with:

- Your .env configuration (remove sensitive info)
- Full error message from `--verbose` mode
- Your Python version and OS
