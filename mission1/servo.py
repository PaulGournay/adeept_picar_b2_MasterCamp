from adafruit_motor import servo as AdafruitServo
from adafruit_pca9685 import PCA9685

i2c = busio.I2C(SCL, SDA)
pca = PCA9685(i2c, address=0x5f)
pca.frequency = 50

class Servo:
    def __init__(self, pca, id, center=90, step=5):
        self.servo = AdafruitServo.Servo(pca.channels[id], min_pulse=500, max_pulse=2400, actuation_range=180)
        self._angle = 0
        self.target_angle = 0
        self.center = center
        self.real_angle = center
        self.servo.angle = center
        self.step = step
    
    def get_angle(self):
        return self._angle
    
    def set_angle(self, a):
        self._angle = a
        self.real_angle = a + self.center
        self.servo.angle = self.real_angle
    
    def go_to_angle(self, a):
        self.target_angle = a
    
    def update_angle(self):
        if self.angle > self.target_angle:
            self.angle = max(self.target_angle, self.angle + self.step)
        
        if self.angle < self.target_angle:
            self.angle = min(self.target_angle, self.angle + self.step)

    angle = property(get_angle, set_angle)

