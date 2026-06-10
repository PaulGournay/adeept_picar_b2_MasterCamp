import time
import threading
from time import sleep
import busio
from board import SCL, SDA
from gpiozero import DistanceSensor
from adafruit_pca9685 import PCA9685
import warnings
from adafruit_motor import motor
from adafruit_motor import servo
from gpiozero import InputDevice

line_pin_left = 22
line_pin_middle = 27
line_pin_right = 17

left = InputDevice(pin=line_pin_right)
middle = InputDevice(pin=line_pin_middle)
right = InputDevice(pin=line_pin_left)

# Masque les avertissements inutiles de gpiozero
warnings.filterwarnings("ignore")

from smooth_motor import SmoothMotor


MOTOR_M1_IN1 = 15
MOTOR_M1_IN2 = 14

#def setup():
i2c = busio.I2C(SCL, SDA)
# Create a simple PCA9685 class instance.
#  pwm_motor.channels[7].duty_cycle = 0xFFFF
pwm_motor = PCA9685(i2c, address=0x5f) #default 0x40
pwm_motor.frequency = 50

m = motor.DCMotor(pwm_motor.channels[MOTOR_M1_IN1],pwm_motor.channels[MOTOR_M1_IN2])
m.decay_mode = (motor.SLOW_DECAY)

robot_motor = SmoothMotor(m, 1)

running = True
status = 0

def set_angle(angle):
    servo_angle = servo.Servo(pwm_motor.channels[0], min_pulse=500, max_pulse=2400,actuation_range=180)
    servo_angle.angle = angle

def background_task():
    global running

    while running:
        if status == 1:
            status_right = right.value
            status_middle = middle.value
            status_left = left.value
            # print('left: %d   middle: %d   right: %d' %(status_right,status_middle,status_left))
            if status_left == 1 and status_middle == 1 and status_right == 0:
                set_angle(75)
            if status_left == 1 and status_middle == 0 and status_right == 0:
                set_angle(55)
            if status_right == 1 and status_middle == 1 and status_left == 0:
                set_angle(105)
            if status_right == 1 and status_middle == 0 and status_left == 0:
                set_angle(125)
            if status_right == 0 and status_middle == 1 and status_left == 0:
                set_angle(90)
            if status_right == 1 and status_middle == 1 and status_left == 1:
                set_angle(90)
            if status_right == 0 and status_middle == 0 and status_left == 0:
                robot_motor.accelerate_to(50, -1)
                set_angle(90)
            else:
                robot_motor.accelerate_to(40, 1)
        else:
            robot_motor.accelerate_to(0, 1)
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
            if choice == 'A':
                status = 0
    except KeyboardInterrupt:
        running = False
        robot_motor.stop()
        robot_motor.destroy()
        print("Exit")


