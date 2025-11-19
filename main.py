#!/usr/bin/env python3
"""
Robot Launcher
Simple script to start the robot system
"""

from robot import Robot
import signal
import sys

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\nShutdown signal received...")
    if robot:
        robot.close()
    sys.exit(0)

if __name__ == "__main__":
    robot = None
    
    try:
        print("=" * 50)
        print("  ROBOT STARTUP SEQUENCE")
        print("=" * 50)
        
        # Create robot instance
        robot = Robot()
        
        # Register signal handler for Ctrl+C
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start robot
        robot.start()
        
        print("\n✓ Robot is now running!")
        print("  Commands: happy, sad, angry, surprise, fear, status, quit")
        print("  Press Ctrl+C to shutdown\n")
        
        # Keep main thread alive
        while robot.running:
            import time
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\nKeyboard interrupt received...")
        if robot:
            robot.close()
            
    except Exception as e:
        print(f"\n✗ Error starting robot: {e}")
        import traceback
        traceback.print_exc()
        if robot:
            robot.close()
        sys.exit(1)
    
    finally:
        print("\nRobot shutdown complete. Goodbye!")