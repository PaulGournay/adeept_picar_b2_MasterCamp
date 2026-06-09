import spidev
import threading  
import numpy
from numpy import sin, cos, pi
import time
class Adeept_SPI_LedPixel(threading.Thread):
    def __init__(self, count = 8, bright = 255, sequence='GRB', bus = 0, device = 0, *args, **kwargs):
        self.set_led_type(sequence)
        self.set_led_count(count)
        self.set_led_brightness(bright)
        self.led_begin(bus, device)
        self.lightMode = 'none'
        self.colorBreathR = 0
        self.colorBreathG = 0
        self.colorBreathB = 0
        self.breathSteps = 10
        #self.spi_gpio_info()
        self.set_all_led_color(0,0,0)
        super(Adeept_SPI_LedPixel, self).__init__(*args, **kwargs)
        self.__flag = threading.Event()
        self.__flag.clear()
    def led_begin(self, bus = 0, device = 0):
        self.bus = bus
        self.device = device
        try:
            self.spi = spidev.SpiDev()
            self.spi.open(self.bus, self.device)
            self.spi.mode = 0
            self.led_init_state = 1
        except OSError:
            print("Please check the configuration in /boot/firmware/config.txt.")
            if self.bus == 0:
                print("You can turn on the 'SPI' in 'Interface Options' by using 'sudo raspi-config'.")
                print("Or make sure that 'dtparam=spi=on' is not commented, then reboot the Raspberry Pi. Otherwise spi0 will not be available.")
            else:
                print("Please add 'dtoverlay=spi{}-2cs' at the bottom of the /boot/firmware/config.txt, then reboot the Raspberry Pi. otherwise spi{} will not be available.".format(self.bus, self.bus))
            self.led_init_state = 0
            
    def check_spi_state(self):
        return self.led_init_state
        
    def spi_gpio_info(self):
        if self.bus == 0:
            print("SPI0-MOSI: GPIO10(WS2812-PIN)  SPI0-MISO: GPIO9  SPI0-SCLK: GPIO11  SPI0-CE0: GPIO8  SPI0-CE1: GPIO7")
        elif self.bus == 1:
            print("SPI1-MOSI: GPIO20(WS2812-PIN)   SPI1-MISO: GPIO19  SPI1-SCLK: GPIO21  SPI1-CE0: GPIO18  SPI1-CE1: GPIO17  SPI0-CE1: GPIO16")
        elif self.bus == 2:
            print("SPI2-MOSI: GPIO41(WS2812-PIN)   SPI2-MISO: GPIO40  SPI2-SCLK: GPIO42  SPI2-CE0: GPIO43  SPI2-CE1: GPIO44  SPI2-CE1: GPIO45")
        elif self.bus == 3:
            print("SPI3-MOSI: GPIO2(WS2812-PIN)  SPI3-MISO: GPIO1  SPI3-SCLK: GPIO3  SPI3-CE0: GPIO0  SPI3-CE1: GPIO24")
        elif self.bus == 4:
            print("SPI4-MOSI: GPIO6(WS2812-PIN)  SPI4-MISO: GPIO5  SPI4-SCLK: GPIO7  SPI4-CE0: GPIO4  SPI4-CE1: GPIO25")
        elif self.bus == 5:
            print("SPI5-MOSI: GPIO14(WS2812-PIN)  SPI5-MISO: GPIO13  SPI5-SCLK: GPIO15  SPI5-CE0: GPIO12  SPI5-CE1: GPIO26")
        elif self.bus == 6:
            print("SPI6-MOSI: GPIO20(WS2812-PIN)  SPI6-MISO: GPIO19  SPI6-SCLK: GPIO21  SPI6-CE0: GPIO18  SPI6-CE1: GPIO27")
    
    def led_close(self):
        self.set_all_led_rgb([0,0,0])
        self.spi.close()
    
    def set_led_count(self, count):
        self.led_count = count
        self.led_color = [0,0,0] * self.led_count
        self.led_original_color = [0,0,0] * self.led_count
    
    def set_led_type(self, rgb_type):
        try:
            led_type = ['RGB','RBG','GRB','GBR','BRG','BGR']
            led_type_offset = [0x06,0x09,0x12,0x21,0x18,0x24]
            index = led_type.index(rgb_type)
            self.led_red_offset = (led_type_offset[index]>>4) & 0x03
            self.led_green_offset = (led_type_offset[index]>>2) & 0x03
            self.led_blue_offset = (led_type_offset[index]>>0) & 0x03
            return index
        except ValueError:
            self.led_red_offset = 1
            self.led_green_offset = 0
            self.led_blue_offset = 2
            return -1
    
    def set_led_brightness(self, brightness):
        self.led_brightness = brightness
        for i in range(self.led_count):
            self.set_led_rgb_data(i, self.led_original_color)
            
    def set_ledpixel(self, index, r, g, b):
        p = [0,0,0]
        p[self.led_red_offset] = round(r * self.led_brightness / 255)
        p[self.led_green_offset] = round(g * self.led_brightness / 255)
        p[self.led_blue_offset] = round(b * self.led_brightness / 255)
        self.led_original_color[index*3+self.led_red_offset] = r
        self.led_original_color[index*3+self.led_green_offset] = g
        self.led_original_color[index*3+self.led_blue_offset] = b
        for i in range(3):
            self.led_color[index*3+i] = p[i]

    def set_led_color_data(self, index, r, g, b):
        self.set_ledpixel(index, r, g, b)  
        
    def set_led_rgb_data(self, index, color):
        self.set_ledpixel(index, color[0], color[1], color[2])   
        
    def set_led_color(self, index, r, g, b):
        self.set_ledpixel(index, r, g, b)
        self.show() 
        
    def set_led_rgb(self, index, color):
        self.set_led_rgb_data(index, color)   
        self.show() 
    
    def set_all_led_color_data(self, r, g, b):
        for i in range(self.led_count):
            self.set_led_color_data(i, r, g, b)
            
    def set_all_led_rgb_data(self, color):
        for i in range(self.led_count):
            self.set_led_rgb_data(i, color)   
        
    def set_all_led_color(self, r, g, b):
        for i in range(self.led_count):
            self.set_led_color_data(i, r, g, b)
        self.show()
        
    def set_all_led_rgb(self, color):
        for i in range(self.led_count):
            self.set_led_rgb_data(i, color) 
        self.show()
    
    def write_ws2812_numpy8(self):
        d = numpy.array(self.led_color).ravel()        #Converts data into a one-dimensional array
        tx = numpy.zeros(len(d)*8, dtype=numpy.uint8)  #Each RGB color has 8 bits, each represented by a uint8 type data
        for ibit in range(8):                          #Convert each bit of data to the data that the spi will send
            tx[7-ibit::8]=((d>>ibit)&1)*0x78 + 0x80    #T0H=1,T0L=7, T1H=5,T1L=3   #0b11111000 mean T1(0.78125us), 0b10000000 mean T0(0.15625us)  
        if self.led_init_state != 0:
            if self.bus == 0:
                self.spi.xfer(tx.tolist(), int(8/1.25e-6))         #Send color data at a frequency of 6.4Mhz
            else:
                self.spi.xfer(tx.tolist(), int(8/1.0e-6))          #Send color data at a frequency of 8Mhz
        
    def write_ws2812_numpy4(self):
        d=numpy.array(self.led_color).ravel()
        tx=numpy.zeros(len(d)*4, dtype=numpy.uint8)
        for ibit in range(4):
            tx[3-ibit::4]=((d>>(2*ibit+1))&1)*0x60 + ((d>>(2*ibit+0))&1)*0x06 + 0x88  
        if self.led_init_state != 0:
            if self.bus == 0:
                self.spi.xfer(tx.tolist(), int(4/1.25e-6))         
            else:
                self.spi.xfer(tx.tolist(), int(4/1.0e-6))       
        
    def show(self, mode = 1):
        if mode == 1:
            write_ws2812 = self.write_ws2812_numpy8
        else:
            write_ws2812 = self.write_ws2812_numpy4
        write_ws2812()
        
    def wheel(self, pos):
        if pos < 85:
            return [(255 - pos * 3), (pos * 3), 0]
        elif pos < 170:
            pos = pos - 85
            return [0, (255 - pos * 3), (pos * 3)]
        else:
            pos = pos - 170
            return [(pos * 3), 0, (255 - pos * 3)]
    
    def hsv2rgb(self, h, s, v):
        h = h % 360
        rgb_max = round(v * 2.55)
        rgb_min = round(rgb_max * (100 - s) / 100)
        i = round(h / 60)
        diff = round(h % 60)
        rgb_adj = round((rgb_max - rgb_min) * diff / 60)
        if i == 0:
            r = rgb_max
            g = rgb_min + rgb_adj
            b = rgb_min
        elif i == 1:
            r = rgb_max - rgb_adj
            g = rgb_max
            b = rgb_min
        elif i == 2:
            r = rgb_min
            g = rgb_max
            b = rgb_min + rgb_adj
        elif i == 3:
            r = rgb_min
            g = rgb_max - rgb_adj
            b = rgb_max
        elif i == 4:
            r = rgb_min + rgb_adj
            g = rgb_min
            b = rgb_max
        else:
            r = rgb_max
            g = rgb_min
            b = rgb_max - rgb_adj
        return [r, g, b]
    
    def police(self):
        self.lightMode = 'police'
        self.resume()
        
    def breath(self, R_input, G_input, B_input):
        self.lightMode = 'breath'
        self.colorBreathR = R_input
        self.colorBreathG = G_input
        self.colorBreathB = B_input
        self.resume()    
            
    def resume(self):
        self.__flag.set()


    def breathProcessing(self):
        while self.lightMode == 'breath':
            for i in range(0,self.breathSteps):
                if self.lightMode != 'breath':
                    break
                self.set_all_led_color(self.colorBreathR*i/self.breathSteps, self.colorBreathG*i/self.breathSteps, self.colorBreathB*i/self.breathSteps)
                #self.show()
                time.sleep(0.03)
            for i in range(0,self.breathSteps):
                if self.lightMode != 'breath':
                    break
                self.set_all_led_color(self.colorBreathR-(self.colorBreathR*i/self.breathSteps), self.colorBreathG-(self.colorBreathG*i/self.breathSteps), self.colorBreathB-(self.colorBreathB*i/self.breathSteps))
                #self.show()
                time.sleep(0.03)
    def policeProcessing(self):
        while self.lightMode == 'police':
            for i in range(0,3):
                self.set_all_led_color_data(0,0,255)
                self.show()
                time.sleep(0.05)
                self.set_all_led_color_data(0,0,0)
                self.show()
                time.sleep(0.05)
            if self.lightMode != 'police':
                break
            time.sleep(0.1)
            for i in range(0,3):
                self.set_all_led_color_data(255,0,0)
                self.show()
                time.sleep(0.05)
                self.set_all_led_color_data(0,0,0)
                self.show()
                time.sleep(0.05)
            time.sleep(0.1)
            
            
    def lightChange(self):
        if self.lightMode == 'none':
            self.pause()
        elif self.lightMode == 'police':
            self.policeProcessing()
        elif self.lightMode == 'breath':
            self.breathProcessing()    
    
    def run(self):
        while 1:
            self.__flag.wait()
            self.lightChange()
            pass
    def piloter_led(self, num_led, couleur, intensite=255):
        """
        num_led: 0 à 13 (pour les 14 LEDs)
        couleur: 'R', 'G', 'B', 'N' (N pour noir/éteint)
        intensite: 0 à 255
        """
        # Ajuster la luminosité globale temporairement pour cette commande
        self.set_led_brightness(intensite)
        
        # Initialisation des composantes
        r, g, b = 0, 0, 0
        
        # Normalisation de la casse de la couleur saisie
        couleur = couleur.upper()
        
        if couleur == 'R':
            r = 255
        elif couleur == 'G':
            g = 255
        elif couleur == 'B':
            b = 255
        elif couleur == 'N':
            r, g, b = 0, 0, 0  # Éteint
        else:
            print(f"Couleur invalide '{couleur}'. Utilisez R, G, B ou N.")
            return

        # Appliquer la couleur sur la mémoire de la LED spécifique
        self.set_led_color_data(num_led, r, g, b)
        
        # REQUIS CRITIQUE : Envoyer le signal physique aux WS2812 !
        self.show()

        
            
    
