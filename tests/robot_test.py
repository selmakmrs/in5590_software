from robot import Robot

robot = Robot()

try:
    robot.start()          # Main loop or initialization
except KeyboardInterrupt:  # When you press Ctrl+C
    pass                   # Skip the error message
finally:
    robot.close()          # Always runs — even if interrupted or an error occurs
