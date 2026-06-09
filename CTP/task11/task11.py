import time
import threading
from time import sleep
import busio
from board import SCL, SDA
from gpiozero import DistanceSensor
from adafruit_pca9685 import PCA9685
import warnings
from adafruit_motor import motor

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

robot_motor = SmoothMotor(m)

running = True

def background_task():
    global running

    while running:
        robot_motor.update_speed()
        sleep(0.05)