if __name__ == '__main__':
    print("--- Initialisation du module WS2812 (14 LEDs) ---")
    arr=["R","G","B"]
    # Instance configurée pour 14 LEDs en bande (Guirlande)
    leds_robot = Adeept_SPI_LedPixel(count=14, bright=255)

    if leds_robot.check_spi_state() == 0:
        print("Erreur de bus SPI. Fin du programme.")
        exit()

    print("Vérification : extinction de toutes les LEDs...")
    leds_robot.set_all_led_color(0, 0, 0)
    time.sleep(1)

    print("\n--- MODE PILOTAGE MANUEL ACTIVÉ ---")
    print("Entrez vos commandes. Pour quitter, tapez 'exit'.")
    
    # for i in range(leds_robot.led_count):
    #     for b in arr:
    #         leds_robot.piloter_led(i,b)
    #         time.sleep(1)
    #     leds_robot.piloter_led(i,"N")
    while True:
        try:
            saisie = input("\nEntrez (Ex: '0 R 150' pour LED 0, Rouge, Intensité 150) : ").strip()
            
            if saisie.lower() == 'exit':
                print("Extinction des feux et fermeture...")
                leds_robot.set_all_led_color(0, 0, 0)
                break
                
            # Découpage des arguments
            elements = saisie.split()
            
            if len(elements) < 2:
                print("Format incorrect. Il faut au moins : <n°LED> <Couleur>")
                continue
                
            num_led = int(elements[0])
            couleur = elements[1]
            
            # Si l'intensité n'est pas fournie, par défaut 255
            intensite = int(elements[2]) if len(elements) >= 3 else 255
            
            # Validation du numéro de LED (0 à 13 pour 14 LEDs)
            if num_led < 0 or num_led >= 14:
                print("Numéro de LED incorrect ! Choisissez entre 0 et 13.")
                continue
                
            if not (0 <= intensite <= 255):
                print("L'intensité doit être comprise entre 0 et 255.")
                continue

            # Exécution de l'action
            leds_robot.piloter_led(num_led, couleur, intensite)
            print(f"LED {num_led} configurée sur {couleur.upper()} (Intensité: {intensite})")

        except ValueError:
            print("Erreur de saisie : assurez-vous que la LED et l'intensité soient des nombres entiers.")
        except KeyboardInterrupt:
            print("\nInterruption détectée. Fermeture.")
            leds_robot.set_all_led_color(0, 0, 0)
            break

