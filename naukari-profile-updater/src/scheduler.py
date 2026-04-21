"""
Scheduler for running the Naukari automator at scheduled times
Supports both local cron and GCP Cloud Scheduler
"""

import logging
import schedule
import time
from datetime import datetime
from typing import Optional, Callable
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class LocalScheduler:
    """Local scheduler using the schedule library"""
    
    def __init__(self, run_time: str = "10:30"):
        """
        Initialize scheduler
        
        Args:
            run_time: Time to run in HH:MM format (default: 10:30)
        """
        self.run_time = run_time
        self.job = None
        self.is_running = False
    
    def schedule_daily_task(self, task: Callable, task_name: str = "Naukari Update"):
        """
        Schedule a task to run daily at specified time
        
        Args:
            task: Callable function to execute
            task_name: Name of the task for logging
        """
        try:
            self.job = schedule.every().day.at(self.run_time).do(
                self._execute_task, task, task_name
            )
            logger.info(f"Task '{task_name}' scheduled for {self.run_time} daily")
        except Exception as e:
            logger.error(f"Failed to schedule task: {e}")
            raise
    
    def _execute_task(self, task: Callable, task_name: str):
        """
        Execute the scheduled task with error handling
        
        Args:
            task: Callable function to execute
            task_name: Name of the task
        """
        try:
            logger.info(f"Executing scheduled task: {task_name}")
            start_time = datetime.now()
            
            result = task()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"Task '{task_name}' completed in {duration:.2f}s")
            logger.info(f"Result: {json.dumps(result, indent=2)}")
            
            # Save execution log
            self._save_execution_log(task_name, result, duration)
            
        except Exception as e:
            logger.error(f"Task '{task_name}' failed: {e}")
            self._save_execution_log(task_name, {'error': str(e)}, -1)
    
    def _save_execution_log(self, task_name: str, result: dict, duration: float):
        """
        Save execution log to file
        
        Args:
            task_name: Name of the task
            result: Task result
            duration: Execution duration in seconds
        """
        try:
            log_file = Path('logs/execution_history.json')
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            logs = []
            if log_file.exists():
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'task_name': task_name,
                'duration_seconds': duration,
                'result': result
            }
            
            logs.append(log_entry)
            
            # Keep only last 100 executions
            logs = logs[-100:]
            
            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to save execution log: {e}")
    
    def start(self):
        """Start the scheduler - runs indefinitely"""
        if not self.job:
            raise ValueError("No job scheduled. Call schedule_daily_task() first.")
        
        self.is_running = True
        logger.info("Scheduler started - waiting for tasks...")
        
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
            self.stop()
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            self.stop()
    
    def stop(self):
        """Stop the scheduler"""
        self.is_running = False
        logger.info("Scheduler stopped")


class GCPCloudScheduler:
    """Helper class for GCP Cloud Scheduler integration"""
    
    @staticmethod
    def get_setup_commands(project_id: str, location: str = "us-central1", schedule_time: str = "30 10 * * *"):
        """
        Get gcloud commands to set up Cloud Scheduler job
        
        Args:
            project_id: GCP project ID
            location: GCP region (default: us-central1)
            schedule_time: Cron expression (default: 10:30 AM daily in UTC)
            
        Returns:
            list: List of gcloud commands to run
        """
        commands = [
            "# Create Cloud Scheduler job that triggers Cloud Function",
            f"gcloud scheduler jobs create pubsub naukari-profile-update \\",
            f"  --schedule='{schedule_time}' \\",
            f"  --topic=naukari-update-trigger \\",
            f"  --message-body='{{\"action\": \"update_profile\"}}' \\",
            f"  --location={location} \\",
            f"  --project={project_id}",
            "",
            "# OR use HTTP trigger if using Cloud Functions HTTP endpoint:",
            f"gcloud scheduler jobs create http naukari-profile-update \\",
            f"  --schedule='{schedule_time}' \\",
            f"  --uri=https://{location}-{project_id}.cloudfunctions.net/naukari-updater \\",
            f"  --http-method=POST \\",
            f"  --location={location} \\",
            f"  --project={project_id}"
        ]
        return commands


def run_local_scheduler():
    """Example of running local scheduler"""
    from naukari_automator import NaukariAutomator
    from config.settings import get_credentials, get_config
    
    # Load configuration
    username, password = get_credentials()
    config = get_config()
    
    # Create automator
    automator = NaukariAutomator(
        username=username,
        password=password,
        headless=config.get('headless', True),
        debug=config.get('debug', False)
    )
    
    # Create scheduler
    scheduler = LocalScheduler(run_time="10:30")
    
    # Schedule the task
    scheduler.schedule_daily_task(
        task=automator.run,
        task_name="Naukari Profile Update"
    )
    
    # Start scheduler (runs indefinitely)
    scheduler.start()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # For testing, show GCP commands
    print("GCP Cloud Scheduler Setup Commands:")
    print("\n".join(GCPCloudScheduler.get_setup_commands(
        project_id="your-gcp-project-id"
    )))
