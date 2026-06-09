#import RPi.GPIO as GPIO
from gpiozero import PWMOutputDevice as PWM, LED
import time

Left_R = 19
Left_G = 0
Left_B = 13

Right_R = 1
Right_G = 5
Right_B = 6

def setup():
  global L_R, L_G, L_B, R_R, R_G, R_B, L_1, L_2, L_3

  L_R = PWM(pin=Left_R, initial_value=1.0, frequency=2000)
  L_G = PWM(pin=Left_G, initial_value=1.0, frequency=2000)
  L_B = PWM(pin=Left_B, initial_value=1.0, frequency=2000)

  R_R = PWM(pin=Right_R, initial_value=1.0, frequency=2000)
  R_G = PWM(pin=Right_G, initial_value=1.0, frequency=2000)
  R_B = PWM(pin=Right_B, initial_value=1.0, frequency=2000)

  L_1 = LED(9)
  L_2 = LED(25)
  L_3 = LED(11)

def loop():
  while True:
    try:
      x = int(input("> "))
      if x == 11:
        L_1.on()
      if x == 12:
        L_2.on()
      if x == 13:
        L_3.on()
      if x == 21:
        L_1.off()
      if x == 22:
        L_2.off()
      if x == 23:
        L_3.off()
      if x == 14:
        L_R.value = 0.0
      if x == 15:
        L_G.value = 0.0
      if x == 16:
        L_B.value = 0.0
      if x == 17:
        R_R.value = 0.0
      if x == 18:
        R_G.value = 0.0
      if x == 19:
        R_B.value = 0.0
      if x == 24:
        L_R.value = 1.0
      if x == 25:
        L_G.value = 1.0
      if x == 26:
        L_B.value = 1.0
      if x == 27:
        R_R.value = 1.0
      if x == 28:
        R_G.value = 1.0
      if x == 29:
        R_B.value = 1.0
    except:
      pass

def destroy():
  L_1.stop()
  L_2.stop()
  L_3.stop()
  L_R.stop()
  L_G.stop()
  L_B.stop()
  R_R.stop()
  R_G.stop()
  R_B.stop()

if __name__ == "__main__":

  setup()
  try:
    loop()
  except KeyboardInterrupt:
    destroy()