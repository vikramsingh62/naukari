#!/usr/bin/env python3
"""
Entry point script - Run this to execute the Naukari Profile Updater
Usage: python run.py [--debug] [--no-headless] [--schedule]
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def main():
    parser = argparse.ArgumentParser(
        description='Naukari Profile Auto-Updater'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode (screenshots, verbose logging)'
    )
    parser.add_argument(
        '--no-headless',
        action='store_true',
        help='Show browser window (for testing)'
    )
    parser.add_argument(
        '--schedule',
        action='store_true',
        help='Run scheduler (continuous, runs daily at 10:30 AM)'
    )
    parser.add_argument(
        '--time',
        default='10:30',
        help='Schedule time in HH:MM format (default: 10:30)'
    )
    
    args = parser.parse_args()
    
    try:
        if args.schedule:
            # Run scheduler
            from src.scheduler import LocalScheduler
            from src.naukari_automator import NaukariAutomator
            from config.settings import get_credentials, get_config
            
            print(f"Starting scheduler (will run at {args.time} daily)...")
            
            username, password = get_credentials()
            config = get_config()
            
            automator = NaukariAutomator(
                username=username,
                password=password,
                headless=not args.no_headless,
                debug=args.debug
            )
            
            scheduler = LocalScheduler(run_time=args.time)
            scheduler.schedule_daily_task(
                task=automator.run,
                task_name="Naukari Profile Update"
            )
            scheduler.start()
            
        else:
            # Run once
            from src.naukari_automator import NaukariAutomator
            from config.settings import get_credentials, get_config
            
            print("Running Naukari Profile Auto-Updater...")
            
            username, password = get_credentials()
            config = get_config()
            
            # Override config with command line args
            if args.debug:
                config['debug'] = True
            if args.no_headless:
                config['headless'] = False
            
            automator = NaukariAutomator(
                username=username,
                password=password,
                headless=config.get('headless', True),
                debug=config.get('debug', False)
            )
            
            result = automator.run()
            
            # Print summary
            print("\n" + "="*50)
            if result.get('success'):
                print("✅ SUCCESS: Profile updated successfully")
                if result.get('updates'):
                    print(f"  Updates made: {len(result['updates'])}")
            else:
                print("❌ FAILED: " + result.get('error', 'Unknown error'))
            print("="*50)
            
            sys.exit(0 if result.get('success') else 1)
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
