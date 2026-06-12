import spidev
import threading
import numpy
import time

class Adeept_SPI_LedPixel(threading.Thread):
    def __init__(self, count=14, bright=255, sequence='GRB', bus=0, device=0, *args, **kwargs):
        self.set_led_type(sequence)
        self.set_led_count(count)
        self.set_led_brightness(bright)
        self.led_begin(bus, device)
        self._blinking = False 
        self.set_all_led_color(0, 0, 0)
        super(Adeept_SPI_LedPixel, self).__init__(*args, **kwargs)
        self.__flag = threading.Event()
        self.__flag.clear()

    def led_begin(self, bus=0, device=0):
        self.bus = bus
        self.device = device
        try:
            self.spi = spidev.SpiDev()
            self.spi.open(self.bus, self.device)
            self.spi.mode = 0
            self.led_init_state = 1
        except OSError:
            print("SPI not available, check your configuration.")
            self.led_init_state = 0

    def set_led_count(self, count):
        self.led_count = count
        self.led_color = [0, 0, 0] * self.led_count
        self.led_original_color = [0, 0, 0] * self.led_count

    def set_led_type(self, rgb_type):
        try:
            led_type = ['RGB','RBG','GRB','GBR','BRG','BGR']
            led_type_offset = [0x06,0x09,0x12,0x21,0x18,0x24]
            index = led_type.index(rgb_type)
            self.led_red_offset   = (led_type_offset[index] >> 4) & 0x03
            self.led_green_offset = (led_type_offset[index] >> 2) & 0x03
            self.led_blue_offset  = (led_type_offset[index] >> 0) & 0x03
        except ValueError:
            self.led_red_offset   = 1
            self.led_green_offset = 0
            self.led_blue_offset  = 2

    def set_led_brightness(self, brightness):
        self.led_brightness = brightness
        for i in range(self.led_count):
            self.set_led_rgb_data(i, self.led_original_color[i*3:i*3+3])

    def set_ledpixel(self, index, r, g, b):
        p = [0, 0, 0]
        p[self.led_red_offset]   = round(r * self.led_brightness / 255)
        p[self.led_green_offset] = round(g * self.led_brightness / 255)
        p[self.led_blue_offset]  = round(b * self.led_brightness / 255)
        self.led_original_color[index*3 + self.led_red_offset]   = r
        self.led_original_color[index*3 + self.led_green_offset] = g
        self.led_original_color[index*3 + self.led_blue_offset]  = b
        for i in range(3):
            self.led_color[index*3 + i] = p[i]

    def set_led_color_data(self, index, r, g, b):
        self.set_ledpixel(index, r, g, b)

    def set_led_rgb_data(self, index, color):
        self.set_ledpixel(index, color[0], color[1], color[2])

    def set_all_led_color(self, r, g, b):
        for i in range(self.led_count):
            self.set_led_color_data(i, r, g, b)
        self.show()

    def write_ws2812_numpy8(self):
        d = numpy.array(self.led_color).ravel()
        tx = numpy.zeros(len(d) * 8, dtype=numpy.uint8)
        for ibit in range(8):
            tx[7 - ibit::8] = ((d >> ibit) & 1) * 0x78 + 0x80
        if self.led_init_state != 0:
            self.spi.xfer(tx.tolist(), int(8 / 1.25e-6))

    def show(self):
        self.write_ws2812_numpy8()

    def run(self):
        while True:
            self.__flag.wait()

    # ─── TURN SIGNALS ─────────────────────────────────────────
    def left_signal_on(self):
        self._blinking = True
        while self._blinking:
            for i in range(11, 14):
                self.set_led_color_data(i, 255, 80, 0)
            self.show()
            time.sleep(0.1)
            for i in range(11, 14):
                self.set_led_color_data(i, 0, 0, 0)
            self.show()
            time.sleep(0.1)
    
    def right_signal_on(self):
        self._blinking = True
        while self._blinking:
            for i in range(8, 11):
                self.set_led_color_data(i, 255, 80, 0)
            self.show()
            time.sleep(0.1)
            for i in range(8, 14):
                self.set_led_color_data(i, 0, 0, 0)
            self.show()
            time.sleep(0.1)
    
    def signals_off(self):
        self._blinking = False   # stops the blink loop in left/right_signal_on
        for i in range(8, 14):
            self.set_led_color_data(i, 0, 0, 0)
        self.show()
