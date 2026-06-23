"""
FINESE2 - Hugging Face Spaces Keep-Alive Utility
Prevents HF Space from sleeping by periodic health check pings.
"""
import requests
import time
import os
import logging

logger = logging.getLogger(__name__)


def start_keep_alive():
    """
    Start keep-alive pinging to prevent Hugging Face Space from sleeping.
    
    Hugging Face Spaces put apps to sleep after 48 hours of inactivity.
    This function pings the health endpoint every 25 minutes to keep the space awake.
    """
    # Get the space host URL
    space_host = os.environ.get('SPACE_HOST', 'http://localhost:7860')
    
    logger.info(f"Starting keep-alive pings to {space_host}")
    
    ping_count = 0
    
    while True:
        try:
            # Ping the health endpoint
            response = requests.get(
                f"{space_host}/health",
                timeout=10,
                headers={'User-Agent': 'FINESE2-KeepAlive/1.0'}
            )
            
            if response.status_code == 200:
                ping_count += 1
                logger.debug(f"Keep-alive ping #{ping_count} successful")
                
                # Log summary every 10 pings (every ~4 hours)
                if ping_count % 10 == 0:
                    logger.info(f"Keep-alive: {ping_count} pings sent successfully")
            else:
                logger.warning(f"Keep-alive ping returned status {response.status_code}")
                
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Keep-alive connection error: {e}")
        except requests.exceptions.Timeout as e:
            logger.warning(f"Keep-alive timeout: {e}")
        except Exception as e:
            logger.error(f"Keep-alive ping failed: {type(e).__name__}: {e}")
        
        # Sleep for 25 minutes (1500 seconds) before next ping
        # This is well under the 48-hour inactivity limit
        time.sleep(1500)


if __name__ == '__main__':
    # Test the keep-alive function
    print("Testing keep-alive function...")
    print("This will ping the health endpoint once and exit.")
    
    space_host = os.environ.get('SPACE_HOST', 'http://localhost:7860')
    try:
        response = requests.get(f"{space_host}/health", timeout=10)
        print(f"Health check response: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
