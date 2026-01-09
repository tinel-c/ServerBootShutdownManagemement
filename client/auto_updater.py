#!/usr/bin/env python3
"""
Auto-updater for Client Monitor
Checks GitHub for updates and automatically installs them
"""

import os
import sys
import json
import logging
import tempfile
import zipfile
import shutil
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
import requests
from packaging import version

logger = logging.getLogger(__name__)

# GitHub repository information
GITHUB_REPO = "owner/ServerBootShutdownMangement"  # Update with actual repo owner
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
CURRENT_VERSION = "2.4.0"  # Current version


class AutoUpdater:
    """Auto-updater for checking and installing updates from GitHub"""
    
    def __init__(self, check_interval_hours=24):
        """Initialize auto-updater
        
        Args:
            check_interval_hours: Hours between update checks (default: 24)
        """
        self.check_interval = timedelta(hours=check_interval_hours)
        self.script_dir = Path(__file__).parent
        self.update_cache = self.script_dir / ".update_cache.json"
        self.current_version = CURRENT_VERSION
        self.last_check = None
        self.latest_version = None
        
        # Load cached update info
        self._load_cache()
    
    def _load_cache(self):
        """Load cached update information"""
        try:
            if self.update_cache.exists():
                with open(self.update_cache, 'r') as f:
                    cache = json.load(f)
                    self.last_check = datetime.fromisoformat(cache.get('last_check', '2000-01-01'))
                    self.latest_version = cache.get('latest_version')
        except Exception as e:
            logger.debug(f"Could not load update cache: {e}")
            self.last_check = datetime.min
    
    def _save_cache(self):
        """Save update information to cache"""
        try:
            cache = {
                'last_check': datetime.now().isoformat(),
                'latest_version': self.latest_version,
                'current_version': self.current_version
            }
            with open(self.update_cache, 'w') as f:
                json.dump(cache, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save update cache: {e}")
    
    def should_check_for_updates(self):
        """Check if it's time to check for updates"""
        if self.last_check is None:
            return True
        
        time_since_check = datetime.now() - self.last_check
        return time_since_check >= self.check_interval
    
    def check_for_updates(self):
        """Check GitHub for new releases
        
        Returns:
            tuple: (has_update: bool, latest_version: str, download_url: str)
        """
        try:
            logger.info(f"Checking for updates (current version: {self.current_version})")
            
            # Make request to GitHub API
            headers = {'Accept': 'application/vnd.github.v3+json'}
            response = requests.get(GITHUB_API_URL, headers=headers, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"GitHub API returned status {response.status_code}")
                return False, None, None
            
            release_data = response.json()
            latest_version = release_data.get('tag_name', '').lstrip('v')
            
            # Find the client package in assets
            download_url = None
            for asset in release_data.get('assets', []):
                if 'client' in asset['name'].lower() and asset['name'].endswith('.zip'):
                    download_url = asset['browser_download_url']
                    break
            
            if not download_url:
                logger.warning("No client package found in latest release")
                return False, None, None
            
            # Compare versions
            try:
                has_update = version.parse(latest_version) > version.parse(self.current_version)
            except Exception as e:
                logger.warning(f"Could not compare versions: {e}")
                has_update = latest_version != self.current_version
            
            self.latest_version = latest_version
            self.last_check = datetime.now()
            self._save_cache()
            
            if has_update:
                logger.info(f"Update available: {self.current_version} -> {latest_version}")
            else:
                logger.info("No updates available")
            
            return has_update, latest_version, download_url
            
        except requests.RequestException as e:
            logger.error(f"Network error checking for updates: {e}")
            return False, None, None
        except Exception as e:
            logger.error(f"Error checking for updates: {e}", exc_info=True)
            return False, None, None
    
    def download_update(self, download_url):
        """Download update package
        
        Args:
            download_url: URL to download the update from
            
        Returns:
            Path to downloaded file or None if failed
        """
        try:
            logger.info(f"Downloading update from: {download_url}")
            
            # Create temporary directory
            temp_dir = Path(tempfile.gettempdir()) / "client_monitor_update"
            temp_dir.mkdir(exist_ok=True)
            
            # Download file
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Save to temporary file
            download_path = temp_dir / "client_update.zip"
            total_size = int(response.headers.get('content-length', 0))
            
            with open(download_path, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            logger.debug(f"Download progress: {percent:.1f}%")
            
            logger.info(f"Update downloaded successfully to: {download_path}")
            return download_path
            
        except Exception as e:
            logger.error(f"Error downloading update: {e}", exc_info=True)
            return None
    
    def install_update(self, update_package_path):
        """Install downloaded update
        
        Args:
            update_package_path: Path to the downloaded update package
            
        Returns:
            bool: True if installation started successfully
        """
        try:
            logger.info("Installing update...")
            
            # Create extraction directory
            extract_dir = Path(tempfile.gettempdir()) / "client_monitor_update" / "extracted"
            if extract_dir.exists():
                shutil.rmtree(extract_dir)
            extract_dir.mkdir(parents=True)
            
            # Extract package
            with zipfile.ZipFile(update_package_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            logger.info("Update package extracted")
            
            # Find the update script
            update_script = None
            for root, dirs, files in os.walk(extract_dir):
                if 'update_client_files.bat' in files:
                    update_script = Path(root) / 'update_client_files.bat'
                    break
            
            if not update_script:
                logger.error("Update script not found in package")
                return False
            
            # Prepare update script execution
            # The script should handle copying files and restarting the service
            logger.info(f"Executing update script: {update_script}")
            
            # Create a batch file to run the update and restart
            restart_script = extract_dir / "apply_update.bat"
            with open(restart_script, 'w') as f:
                f.write(f'''@echo off
echo ============================================================
echo Applying Client Monitor Update
echo ============================================================
echo.
echo Waiting for client to close...
timeout /t 3 /nobreak >nul

echo Changing to update directory...
cd /d "{extract_dir}"

echo Running update script...
call "{update_script}"

if errorlevel 1 (
    echo.
    echo ============================================================
    echo UPDATE FAILED
    echo ============================================================
    echo.
    echo The update script encountered an error.
    echo Your previous version should be restored from backup.
    echo Please check the logs and try again.
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo UPDATE APPLIED SUCCESSFULLY
echo ============================================================
echo.
echo Client Monitor has been updated and restarted.
echo You can close this window.
echo.
timeout /t 5 /nobreak
exit /b 0
''')
            
            # Execute the update script in a detached process
            subprocess.Popen(
                ['cmd', '/c', str(restart_script)],
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                close_fds=True
            )
            
            logger.info("Update installation initiated. Application will restart.")
            return True
            
        except Exception as e:
            logger.error(f"Error installing update: {e}", exc_info=True)
            return False
    
    def check_and_install_updates(self, auto_install=True):
        """Check for updates and optionally install them automatically
        
        Args:
            auto_install: If True, automatically install updates
            
        Returns:
            dict: Update status information
        """
        result = {
            'checked': False,
            'update_available': False,
            'current_version': self.current_version,
            'latest_version': None,
            'installed': False,
            'error': None
        }
        
        try:
            # Check if it's time to check
            if not self.should_check_for_updates():
                logger.debug("Skipping update check (too soon since last check)")
                return result
            
            # Check for updates
            has_update, latest_version, download_url = self.check_for_updates()
            result['checked'] = True
            result['update_available'] = has_update
            result['latest_version'] = latest_version
            
            if not has_update:
                return result
            
            if not auto_install:
                logger.info("Auto-install disabled, skipping installation")
                return result
            
            # Download update
            update_package = self.download_update(download_url)
            if not update_package:
                result['error'] = "Failed to download update"
                return result
            
            # Install update
            success = self.install_update(update_package)
            result['installed'] = success
            
            if not success:
                result['error'] = "Failed to install update"
            
            return result
            
        except Exception as e:
            logger.error(f"Error in check_and_install_updates: {e}", exc_info=True)
            result['error'] = str(e)
            return result


def main():
    """Test auto-updater"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    updater = AutoUpdater(check_interval_hours=0)  # Always check for testing
    result = updater.check_and_install_updates(auto_install=False)
    
    print("\nUpdate Check Results:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

