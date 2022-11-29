import st7920

lcd = st7920.Screen(cs=5, rst=0)    # Create the lcd object
lcd.graphics_mode()                 # Put the LCD into graphics mode
lcd.clear()                         # Clear the screen

lcd.rect(28, 14, 100, 46)           # Draw a rectangle
lcd.rect(26, 12, 102, 48)           # Draw another rectangle

lcd.fill_rect(108, 20, 123, 40)     # Draw a filled rectangle

lcd.rect(110, 36, 121, 38, False)   # Remove a rectangle

lcd.circle(64, 30, 10)              # Draw a circle

lcd.plot(2, 37)                     # Draw a dot
lcd.plot(70, 19)                    # Draw another dot
lcd.plot(125, 62)                   # Draw another dot

lcd.plot(112, 24, False)            # Remove a dot

lcd.put_text("Example", 44, 3)      # Write some text

lcd.line(10, 5, 20, 60)             # Draw a line

lcd.redraw()                        # Repaint the display