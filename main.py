from gpiozero import Button, PWMLED, Servo
from Adafruit_CharLCD import Adafruit_CharLCD
from time import time, sleep
import decimal
import datetime
import RPi.GPIO as GPIO

# stage:
# 0 = begining, wait for pushing button
# 1 = spinning, wait for stop
# 2 = is stoped, showing time
# 3 = is stoped, showing message
# 4 = ending, auto matically go to begining
stage = 0

# some useful variables
pulsesStamps = []
lcdTime = ""
rpmStartTime = time()
time_start = time()
seconds = 0
minutes = 0
currentRpm = 0

# pin for hardwares
lcd = Adafruit_CharLCD(rs=26, en=19, d4=13, d5=6, d6=5, d7=11, cols=16, lines=2)
led = PWMLED(17)
servo = Servo(22) 
button = Button(4)

# setup
servo.max()

# founctions to call in the futurei
# stage 0 wait for starting
def WaifForStart ():
	if stage == 0:
		lcd.clear()
		lcd.message("Press Button")

# stage 1, spining
def Spin ():
	global currentRpm, stage, pulsesStamps, seconds, minutes, rpmStartTime, time_start, lcdTime
	if stage == 1 :	
		if (time() - rpmStartTime) >= 2 and len(pulsesStamps) >= 2 :
			currentRpm = 60 / ((pulsesStamps[-1] - pulsesStamps[0]) / (len(pulsesStamps)-1))
			rpmStartTime = time()
			del pulsesStamps[0: (len(pulsesStamps)-2)]
			print(currentRpm)
			if currentRpm <= 30 :
				print("RPM < 30, Stopped")
				stage = 2
		
		seconds = int(time() - time_start) - minutes * 60
	 	try:	
			if (time() - pulsesStamps[-1]) >= 5:
				print("Not detect spin for 5 second, Stopped")
				stage = 2 		
		except:
			pass
		if seconds >= 60:
        		minutes += 1
        		seconds = 0
		if seconds < 10 :
			lcdTime = str(minutes)+ "'0" +str(seconds)+ '"  RPM ' + str(currentRpm)
		else: 
			lcdTime = str(minutes)+ "'" +str(seconds)+ '"  RPM ' + str(currentRpm)
		lcd.clear()
		lcd.message(lcdTime)
		if currentRpm >= 400:
			lcd.message("\n" + "Are You Cheating?")

#stage 2,3,4, stopping
def Stop ():
	global currentRpm, pulsesStamps, stage
	if stage == 2 :
		pulsesStamps = []
		for i in range (0,4):
			lcd.clear()
			sleep(0.2)
			lcd.message(lcdTime)
			sleep(0.2)
		stage = 3
	if stage == 3 :
		congrat1 = str(minutes)+ "'" +str(seconds)+ '"' + " = " + "$" + str(0.07 * (minutes*60 + seconds)) 
		congrat2 = "    $1766/Credit in ITP is $0.7/second, and you just wasted "+ str(minutes)+ "'" +str(seconds)+ '"' +" here.  "
		lcd.clear()
		lcd.message(congrat1)	
		for i in range(0,len(congrat2)-16):
			lcd.message("\n" + congrat2[i:i+16])
			sleep(0.5)
			if stage == 1:
				break
		if stage == 3:
			sleep (3)
			stage = 0

# call this to record the time stamp when hall effect sensor activated
def sensorCallback(channel):
  timestamp = time()
  if stage == 1 and GPIO.input(channel):
	pulsesStamps.append(timestamp)

# what to do when pressing button
def recordStartTime():
	global time_start, minutes
	time_start = time()
	minutes = 0
	print("startTimeRefreshed")

def triggerServo1():
	global stage 
	stage = 1 
	servo.mid()
	lcd.clear()
	led.value = 0.8
	print("pressed")
def triggerServo2():
	sleep(0.05)
	servo.max()
	led.value = 0.2
	recordStartTime()

# setup call back event
GPIO.setmode(GPIO.BCM)
print("Setup GPIO pin as input on GPIO27")
GPIO.setup(27 , GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(27, GPIO.BOTH, callback=sensorCallback,bouncetime=10)

# loop
try:
	while True:
		sleep(0.1)
		button.when_pressed = triggerServo1
		button.when_released = triggerServo2
		WaifForStart()
		Spin()
		Stop()
		print(stage)
except KeyboardInterrupt:
	GPIO.cleanup()
