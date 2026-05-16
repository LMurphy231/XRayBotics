import time
import board
import busio
import Adafruit_ADS1x15.ADS1x15 as ADS

i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)
chan = AnalogIn(ads, ADS.P0)