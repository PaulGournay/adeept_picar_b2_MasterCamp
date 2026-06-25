import cv2
from picamera2 import Picamera2
import numpy as np

import busio
from board import SCL, SDA
from adafruit_pca9685 import PCA9685
from board import SCL, SDA
import busio
from adafruit_motor import motor
from servo import Servo

from smooth_motor import SmoothMotor

MOTOR_M1_IN1 = 15
MOTOR_M1_IN2 = 14

#def setup():
i2c = busio.I2C(SCL, SDA)
# Create a simple PCA9685 class instance.
#  pwm_motor.channels[7].duty_cycle = 0xFFFF
pwm_motor = PCA9685(i2c, address=0x5f) #default 0x40
pwm_motor.frequency = 50

direction = Servo(pwm_motor, 0, center=96, step=4)
cam1 = Servo(pwm_motor, 1, center=90, step=4)
cam2 = Servo(pwm_motor, 2, center=90, step=4)

cam1.angle = 0
cam2.angle = -20

m = motor.DCMotor(pwm_motor.channels[MOTOR_M1_IN1],pwm_motor.channels[MOTOR_M1_IN2])
m.decay_mode = (motor.SLOW_DECAY)

robot_motor = SmoothMotor(m, 3)

# Initialize OpenCV window
cv2.startWindowThread()

# Initialize Picamera2 and configure the camera
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}))
picam2.start()

robot_motor.stop()
input()
robot_motor.set_speed(70, 1)

try:
    while True:
        # Capture frame-by-frame
        img = picam2.capture_array()

        h, w, _ = img.shape

        img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        lower_red = np.array([0,150,150])
        upper_red = np.array([10,255,255])
        mask = cv2.inRange(img_hsv, lower_red, upper_red)

        points = []
        for y in range(h):
            xs = np.where(mask[y, :] > 0)[0]
            if len(xs) > 0:
                cx = int(np.mean(xs))
                points.append(cx)

        # for i in range(len(points) - 1):
        #     cv2.line(mask, points[i], points[i+1], 3)
        

        m = 0
        if len(points) > 0:
            m = np.mean(points)
        else:
            robot_motor.stop()

        deg = (m * 70 / w) - 35
    
        print(m, deg)

        # cv2.imshow("Line tracker", mask)

        direction.angle = -1 * deg

        # Break the loop if 'q' is pressed
        # if cv2.waitKey(1) & 0xFF == ord('q'):
        #     break
except:
    # Release the camera and close windows
    cv2.destroyAllWindows()
    robot_motor.stop()