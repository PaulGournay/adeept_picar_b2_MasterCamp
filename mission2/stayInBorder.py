import time
import threading
from time import sleep
import busio
from board import SCL, SDA
from adafruit_pca9685 import PCA9685
import warnings
from adafruit_motor import motor
from adafruit_motor import servo
from gpiozero import InputDevice

from smooth_motor import SmoothMotor

MOTOR_M1_IN1 = 15
MOTOR_M1_IN2 = 14

warnings.filterwarnings("ignore")

i2c = busio.I2C(SCL, SDA)
pwm_motor = PCA9685(i2c, address=0x5f)
pwm_motor.frequency = 50

m = motor.DCMotor(pwm_motor.channels[MOTOR_M1_IN1], pwm_motor.channels[MOTOR_M1_IN2])
m.decay_mode = motor.SLOW_DECAY
robot_motor = SmoothMotor(m, 4)

line_pin_left   = 22
line_pin_middle = 27
line_pin_right  = 17

left   = InputDevice(pin=line_pin_right)
middle = InputDevice(pin=line_pin_middle)
right  = InputDevice(pin=line_pin_left)

running = True
status  = 0

def set_angle(ID, angle):
    servo_angle = servo.Servo(pwm_motor.channels[ID], min_pulse=500, max_pulse=2400, actuation_range=180)
    servo_angle.angle = angle

def turn_away_from_border(direction):

    if direction == 'left':
        set_angle(0, 125)               # steer right
    else:
        set_angle(0, 55)                # steer left
    robot_motor.accelerate_to(20, -1,2)       # reverse
    sleep(0.3)
    if direction == 'left':
        set_angle(0, 55)             
    else:
        set_angle(0, 125)     
    
    robot_motor.accelerate_to(20, 1,2)        # go forward in new direction
    sleep(0.3)
    set_angle(0, 90)                    # re-center

def background_task():
    global running, status

    while running:
        if status == 1:
            status_right  = right.value
            status_middle = middle.value
            status_left   = left.value

            if status_left == 1 and status_middle == 1:
                # border on the left, turn away right
                turn_away_from_border('left')
            elif status_right == 1 and status_middle == 1:
                # border on the right → turn away left
                turn_away_from_border('right')
            elif status_left == 1 and status_right == 1:
                # both sides hit, reverse straight
                turn_away_from_border('right')
            else:
                # all clear, go forward
                robot_motor.accelerate_to(40, 1, acceleration=5)

        else:
            robot_motor.accelerate_to(0, 1, acceleration=2)

        robot_motor.update_speed()
        sleep(0.05)

if __name__ == "__main__":
    bg_thread = threading.Thread(target=background_task, daemon=True)
    bg_thread.start()

    try:
        while True:
            choice = input("\nCommande (M/A) : ").strip().upper()
            if choice == 'M':
                status = 1
            elif choice == 'A':
                status = 0
    except KeyboardInterrupt:
        running = False
        robot_motor.stop()
        robot_motor.destroy()
        print("Exit")