import serial
import time

arduino = serial.Serial('COM4', 9600)
time.sleep(3)

arduino.write(b'E')
print("Sent E")