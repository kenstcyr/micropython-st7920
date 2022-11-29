from machine import Pin, SPI
from time import sleep
from microbmp import MicroBMP

# dimension framebuffer
rowBound = 64       # bytearray 'rows' - 64 rows -> 64bits
colBound = 128//8   # 'cols' in each bytearray - 16 bytes -> 128bits

# Font Sheet Size
font_w = 6
font_h = 8

# EXAMPLE WIRING (MCU runs at 3.3V, so use VIN to get 5V)
#   * RS ---- GP5    - Chip Select
#   * RW ---- GP7    - SPI MOSI  
#   * E ----- GP6    - SPI Clock
#   * PSB --- GND    - Activate SPI
#   * RST --- 5V     - resetDisplay
#   * V0 ---- 5V     - LCD contrast
#   * BLA --- 5V     - Backlight Anode
#   * BLK --- GND    - Backlight Cathode
#   * VCC --- 5V     - USB power VIN (not 3V3)
#   * GND --- 0V

class Screen():
    def __init__(self, sck=None, mosi=None, miso=None, spi=None, rst=None, cs=None, baudrate=1000000):
        self.cmdbuf = bytearray(33) # enough for 1 header byte plus 16 graphic bytes encoded as two bytes each
        self.cmdmv = memoryview(self.cmdbuf)

        if spi is not None:
            self.spi = spi
        else:
            polarity=0
            phase=0
            if sck or mosi or miso: # any pins are identified - wire up as software SPI
                if not(sck and mosi and miso):
                    raise AssertionError("All SPI pins sck, mosi and miso need to be specified")
                self.spi = SPI(-1, baudrate=baudrate, polarity=polarity, phase=phase, sck=sck, mosi=mosi, miso=miso)
            else:
                self.spi = SPI(0, baudrate=baudrate, polarity=polarity, phase=phase)


        # allocate frame buffer just once, use memoryview-wrapped bytearrays for rows
        self.fbuff = [memoryview(bytearray(colBound)) for rowPos in range(rowBound)]
 
        # Set the reset pin as an output, if specified by the user
        if rst is not None:
            self.rst = Pin(rst, mode=Pin.OUT)

        # Set the chip select pin as an output, if specified by the user
        if cs is not None:
            self.cs = Pin(cs, mode=Pin.OUT)

        # Set the screen rotation of landscape mode (0 degrees)
        self.set_rotation(0)

        # Load the font bitmap
        self.load_font_bmp()

        # Initialize the LCD
        self.init()

        # Put the screen in graphics mode by default
        self.graphics_mode()

    # Initializes the screen
    def init(self):
        self.reset()
        sleep(0.04)
        self.select(True)
        self.send_cmd(0x30)             # Function Set
        sleep(.11)
        self.send_cmd(0x30)             # Function Set
        sleep(.11)
        self.send_cmd(0x0C)             # Display On/Off
        sleep(.11)
        self.send_cmd(0x01)             # Display Clear
        sleep(0.011)
        self.send_cmd(0x06)             # Entry Mode Set
        sleep(0.072)
        self.select(False)


    # Puts the LCD into graphics mode
    def graphics_mode(self):
        self.select(True)
        self.send_cmd(0x30)
        self.send_cmd(0x34)
        self.send_cmd(0x36)
        self.set_rotation(0)
        self.select(False)

    # Enables or disables the chip select pin
    def select(self, selected):
        if selected:
            self.cs.value(True)
        else:
            self.cs.value(False)

    # Resets the LCD
    def reset(self):
        self.rst.value(False)
        sleep(0.1)
        self.rst.value(True)

    # Changes the rotation of the screen
    def set_rotation(self, rot):
        if rot == 0 or rot == 2:
            self.width = 128
            self.height = 64
        elif rot == 1 or rot == 3:
            self.width = 64
            self.height = 128
        self.rot = rot

    # Sends a command to the LCD
    def send_cmd(self, data):
        count = 3
        pos = 0

        # Clears the first 3 bytes of the command buffer
        while pos < count:
            self.cmdbuf[pos] = 0
            pos += 1

        # Sets the first 3 bytes of the command buffer
        self.cmdbuf[0] = 0b11111000
        self.cmdbuf[1] = data & 0xF0
        self.cmdbuf[2] = (data & 0x0F) << 4

        submv = self.cmdmv[:count]
        self.spi.write(submv)

        # Wait for 50ms
        sleep(0.05)
        del submv


    def send_address(self, b1, b2):
        count = 5
        pos = 0
        while pos < count:
            self.cmdbuf[pos] = 0
            pos += 1
        self.cmdbuf[0] = 0b11111000  # rs = 0
        self.cmdbuf[1] = b1 & 0xF0
        self.cmdbuf[2] = (b1 & 0x0F) << 4
        self.cmdbuf[3] = b2 & 0xF0
        self.cmdbuf[4] = (b2 & 0x0F) << 4
        submv = self.cmdmv[:count]
        self.spi.write(submv)
        del submv

    def send_data(self, arr):
        arrlen = len(arr)
        count = 1 + (arrlen << 1)
        pos = 0
        while pos < count:
            self.cmdbuf[pos] = 0
            pos += 1
        self.cmdbuf[0] = 0b11111000 | 0x02  # rs = 1
        pos = 0
        while pos < arrlen: # inlined code from marshal_byte
            self.cmdbuf[1 + (pos << 1)] = arr[pos] & 0xF0
            self.cmdbuf[2 + (pos << 1)] = (arr[pos] & 0x0F) << 4
            pos += 1
        submv = self.cmdmv[:count]
        self.spi.write(submv)
        del submv

    # Clears the LCD
    def clear(self):
        rowPos = 0
        while rowPos < rowBound:
            row = self.fbuff[rowPos]
            colPos = 0
            while colPos < colBound:
                row[colPos]=0
                colPos += 1
            rowPos += 1

    # Draws a line
    def line(self, x1, y1, x2, y2, set=True):
        diffX = abs(x2-x1)
        diffY = abs(y2-y1)
        shiftX = 1 if (x1 < x2) else -1
        shiftY = 1 if (y1 < y2) else -1
        err = diffX - diffY
        drawn = False
        while not drawn:
            self.plot(x1, y1, set)
            if x1 == x2 and y1 == y2:
                drawn = True
                continue
            err2 = 2 * err
            if err2 > -diffY:
                err -= diffY
                x1 += shiftX
            if err2 < diffX:
                err += diffX
                y1 += shiftY

    # Draws a rectangle
    def rect(self, x1, y1, x2, y2, set=True):
        self.line(x1,y1,x2,y1,set)
        self.line(x2,y1,x2,y2,set)
        self.line(x2,y2,x1,y2,set)
        self.line(x1,y2,x1,y1,set)

    # Draws a filled-in rectangle
    def fill_rect(self, x1, y1, x2, y2):
        for y in range(y1, y2):
            self.line(x1, y, x2, y)

    # Draws a point
    def plot(self, x, y, set=True):
        if x<0 or x>=self.width or y<0 or y>=self.height:
            return

        if set:
            if self.rot==0:
                self.fbuff[y][x//8] |= 1 << (7-(x%8))
            elif self.rot==1:
                self.fbuff[x][15 - (y//8)] |= 1 << (y%8)
            elif self.rot==2:
                self.fbuff[63 - y][15-(x//8)] |= 1 << (x%8)
            elif self.rot==3:
                self.fbuff[63 - x][y//8] |= 1 << (7-(y%8))
        else:
            if self.rot==0:
                self.fbuff[y][x//8] &= ~(1 << (7-(x%8)))
            elif self.rot==1:
                self.fbuff[x][15 - (y//8)] &= ~(1 << (y%8))
            elif self.rot==2:
                self.fbuff[63 - y][15-(x//8)] &= ~(1 << (x%8))
            elif self.rot==3:
                self.fbuff[63 - x][y//8] &= ~(1 << (7-(y%8)))

    # Draws a circle
    def circle(self, x1, y1, r):
        counter = r + 1
        c2 = r * r
        self.plot(x1, y1 + r)
        self.plot(x1, y1 - r)
        self.plot(x1 + r, y1)
        self.plot(x1 - r, y1)

        y = r
        x = 1
        y = round ((c2 - 1) ** (0.5))
        while x < y:
            self.plot(x1 + x, y1 - y)
            self.plot(x1 + x, y1 + y)
            self.plot(x1 - x, y1 + y)
            self.plot(x1 - x, y1 - y)
            self.plot(x1 + y, y1 - x)
            self.plot(x1 + y, y1 + x)
            self.plot(x1 - y, y1 + x)
            self.plot(x1 - y, y1 - x)
            x+=1
            y = round ((c2 - x*x) ** (0.5))

        if x == y:
            self.plot(x1 + x, y1 - y)
            self.plot(x1 + x, y1 + y)
            self.plot(x1 - x, y1 + y)
            self.plot(x1 - x, y1 - y)


    def load_font_bmp(self):
        self.fontImg = MicroBMP().load("/fontsheet.bmp")

    # Draws text using the included font bitmap
    def put_text(self, s, x, y):
        if self.fontImg == None:
            self.load_font_bmp()
        for c in s:
            d = hex(ord(c))
            x_fontmap = int(d[3], 16) * font_w
            y_fontmap = int(d[2], 16) * font_h
            for y_px in range(font_h):
                for x_px in range(font_w):
                    r, g, b = self.fontImg.palette[self.fontImg[x_px + x_fontmap, y_px + y_fontmap]]  # type: ignore
                    self.plot(x + x_px, y + y_px, r | b | g)
            x += font_w

    def redraw(self, dx1=None, dy1=None, dx2=None, dy2=None):
        """
        # TODO CH bug here? (inherited from https://github.com/JMW95/pyST7920 ) buffer address ranges calculated incorrect for (bottom-right?) rectangles
        # TODO CH HACK uncomment 4 lines below for redraw rectangle to be ignored
        dx1 = 0
        dy1 = 0
        dx2 = 127
        dy2 = 63
        """
        # TODO CH consider more efficient bounds checking
        if dx1 is None:
            dx1 = 0
        else:
            dx1 = max(0, dx1)
            dx1 = min(127, dx1)
        if dx2 is None:
            dx2 = 127
        else:
            dx2 = max(0, dx2)
            dx2 = min(127, dx2)
        if dy1 is None:
            dy1 = 0
        else:
            dy1 = max(0, dy1)
            dy1 = min(63, dy1)
        if dy2 is None:
            dy2 = 63
        else:
            dy2 = max(0, dy2)
            dy2 = min(63, dy2)
        try:
            self.select(True)
            i = dy1
            while i < dy2 + 1:
                self.send_address(0x80 + i % 32, 0x80 + ((dx1 // 16) + (8 if i >= 32 else 0)))
                self.send_data(self.fbuff[i][dx1 // 16:(dx2 // 8) + 1])
                i+=1
        finally:
            self.select(False)