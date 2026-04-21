"""
Naukari Profile Auto-Updater
Automated script to update profile punctuation on naukari.com daily
"""

import logging
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from typing import Optional
import os
import json
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/naukari_updater.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class NaukariAutomator:
    """Automates profile updates on naukari.com"""
    
    BASE_URL = "https://www.naukri.com"
    HOME_PAGE = BASE_URL
    PROFILE_PAGE = f"{BASE_URL}/mnjuser/profile"
    
    def __init__(self, username: str, password: str, headless: bool = True, debug: bool = False):
        """
        Initialize the automator
        
        Args:
            username: Naukari username/email
            password: Naukari password
            headless: Run browser in headless mode (True for production)
            debug: Enable debug logging and screenshots
        """
        self.username = username
        self.password = password
        self.headless = headless
        self.debug = debug
        self.playwright = None
        self.browser = None
        self.page = None
        
    def start(self):
        """Start the playwright browser"""
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=self.headless)
            logger.info("Browser started successfully")
        except Exception as e:
            logger.error(f"Failed to start browser: {e}")
            raise
    
    def stop(self):
        """Stop the playwright browser"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        logger.info("Browser stopped")
    
    def login(self) -> bool:
        """
        Login to Naukari with correct flow:
        1. Go to naukri.com
        2. Click on Jobseeker Login button
        3. Enter email/username
        4. Enter password
        5. Click login
        
        Returns:
            bool: True if login successful, False otherwise
        """
        try:
            logger.info("Starting login process...")
            self.page = self.browser.new_page()
            self.page.set_viewport_size({"width": 1920, "height": 1080})
            
            # Step 1: Navigate to home page
            self.page.goto(self.HOME_PAGE, wait_until="networkidle")
            logger.info("Navigated to naukri.com")
            
            if self.debug:
                self.page.screenshot(path="logs/01_home_page.png")
            
            # Step 2: Click on Jobseeker Login button
            logger.info("Looking for Jobseeker Login button...")
            try:
                jobseeker_login = self.page.locator("//*[@title='Jobseeker Login']").first
                jobseeker_login.click()
                logger.info("Jobseeker Login button clicked")
                self.page.wait_for_timeout(2000)  # Wait for login modal/page to load
            except Exception as e:
                logger.error(f"Failed to click Jobseeker Login button: {e}")
                if self.debug:
                    self.page.screenshot(path="logs/error_jobseeker_login_button.png")
                return False
            
            if self.debug:
                self.page.screenshot(path="logs/02_after_jobseeker_click.png")
            
            # Step 3: Fill username field
            logger.info("Entering username...")
            try:
                username_field = self.page.locator("//*[@placeholder='Enter your active Email ID / Username']").first
                username_field.fill(self.username)
                logger.info("Username entered")
            except Exception as e:
                logger.error(f"Failed to fill username field: {e}")
                if self.debug:
                    self.page.screenshot(path="logs/error_username_field.png")
                return False
            
            # Step 4: Fill password field
            logger.info("Entering password...")
            try:
                password_field = self.page.locator("//*[@placeholder='Enter your password']").first
                password_field.fill(self.password)
                logger.info("Password entered")
            except Exception as e:
                logger.error(f"Failed to fill password field: {e}")
                if self.debug:
                    self.page.screenshot(path="logs/error_password_field.png")
                return False
            
            if self.debug:
                self.page.screenshot(path="logs/03_credentials_filled.png")
            
            # Step 5: Click login button
            logger.info("Clicking login button...")
            try:
                login_button = self.page.locator("button:has-text('Login'), button:has-text('Sign In')").first
                login_button.click()
                logger.info("Login button clicked")
            except Exception as e:
                logger.error(f"Failed to click login button: {e}")
                if self.debug:
                    self.page.screenshot(path="logs/error_login_button.png")
                return False
            
            # Wait for navigation to complete (allow time for potential OTP/2FA)
            try:
                self.page.wait_for_url("**/mnjuser/**", wait_until="domcontentloaded", timeout=10000)
                logger.info("Login successful - redirected to dashboard")
            except PlaywrightTimeoutError:
                # If URL didn't change to mnjuser, we might be on OTP page or still on login
                # Check if we're still on login page
                current_url = self.page.url
                if "mnjuser" in current_url or "applicant" in current_url:
                    logger.info("Login successful - authenticated")
                elif "/login" in current_url or "naukri.com" in current_url:
                    logger.error("Still on login/naukri.com page - login might have failed")
                    logger.error(f"Current URL: {current_url}")
                    if self.debug:
                        self.page.screenshot(path="logs/error_after_login_attempt.png")
                    return False
            
            if self.debug:
                self.page.screenshot(path="logs/04_after_login.png")
            
            return True
            
        except PlaywrightTimeoutError as e:
            logger.error(f"Login timeout: {e}")
            if self.debug:
                self.page.screenshot(path="logs/error_login_timeout.png")
            return False
        except Exception as e:
            logger.error(f"Login failed: {e}")
            if self.debug and self.page:
                self.page.screenshot(path="logs/error_login.png")
            return False
    
    def navigate_to_profile(self) -> bool:
        """
        Navigate to the view profile page by clicking on profile menu/link
        
        Returns:
            bool: True if navigation successful, False otherwise
        """
        try:
            logger.info("Navigating to profile page...")
            
            # Method 1: Look for profile link by text
            try:
                logger.info("Looking for profile link/button...")
                # Try clicking on profile menu/link
                profile_locators = [
                    self.page.locator("a:has-text('My Profile')"),
                    self.page.locator("a:has-text('profile')"),
                    self.page.locator("[aria-label*='Profile' i]"),
                    self.page.locator("//a[contains(@href, 'profile')]").first,
                    self.page.locator("//button[contains(text(), 'Profile')]").first,
                ]
                
                for locator in profile_locators:
                    try:
                        if locator.count() > 0 or locator.is_visible():
                            locator.click()
                            logger.info("Clicked on profile link")
                            self.page.wait_for_timeout(2000)  # Wait for page load
                            break
                    except:
                        continue
                
                if self.debug:
                    self.page.screenshot(path="logs/03_profile_page.png")
                
                return True
                
            except Exception as e:
                logger.warning(f"Failed to click profile link: {e}")
                
                # Method 2: Direct URL navigation with more lenient timeout
                try:
                    logger.info("Trying direct URL navigation to profile...")
                    self.page.goto(self.PROFILE_PAGE, wait_until="domcontentloaded", timeout=15000)
                    logger.info("Navigated to profile page via URL")
                    
                    if self.debug:
                        self.page.screenshot(path="logs/03_profile_page.png")
                    
                    return True
                except Exception as e2:
                    logger.error(f"Direct URL navigation also failed: {e2}")
                    
                    if self.debug and self.page:
                        self.page.screenshot(path="logs/error_profile_nav.png")
                    
                    return False
                    
        except Exception as e:
            logger.error(f"Profile navigation failed: {e}")
            if self.debug and self.page:
                self.page.screenshot(path="logs/error_profile_nav_outer.png")
            return False
    
    def check_and_update_profile(self) -> Optional[dict]:
        """
        Check profile for full stop and update if needed
        
        Returns:
            dict: Update status with details, None if failed
        """
        try:
            logger.info("Starting profile check and update...")
            
            # Wait for profile content to load
            # self.page.wait_for_selector("text=View Profile, text=profile", timeout=5000)
            
            # Get profile text - adjust selector based on actual Naukari structure
            profile_sections = self.page.query_selector_all("#lazyResumeHead .prefill.typ-14Medium > div")
            
            updates_made = []
            
            for idx, section in enumerate(profile_sections):
                try:
                    # Get text content
                    text_content = section.text_content()
                    print(f"Section {idx} text: {text_content}")
                    if not text_content or len(text_content.strip()) < 5:
                        continue
                    
                    original_text = text_content.strip()
                    logger.debug(f"Section {idx}: {original_text[:100]}...")
                    
                    # Check if text ends with full stop
                    if original_text.endswith('.'):
                        logger.info(f"Full stop found at end of section {idx}, removing...")
                        updated_text = original_text[:-1]
                    else:
                        logger.info(f"Full stop NOT found at end of section {idx}, adding...")
                        updated_text = original_text + '.'
                    
                    self.page.locator("#lazyResumeHead .widgetHead .edit.icon").click()
                    # Find editable field
                    editable_field = self.page.locator("#resumeHeadlineTxt")
                    
                    if editable_field:
                        # Clear and update
                        editable_field.fill(updated_text) if hasattr(editable_field, 'fill') else editable_field.click()
                        logger.info(f"Section {idx} updated successfully")
                        
                        updates_made.append({
                            'section': idx,
                            'original': original_text,
                            'updated': updated_text,
                            'action': 'removed_period' if original_text.endswith('.') else 'added_period'
                        })
                        
                except Exception as e:
                    logger.warning(f"Error processing section {idx}: {e}")
                    continue
            
            if self.debug:
                self.page.screenshot(path="logs/04_profile_updated.png")
            
            return {
                'success': len(updates_made) > 0,
                'updates': updates_made,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Profile check and update failed: {e}")
            if self.debug and self.page:
                self.page.screenshot(path="logs/error_profile_update.png")
            return None
    
    def save_profile(self) -> bool:
        """
        Save the updated profile
        
        Returns:
            bool: True if save successful, False otherwise
        """
        try:
            logger.info("Attempting to save profile...")
            
            # Look for save button
            save_button = self.page.query_selector(".action.s12 [type='submit']")
            
            if save_button:
                save_button.click()
                logger.info("Save button clicked")
                
                # Wait for save confirmation
                self.page.wait_for_timeout(2000)
                
                if self.debug:
                    self.page.screenshot(path="logs/05_profile_saved.png")
                
                logger.info("Profile saved successfully")
                return True
            else:
                logger.warning("Save button not found")
                return False
                
        except Exception as e:
            logger.error(f"Failed to save profile: {e}")
            if self.debug and self.page:
                self.page.screenshot(path="logs/error_save.png")
            return False
    
    def run(self) -> dict:
        """
        Execute the complete automation workflow
        
        Returns:
            dict: Execution status and results
        """
        try:
            start_time = datetime.now()
            logger.info("=" * 50)
            logger.info("Starting Naukari Profile Auto-Updater")
            logger.info("=" * 50)
            
            self.start()
            
            # Step 1: Login
            if not self.login():
                return {
                    'success': False,
                    'error': 'Login failed',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Step 2: Navigate to profile
            if not self.navigate_to_profile():
                return {
                    'success': False,
                    'error': 'Failed to navigate to profile',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Step 3: Check and update profile
            update_result = self.check_and_update_profile()
            if not update_result:
                return {
                    'success': False,
                    'error': 'Failed to check and update profile',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Step 4: Save profile
            save_success = self.save_profile()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            result = {
                'success': save_success,
                'updates': update_result.get('updates', []),
                'timestamp': datetime.now().isoformat(),
                'duration_seconds': duration
            }
            
            logger.info(f"Execution completed in {duration:.2f} seconds")
            logger.info("=" * 50)
            
            return result
            
        except Exception as e:
            logger.error(f"Automation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        finally:
            self.stop()


def main():
    """Main entry point"""
    from config.settings import get_credentials, get_config
    
    # Load credentials and config
    try:
        username, password = get_credentials()
        config = get_config()
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return
    
    # Create automator
    automator = NaukariAutomator(
        username=username,
        password=password,
        headless=config.get('headless', True),
        debug=config.get('debug', False)
    )
    
    # Run automation
    result = automator.run()
    
    # Log result
    logger.info(f"Final result: {json.dumps(result, indent=2)}")


if __name__ == "__main__":
    main()
