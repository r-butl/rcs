# Troubleshooting Guide

## Common Issues and Solutions

### 1. ChromeDriver "Exec format error" on macOS

**Error:** `[Errno 8] Exec format error: '/Users/username/.wdm/drivers/chromedriver/...'`

**Cause:** This is a common issue on Apple Silicon Macs (M1/M2) where the wrong architecture ChromeDriver is downloaded.

**Solutions:**

#### Option A: Use the installation script
```bash
python install_chromedriver.py
```

#### Option B: Manual installation
1. Go to https://chromedriver.chromium.org/
2. Download the correct version for your Mac:
   - **Apple Silicon (M1/M2)**: `mac_arm64`
   - **Intel Mac**: `mac64`
3. Extract and move to `/usr/local/bin/`:
```bash
sudo mv chromedriver /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
```

#### Option C: Use Homebrew
```bash
brew install chromedriver
```

### 2. ChromeDriver not found in PATH

**Error:** `ChromeDriver not found in PATH`

**Solution:**
```bash
# Add ChromeDriver to PATH
export PATH="/usr/local/bin:$PATH"

# Or add to your shell config file (~/.zshrc or ~/.bash_profile)
echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### 3. Chrome browser not found

**Error:** `Chrome browser not found`

**Solution:**
1. Install Google Chrome from https://www.google.com/chrome/
2. Make sure it's in `/Applications/Google Chrome.app/`

### 4. LinkedIn login fails

**Error:** `Login failed - check credentials`

**Solutions:**
1. Verify your LinkedIn credentials
2. Check if 2FA is enabled (may require manual intervention)
3. Ensure your account isn't locked
4. Try logging in manually first to ensure the account is active

### 5. No saved jobs found

**Error:** `No saved jobs found`

**Solutions:**
1. Make sure you have saved jobs on LinkedIn
2. Navigate to LinkedIn → My Items → Saved Jobs to verify
3. Check if you're logged into the correct account

### 6. Rate limiting or blocking

**Error:** `Timeout during login process` or `Navigation error`

**Solutions:**
1. Increase delays in the code (modify `DELAY_BETWEEN_JOBS`)
2. Run during off-peak hours
3. Use a VPN if you're being rate-limited
4. Try running in non-headless mode to see what's happening

### 7. Selenium version conflicts

**Error:** `WebDriverException` or import errors

**Solution:**
```bash
# Uninstall and reinstall selenium
pip uninstall selenium
pip install selenium>=4.15.0

# Also ensure webdriver-manager is up to date
pip install --upgrade webdriver-manager
```

### 8. Permission denied errors

**Error:** `Permission denied` when running scripts

**Solution:**
```bash
# Make scripts executable
chmod +x linkedin_scraper.py
chmod +x example_usage.py
chmod +x install_chromedriver.py
```

## System-Specific Issues

### macOS (Apple Silicon)

1. **ChromeDriver Architecture**: Always use `mac_arm64` version
2. **Rosetta**: Some versions may require Rosetta 2
3. **Security**: macOS may block ChromeDriver - go to System Preferences → Security & Privacy → General → Allow

### macOS (Intel)

1. **ChromeDriver Architecture**: Use `mac64` version
2. **Gatekeeper**: May need to allow ChromeDriver in Security settings

### Linux

1. **Dependencies**: Install required packages:
```bash
sudo apt-get install -y chromium-browser chromium-chromedriver
# or
sudo yum install -y chromium chromium-headless chromedriver
```

2. **Display**: For headless mode, ensure Xvfb is available:
```bash
sudo apt-get install -y xvfb
```

### Windows

1. **ChromeDriver**: Download from https://chromedriver.chromium.org/
2. **PATH**: Add ChromeDriver to system PATH
3. **Antivirus**: May block ChromeDriver - add to exclusions

## Debug Mode

Enable detailed logging to see what's happening:

```python
import logging
logging.getLogger('linkedin_scraper').setLevel(logging.DEBUG)
```

## Manual Verification

If the scraper fails, manually verify:

1. **Chrome**: Open Chrome and navigate to any website
2. **ChromeDriver**: Run `chromedriver --version` in terminal
3. **LinkedIn**: Log in manually and navigate to saved jobs
4. **Network**: Check internet connection and firewall settings

## Getting Help

If you're still having issues:

1. Check the log file: `linkedin_scraper.log`
2. Run the test script: `python test_installation.py`
3. Try the installation script: `python install_chromedriver.py`
4. Check your system architecture and Chrome version
5. Ensure all dependencies are properly installed

## Common Commands

```bash
# Test installation
python test_installation.py

# Install ChromeDriver
python install_chromedriver.py

# Run scraper
python example_usage.py

# Check ChromeDriver version
chromedriver --version

# Check Chrome version (macOS)
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version

# Check Python packages
pip list | grep -E "(selenium|webdriver|pandas)"
```
