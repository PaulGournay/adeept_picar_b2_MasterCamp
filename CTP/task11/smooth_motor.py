def map(x,in_min,in_max,out_min,out_max):
  return (x - in_min)/(in_max - in_min) *(out_max - out_min) +out_min

class SmoothMotor:
    def __init__(self, motor, acceleration = 1):
        self.speed = 0
        self.target_speed = 0
        self.direction = 1
        self.motor = motor
        self.acceleration = acceleration
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
        self._set_speed_immediate(speed * direction)
    
    def _set_speed_immediate(self, speed):
        self.speed = speed
        self.motor.throttle = self.speed / 100

    def destroy(self):
        self.stop()
        
    def update_speed(self):
        if self.speed < self.target_speed:
            self._set_speed_real(self.speed + self.acceleration)
        elif self.speed > self.target_speed:
            self._set_speed_real(self.speed - self.acceleration)