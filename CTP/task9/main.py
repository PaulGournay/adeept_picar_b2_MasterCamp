from gpiozero import DistanceSensor
from time import sleep
import time
from board import SCL, SDA
import busio
from adafruit_pca9685 import PCA9685
from adafruit_motor import motor

Tr = 23
Ec = 24
sensor = DistanceSensor(echo=Ec, trigger=Tr,max_distance=2) # Maximum detection distance 2m.

# motor_EN_A: Pin7  |  motor_EN_B: Pin11
# motor_A:  Pin8,Pin10    |  motor_B: Pin13,Pin12

vitesse = 0

MOTOR_M1_IN1 =  15      #Define the positive pole of M1
MOTOR_M1_IN2 =  14      #Define the negative pole of M1

Dir_forward   = 0
Dir_backward  = 1

left_forward  = 1
left_backward = 0

right_forward = 0
right_backward= 1

pwn_A = 0
pwm_B = 0
  
def map(x,in_min,in_max,out_min,out_max):
  return (x - in_min)/(in_max - in_min) *(out_max - out_min) +out_min


#def setup():
i2c = busio.I2C(SCL, SDA)
# Create a simple PCA9685 class instance.
#  pwm_motor.channels[7].duty_cycle = 0xFFFF
pwm_motor = PCA9685(i2c, address=0x5f) #default 0x40
pwm_motor.frequency = 50

motor1 = motor.DCMotor(pwm_motor.channels[MOTOR_M1_IN1],pwm_motor.channels[MOTOR_M1_IN2] )
motor1.decay_mode = (motor.SLOW_DECAY)
#  motorStop()


def motorStop():#Motor stops
    motor1.throttle = 0

def destroy():
  motorStop()
  pwm_motor.deinit()


def getToSpeed(goalSpeed, direction, duration):
    global vitesse                             # Utilisé par le fonction Motor
    if direction == -1:
        goalSpeed = -1 * goalSpeed
    delta = (goalSpeed - vitesse) / 100
    for i in range(100):
        vitesse += delta
        speed = map(vitesse, 0, 100, 0, 1.0)
        motor1.throttle = speed
        sleep(duration / 100)

# Get the distance of ultrasonic detection.
def checkdist():
    return (sensor.distance) *100 # Unit: cm

if __name__ == '__main__':
  try:
    chann =  1
    
    while True:
        distance = checkdist()
        if distance > 50:
            getToSpeed(50,1,0.5)
        else:
            getToSpeed(0,1,0.5)
  except KeyboardInterrupt:
    destroy()
