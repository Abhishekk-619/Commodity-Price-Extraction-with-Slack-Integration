"""
Slack Notification System for Commodity Price Scrapers
=====================================================

This module provides simple Slack notifications for scraper success/failure.
Only requires inserting your Slack webhook URL to work.

Usage:
    from slack_notifier import SlackNotifier
    
    notifier = SlackNotifier()
    notifier.send_success("EGG SCRAPER")
    notifier.send_error("COPRA SCRAPER")
"""

import requests
import json
import os
from datetime import datetime
from typing import Optional


class SlackNotifier:
    """Simple Slack notifier for scraper status updates"""
    
    def __init__(self, webhook_url: Optional[str] = None):
        """
        Initialize Slack notifier
        
        Args:
            webhook_url: Slack webhook URL. If None, will try to get from environment
        """
        # Try to get webhook URL from parameter, environment, or use placeholder
        self.webhook_url = (
            webhook_url or 
            os.getenv('SLACK_WEBHOOK_URL') or 
            "INSERT_YOUR_WEBHOOK_URL_HERE"
        )
        
        # Check if webhook URL is properly configured
        self.is_configured = (
            self.webhook_url and 
            self.webhook_url != "INSERT_YOUR_WEBHOOK_URL_HERE" and
            self.webhook_url.startswith('https://hooks.slack.com/')
        )
        
        if not self.is_configured:
            print("⚠️ Slack webhook URL not configured. Notifications will be printed to console.")
    
    def send_success(self, scraper_name: str) -> bool:
        """
        Send success notification to Slack
        
        Args:
            scraper_name: Name of the scraper (e.g., "EGG SCRAPER")
            
        Returns:
            bool: True if notification sent successfully, False otherwise
        """
        message = f"✅ SUCCESSFULLY SCRAPED PRICES FOR {scraper_name.upper()}"
        return self._send_notification(message, "good")
    
    def send_error(self, scraper_name: str) -> bool:
        """
        Send error notification to Slack
        
        Args:
            scraper_name: Name of the scraper (e.g., "EGG SCRAPER")
            
        Returns:
            bool: True if notification sent successfully, False otherwise
        """
        message = f"🚨 ERROR SCRAPING PRICES FOR {scraper_name.upper()}"
        return self._send_notification(message, "danger")
    
    def _send_notification(self, message: str, color: str) -> bool:
        """
        Internal method to send notification to Slack
        
        Args:
            message: Message to send
            color: Color for the attachment (good, warning, danger)
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        # If not configured, print to console instead
        if not self.is_configured:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] SLACK: {message}")
            return True
        
        # Prepare Slack payload
        payload = {
            "attachments": [
                {
                    "color": color,
                    "text": message,
                    "ts": datetime.now().timestamp(),
                    "footer": "Commodity Price Scraper",
                    "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png"
                }
            ]
        }
        
        try:
            # Send to Slack with timeout
            response = requests.post(
                self.webhook_url, 
                json=payload, 
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            
            # Check if request was successful
            if response.status_code == 200:
                return True
            else:
                print(f"⚠️ Slack notification failed: HTTP {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            print("⚠️ Slack notification timed out")
            return False
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Slack notification failed: {e}")
            return False
        except Exception as e:
            print(f"⚠️ Unexpected error sending Slack notification: {e}")
            return False


# Global notifier instance for easy import
notifier = SlackNotifier()


def send_success(scraper_name: str) -> bool:
    """Convenience function to send success notification"""
    return notifier.send_success(scraper_name)


def send_error(scraper_name: str) -> bool:
    """Convenience function to send error notification"""
    return notifier.send_error(scraper_name)


# Test function
def test_notifications():
    """Test function to verify Slack notifications work"""
    print("Testing Slack notifications...")
    print("1. Testing success notification...")
    send_success("TEST SCRAPER")
    
    print("2. Testing error notification...")
    send_error("TEST SCRAPER")
    
    print("Test completed!")


if __name__ == "__main__":
    test_notifications()
