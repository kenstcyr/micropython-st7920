# Micropython ST7920

Micropython library for simple graphic primitives on ST7920 128x64 monochrome LCD panel using a Raspberry Pi Pico and SPI

# Features

Can initialise a screen and framebuffer with...

```python
import st7920 
screen = st7920.Screen()
```

Can draw points, lines, rectangles, circles, and text to a framebuffer with e.g.

```
screen.plot(10, 10)
screen.line(10, 10, 20, 20)
screen.rect(25, 25, 50, 50)
screen.fill_rect(5, 5, 95, 95)
screen.circle(30, 30, 6)
screen.put_text("Text", 0, 0)
```

Can draw inverse with e.g.

```
screen.plot(10, 10, False)
screen.line(10, 10, 20, 20, False)
screen.rect(25, 25, 50, 50, False)
```

Then send finished 1kbyte frame to the screen at 1Mbaud with...

```
screen.redraw()
```

Finally clear again with...
```
screen.clear()
screen.redraw()
```

# Credits

Based on project developed by @cefn of @ShrimpingIt, which is based on @JMW95's incredibly useful reference Raspberry Pi python SPI port at https://github.com/JMW95/pyST7920, funded by the Milecastles project.  Last modified by @kenstcyr.

Leverages [MicroBMP library](https://github.com/jacklinquan/microbmp) for loading fontsheet PNG file for drawing text.

# See also

[ST7920 Datasheet](http://www.hpinfotech.ro/ST7920.pdf)

[Micropython SPI reference](https://docs.micropython.org/en/latest/esp8266/esp8266/quickref.html#software-spi-bus)

[Arduino U8G2 reference setup for ST7920 128x64 SPI display](https://github.com/olikraus/u8g2/wiki/setup_tutorial#identify-the-display)
