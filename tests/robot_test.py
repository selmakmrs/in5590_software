from robot_v2 import Robot
import time

def main():
    robot = Robot()
    
    try:
        robot.start()
        
        # Keep main thread alive - otherwise daemon threads will exit immediately
        print("Robot running... Press Ctrl+C to stop")
        while robot.running:
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"\nError occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Cleaning up...")
        robot.close()
        print("Robot stopped successfully")

if __name__ == "__main__":
    main()