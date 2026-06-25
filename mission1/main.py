import time
import threading
from time import sleep
import busio
from board import SCL, SDA
from gpiozero import DistanceSensor
from adafruit_pca9685 import PCA9685
from board import SCL, SDA
import busio
from adafruit_motor import motor
from adafruit_motor import servo
from gpiozero import InputDevice
from gpiozero import PWMOutputDevice as PWM
from servo import Servo

from smooth_motor import SmoothMotor

line_pin_left = 22
line_pin_middle = 27
line_pin_right = 17

left = InputDevice(pin=line_pin_right)
middle = InputDevice(pin=line_pin_middle)
right = InputDevice(pin=line_pin_left)

MOTOR_M1_IN1 = 15
MOTOR_M1_IN2 = 14

#def setup():
i2c = busio.I2C(SCL, SDA)
# Create a simple PCA9685 class instance.
#  pwm_motor.channels[7].duty_cycle = 0xFFFF
pwm_motor = PCA9685(i2c, address=0x5f) #default 0x40
pwm_motor.frequency = 50

direction = Servo(pwm_motor, 0, center=96)

m = motor.DCMotor(pwm_motor.channels[MOTOR_M1_IN1],pwm_motor.channels[MOTOR_M1_IN2])
m.decay_mode = (motor.SLOW_DECAY)

robot_motor = SmoothMotor(m, 4)

Tr = 23
Ec = 24
sensor = DistanceSensor(echo=Ec, trigger=Tr,max_distance=2) # Maximum detection distance 2m.

# Get the distance of ultrasonic detection.
def checkdist():
    return (sensor.distance) *100 # Unit: cm

running = True
status = 0
steering = 0

def background_task():
    global running
    global steering
    global status

    angle1 = 15
    angle2 = 35
    basis_angle = 96

    while running:
        if status == 1:
            status_right = right.value
            status_middle = middle.value
            status_left = left.value
            # print('left: %d   middle: %d   right: %d' %(status_right,status_middle,status_left))
            if status_left == 1 and status_middle == 1 and status_right == 0:
                direction.go_to_angle(-angle1)
                steering = -1
                robot_motor.accelerate_to(20, 1, acceleration = 1)
            if status_left == 1 and status_middle == 0 and status_right == 0:
                direction.angle = -angle2
                direction.target_angle = direction.angle
                steering = -1
                robot_motor.accelerate_to(20, 1, acceleration = 1)
            if status_left == 0 and status_middle == 1 and status_right == 1:
                direction.go_to_angle(angle1)
                steering = 1
                robot_motor.accelerate_to(20, 1, acceleration = 1)
            if status_left == 0 and status_middle == 0 and status_right == 1:
                direction.angle = angle2
                direction.target_angle = direction.angle
                steering = 1
                robot_motor.accelerate_to(20, 1, acceleration = 1)
            if status_left == 0 and status_middle == 1 and status_left == 0:
                direction.angle = 0
                direction.target_angle = 0
                steering = 0
                robot_motor.accelerate_to(60, 1, acceleration = 5)
            if status_right == 1 and status_middle == 1 and status_left == 1:
                direction.angle = 0
                direction.target_angle = 0
                steering = 0
                robot_motor.accelerate_to(60, 1, acceleration = 5)
            if status_right == 0 and status_middle == 0 and status_left == 0:
                robot_motor.accelerate_to(30, -1, acceleration = 2)
                if -4 < robot_motor.speed < 4:
                    if steering == 0:
                        direction.angle = 0
                        direction.target_angle = 0
                    if steering == 1:
                        direction.angle = -angle1
                        direction.target_angle = -angle1
                    if steering == -1:
                        direction.angle = angle1
                        direction.target_angle = angle1
            
            if checkdist() <= 20:
                status = 0
        else:
            robot_motor.accelerate_to(0, 1, acceleration = 2)
        robot_motor.update_speed()
        direction.update_angle()
        sleep(0.05)

if __name__ == "__main__":
    bg_thread = threading.Thread(target=background_task, daemon=True)
    bg_thread.start()

    light_thread = threading.Thread(target=led_task, daemon=True)
    light_thread.start()
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


