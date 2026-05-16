# Streamlit Community Cloud Deployment

This guide explains how to deploy RepoQuest to Streamlit Community Cloud.

## Prerequisites

- GitHub account
- Streamlit Community Cloud account (free at [share.streamlit.io](https://share.streamlit.io))
- Public GitHub repository with RepoQuest code

## Deployment Steps

### 1. Prepare Repository

Ensure your repository has:

- ✅ `app/streamlit_app.py` - Main application file
- ✅ `requirements.txt` - Root requirements file
- ✅ `.streamlit/config.toml` - Streamlit configuration
- ✅ `examples/demo_repos/` - Bundled demo repository

**Important:** The root `requirements.txt` should reference the cloud requirements:

```text
-r infra/streamlit/requirements.txt
```

### 2. Push to GitHub

```bash
git add .
git commit -m "Prepare for Streamlit Cloud deployment"
git push origin main
```

**Note:** Repository must be public for Streamlit Community Cloud free tier.

### 3. Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click "New app"
4. Configure deployment:
   - **Repository:** Your GitHub repository
   - **Branch:** `main` (or your default branch)
   - **Main file path:** `app/streamlit_app.py`
5. Click "Deploy"

### 4. Wait for Deployment

Streamlit Cloud will:
- Clone your repository
- Install dependencies from `requirements.txt`
- Start the application
- Provide a public URL

Deployment typically takes 2-5 minutes.

### 5. Verify Deployment

Once deployed:
- ✅ App loads without errors
- ✅ Demo repository analysis works
- ✅ ZIP upload works (up to 25 MB)
- ✅ All tabs display correctly
- ✅ Documentation generation works
- ✅ Export download works

## Configuration

Cloud deployment uses `infra/streamlit/streamlit_config.toml`:

```toml
[server]
maxUploadSize = 25
headless = true

[client]
showErrorDetails = false

[theme]
base = "light"
```

Key differences from local:
- **showErrorDetails:** `false` (hide detailed errors from users)
- **runOnSave:** Not set (not applicable in cloud)
- **port:** Not set (Streamlit Cloud manages ports)

## Dependencies

Cloud runtime dependencies (`infra/streamlit/requirements.txt`):

```text
streamlit>=1.28.0
pandas>=2.0.0
pyyaml>=6.0
```

**No additional system packages required.**

RepoQuest is designed to work with Python standard library and minimal dependencies.

## Environment Variables

**None required.**

RepoQuest does not use:
- API keys
- Secrets
- External services
- Database connections
- Cloud credentials

## Limitations

### Streamlit Community Cloud

- **File upload:** 200 MB limit (RepoQuest enforces 25 MB)
- **Memory:** 1 GB RAM
- **CPU:** Shared resources
- **Storage:** Temporary only (no persistent storage)
- **Execution time:** Apps may sleep after inactivity

### RepoQuest Limits

- **Max ZIP size:** 25 MB
- **Max files scanned:** 600
- **Max file size:** 512 KB
- **Max graph nodes:** 80

These limits ensure the app runs smoothly on Streamlit Community Cloud.

## Troubleshooting

### Deployment Fails

**Check:**
- Repository is public
- `requirements.txt` exists at root
- `app/streamlit_app.py` exists
- No syntax errors in code

**View logs:**
- Click "Manage app" in Streamlit Cloud
- View deployment logs
- Check for import errors or missing dependencies

### App Crashes

**Common causes:**
- Memory limit exceeded (large file upload)
- Timeout (long-running analysis)
- Missing dependency

**Solutions:**
- Enforce file size limits in code
- Use progress indicators
- Verify all imports work

### Upload Not Working

**Check:**
- File size under 25 MB
- ZIP file is valid
- Path validation passes

**Test locally first:**
```bash
python scripts/run_local.py
```

### Graphs Not Rendering

**Possible issues:**
- Too many nodes (limit to 80)
- Invalid DOT syntax
- Streamlit version mismatch

**Solution:**
- Check graph generation logic
- Test with demo repository
- Verify Streamlit version

## Monitoring

### App Health

Streamlit Cloud provides:
- App status (running/sleeping/error)
- Resource usage
- Error logs
- Deployment history

### User Analytics

Streamlit Cloud shows:
- Number of visitors
- Active sessions
- Geographic distribution

## Updates

### Deploy New Version

1. Make changes locally
2. Test thoroughly
3. Commit and push to GitHub
4. Streamlit Cloud auto-deploys from main branch

### Rollback

If deployment fails:
1. Go to Streamlit Cloud dashboard
2. Click "Manage app"
3. View deployment history
4. Revert to previous commit if needed

## Best Practices

### Before Deployment

- ✅ Test locally with `python scripts/run_local.py`
- ✅ Run full test suite: `pytest -q`
- ✅ Verify demo repository works
- ✅ Test ZIP upload with sample files
- ✅ Check all tabs and features
- ✅ Verify export download works

### After Deployment

- ✅ Test on actual Streamlit Cloud URL
- ✅ Verify demo repository analysis
- ✅ Test ZIP upload (small file)
- ✅ Check error handling
- ✅ Verify documentation generation
- ✅ Test export download

### Maintenance

- Keep dependencies updated
- Monitor error logs
- Test after Streamlit updates
- Keep demo repository current

## Security

### Safe by Design

RepoQuest is secure because it:
- ✅ Validates all ZIP uploads
- ✅ Never executes uploaded code
- ✅ Never installs dependencies
- ✅ Uses no external APIs
- ✅ Requires no credentials
- ✅ Stores no user data

### ZIP Upload Safety

- Path traversal protection
- Absolute path rejection
- File size limits
- Binary file skipping
- Safe text decoding

## Performance

### Optimization

- Limit file scanning to 600 files
- Skip binary files early
- Truncate large text previews
- Limit graph nodes
- Use Streamlit caching where appropriate

### Expected Performance

- **Demo repository:** 2-5 seconds
- **Small ZIP (<5 MB):** 5-10 seconds
- **Medium ZIP (10-25 MB):** 10-20 seconds

## Demo Flow

For hackathon judges:

1. **Open app** - Public Streamlit Cloud URL
2. **Select demo repo** - No upload needed
3. **Generate quest** - Click button
4. **Explore tabs** - Overview, Architecture, Reading Path, etc.
5. **Generate docs** - Documentation tab
6. **Export guide** - Download Markdown

## Support

### Streamlit Cloud Issues

- [Streamlit Community Forum](https://discuss.streamlit.io)
- [Streamlit Documentation](https://docs.streamlit.io)
- [Streamlit Cloud Status](https://status.streamlit.io)

### RepoQuest Issues

- Check local deployment first
- Review error logs
- Test with demo repository
- Verify configuration files

## Additional Resources

- [Main README](../../README.md)
- [Local Development Setup](../local/README.md)
- [Architecture Documentation](../../docs/architecture.md)
- [Demo Script](../../docs/demo_script.md)

---

*This guide was created with IBM Bob's assistance.*