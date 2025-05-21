# update_checker.py
import requests
import logging
import webbrowser
from tkinter import messagebox

class UpdateChecker:
    def __init__(self, app_name, current_version, repo_owner, repo_name, token=None):
        """Initialize update checker with application and repository details.
        
        Args:
            app_name: Name of the application
            current_version: Current application version string (e.g. "1.0.0")
            repo_owner: GitHub repository owner/username
            repo_name: GitHub repository name
            token: Optional GitHub API token for private repositories
        """
        self.app_name = app_name
        self.current_version = current_version
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.token = token
        self.api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases"
        
    def _parse_version(self, version_str):
        """Convert version string to tuple for comparison."""
        if version_str.lower().startswith('v'):
            version_str = version_str[1:]
        return tuple(map(int, version_str.split('.')))
    
    def _is_newer_version(self, remote_version):
        """Compare remote version with current version."""
        try:
            current = self._parse_version(self.current_version)
            remote = self._parse_version(remote_version)
            return remote > current
        except Exception as e:
            logging.error(f"Version comparison error: {e}")
            return False
            
    def check_and_notify(self, parent_window=None):
        """Check for updates and notify user if newer version exists."""
        try:
            logging.info(f"Checking for updates from: {self.api_url}")
            
            # Get headers with token if available
            headers = {"Authorization": f"token {self.token}"} if self.token else {}
            
            # Add user-agent header to avoid GitHub API limitations
            headers["User-Agent"] = f"{self.app_name} Update Checker"
            
            # Request releases from GitHub API
            response = requests.get(self.api_url, headers=headers, timeout=10)
            
            # Log the response details
            logging.info(f"GitHub API response status: {response.status_code}")
            
            # Handle 404 and other errors more gracefully
            if response.status_code != 200:
                error_message = f"GitHub API returned status {response.status_code}"
                if response.status_code == 404:
                    error_message += f": Repository or releases not found at {self.api_url}"
                elif response.status_code == 403:
                    error_message += ": Rate limit exceeded or access denied"
                logging.warning(error_message)
                return False
            
            releases = response.json()
            
            if not releases:
                logging.info("No releases found in the repository")
                return False
                
            # Get latest release (GitHub returns them in descending order)
            latest_release = releases[0]
            latest_version = latest_release['tag_name']
            if latest_version.lower().startswith('v'):
                latest_version = latest_version[1:]
                
            # Check if this is a newer version
            if not self._is_newer_version(latest_version):
                logging.info(f"Current version {self.current_version} is up to date")
                return False
                
            # Find download URL for executable
            download_url = None
            for asset in latest_release['assets']:
                if asset['name'].endswith('.exe'):
                    download_url = asset['browser_download_url']
                    break
                    
            release_url = latest_release.get('html_url', download_url)
            
            # Show notification to user
            if parent_window:
                result = messagebox.askyesno(
                    f"{self.app_name} Update Available",
                    f"A new version of {self.app_name} is available!\n\n"
                    f"Current version: {self.current_version}\n"
                    f"New version: {latest_version}\n\n"
                    f"Would you like to download the update now?",
                    parent=parent_window
                )
                
                if result and (release_url or download_url):
                    webbrowser.open(release_url or download_url)
                    messagebox.showinfo(
                        "Update Instructions",
                        "The download page has been opened in your browser.\n\n"
                        "To install the update:\n"
                        "1. Download the new version\n"
                        "2. Close this application\n"
                        "3. Install or extract the new version\n"
                        "4. Run the updated application",
                        parent=parent_window
                    )
            
            return True
            
        except Exception as e:
            logging.error(f"Error checking for updates: {e}")
            return False