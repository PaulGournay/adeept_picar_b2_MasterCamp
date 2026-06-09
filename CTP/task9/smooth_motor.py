#!/usr/bin/env/python3
from board import SCL, SDA
import busio
from adafruit_pca9685 import PCA9685
from adafruit_motor import motor


MOTOR_M1_IN1 =  15      #Define the positive pole of M1
MOTOR_M1_IN2 =  14      #Define the negative pole of M1

def map(x,in_min,in_max,out_min,out_max):
  return (x - in_min)/(in_max - in_min) *(out_max - out_min) +out_min


#def setup():
i2c = busio.I2C(SCL, SDA)
# Create a simple PCA9685 class instance.
#  pwm_motor.channels[7].duty_cycle = 0xFFFF
pwm_motor = PCA9685(i2c, address=0x5f) #default 0x40
pwm_motor.frequency = 50

class SmoothMotor:
    def __init__(self, MOTOR_M1_IN1, MOTOR_M1_IN2):
        self.speed = 0
        self.target_speed = 0
        self.direction = 1
        self.motor = motor.DCMotor(pwm_motor.channels[MOTOR_M1_IN1],pwm_motor.channels[MOTOR_M1_IN2])
        self.motor.decay_mode = (motor.SLOW_DECAY)

    def stop(self):
        self.motor.throttle = 0

    def accelerate_to(self, speed, direction):
        if direction != -1 and direction != 1:
            direction = 1
        if speed > 100:
            speed = 100
        if speed < 0:
            speed = 0
        self.target_speed = speed * direction

    def set_speed(self, speed, direction):
        if direction != -1 and direction != 1:
            direction = 1
        if speed > 100:
            speed = 100
        if speed < 0:
            speed = 0
        self.direction = direction
        self.target_speed = speed * direction
        self._set_speed_real(speed * direction)
    
    def _set_speed_real(self, speed):
        self.speed = speed
        self.motor.throttle = self.speed / 100

    def destroy(self):
        self.stop()
        pwm_motor.deinit()

    def update_speed(self):
        if self.speed < self.target_speed:
            self._set_speed_real(self.speed + 1)
        elif self.speed > self.target_speed:
            self._set_speed_real(self.speed - 1)