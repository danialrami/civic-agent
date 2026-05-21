# Troubleshooting

Common issues and their solutions when working with the Civic Agent project.

---

## API Issues

### Problem: `ValueError: GOOGLE_CIVIC_API_KEY not set in .env file`

**Cause**: The `.env` file is missing or the API key is not set.

**Solution**:
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Get an API key from [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
3. Edit `.env` and set `GOOGLE_CIVIC_API_KEY=your_actual_key_here`

---

### Problem: `ValueError: CIVIC_ADDRESS not set in .env file`

**Cause**: Your address is not configured in `.env`.

**Solution**:
1. Edit `.env` and set your full address:
   ```
   CIVIC_ADDRESS=123 Main St, San Antonio, TX 78201
   ```
2. Use the format: `Street, City, State ZIP`
3. The address must be a valid U.S. residential address

---

### Problem: `HttpError 403: The request is missing a valid API key`

**Cause**: Invalid or missing API key.

**Solution**:
1. Verify the API key in `.env` is correct (no extra spaces)
2. Check that "Civic Information API" is enabled in your Google Cloud project
3. If you restricted the API key, ensure the restriction allows Civic Information API access
4. Check API quota at [Google Cloud Console > APIs & Services > Quotas](https://console.cloud.google.com/apis/api/civicinfo.googleapis.com/quotas)

---

### Problem: `HttpError 400: Invalid address`

**Cause**: The address format is incorrect or not recognized by Google's API.

**Solution**:
1. Verify the address is a complete U.S. street address
2. Try a simpler format: `123 Main Street, San Antonio, TX 78201`
3. The API may not recognize PO boxes or non-standard addresses
4. Check for typos in street name, city, or ZIP code

---

### Problem: API Returns Empty Elections List

**Cause**: No upcoming elections found for the address.

**Solution**:
1. This is normal - there may not be elections in the near future
2. Check the [Google Civic API documentation](https://developers.google.com/civic-information) for election availability
3. Try a different address in an area with known upcoming elections
4. Verify the current date - elections may have already passed

---

## Python/uv Issues

### Problem: `uv: command not found`

**Cause**: `uv` is not installed.

**Solution**:
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with pip
pip install uv
```

---

### Problem: `ModuleNotFoundError: No module named 'googleapiclient'`

**Cause**: Dependencies not installed.

**Solution**:
```bash
uv sync
```

---

### Problem: `ModuleNotFoundError: No module named 'dotenv'`

**Cause**: Missing `python-dotenv` dependency.

**Solution**:
```bash
uv add python-dotenv
```

---

## OpenCode Agent Issues

### Problem: Agent not appearing in OpenCode

**Cause**: Agent file not in the correct location or invalid YAML frontmatter.

**Solution**:
1. Verify agent file is at `.opencode/agents/civic-researcher.md`
2. Check YAML frontmatter syntax (should start and end with `---`)
3. Ensure `description` field is present (required)
4. Restart OpenCode session to reload agent definitions

---

### Problem: Agent can't read election data files

**Cause**: Output directory doesn't exist or paths are incorrect.

**Solution**:
1. Run the Python tool first: `uv run python src/civic_agent/api.py`
2. Verify `output/` directory was created with timestamped subdirectories
3. Check that `election_summary.md` exists in the output folder
4. The agent reads from the most recent `output/{timestamp}/` directory

---

### Problem: Agent has write access (security concern)

**Cause**: Permission configuration is incorrect.

**Solution**:
1. Verify `.opencode/agents/civic-researcher.md` has:
   ```yaml
   permission:
     read: allow
     edit: deny
     write: deny
     bash: deny
   ```
2. Restart OpenCode to reload permissions
3. Test by attempting to edit a file as the agent

---

## Time/Date Issues

### Problem: Agent says "I don't know what time it is"

**Cause**: The agent needs the time-tools skill to get current time.

**Solution**:
1. Verify `skill: allow` is set in the agent's permission block
2. The agent should use the time-tools skill to get current time
3. If time-tools skill is unavailable, the agent can read the timestamp from the output directory name

---

### Problem: Election dates seem wrong or outdated

**Cause**: Election data is stale (generated days/weeks ago).

**Solution**:
1. Re-run the Python tool to refresh data:
   ```bash
   uv run python src/civic_agent/api.py
   ```
2. The new data will be in a new `output/{timestamp}/` directory
3. The agent reads the most recent timestamped directory

---

## Git Issues

### Problem: Accidentally committed `.env` file

**Cause**: `.env` was not in `.gitignore`.

**Solution**:
1. Add `.env` to `.gitignore`
2. Remove from git tracking (but keep the file):
   ```bash
   git rm --cached .env
   git commit -m "Remove .env from tracking"
   ```
3. Verify `.env` is now ignored: `git status`

---

## Still Having Issues?

1. Check the [Google Civic Information API docs](https://developers.google.com/civic-information)
2. Review the project documentation in `docs/`
3. Open an issue on the project repository with:
   - Your OS and Python version
   - The exact error message
   - Steps to reproduce the issue
