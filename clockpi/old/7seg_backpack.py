#! /usr/bin/env python3

import board
from adafruit_ht16k33.segments import BigSeg7x4

from time import sleep
import random

from osc4py3.oscmethod import *
from osc4py3.as_eventloop import *


# setup I2C display
i2c = board.I2C()
led = BigSeg7x4(i2c)


# OSC Handler Functions

def format_time(clocktime):
	
	if len(clocktime) < 4:
		clocktime = clocktime.rjust(4, '0')
	_hh = clocktime[0:2]
	_mm = clocktime[2:4]
	_hh = int(_hh) % 24
	_mm = int(_mm) % 60
	_time = str(_hh).rjust(2, '0') + str(_mm).rjust(2, '0')
	print(f'{_hh} {_mm} {_time}')
	
	return _time


def update_clock(time):
	led.print(format_time(time))


def time_to_int(t_string):
	if len(t_string) < 4:
		t_string = t_string.rjust(4, '0')
	_hh = int(t_string[0:2])
	_mm = int(t_string[2:4])
	return _hh, _mm


def int_to_str(t,):
	_hh = str(t[0]).rjust(2, '0')
	_mm = str(t[1]).rjust(2, '0')
	return _hh + _mm


def ramp_time(hh, mm):

	mm += 1	
	if (mm > 59):
		mm = mm % 60
		hh = hh + 1
	hh = hh % 24
	return hh, mm


led.brightness = 0.01
led.blink_rate = 0
led.print("12:58")

sleep(3)
#for d in range(4):
#	display.set_digit_raw(d, 0x00)
led.colons[0] = True



update_clock("307")
inttime = time_to_int("307")

print(f"307 as an int is {time_to_int('307')}")
now = "0412"

now = ramp_time(*time_to_int(now))
while True:
	now = ramp_time(*now)
	nowstr = int_to_str(now)

	print(f'´tuple is {now} mapped is {nowstr}')
	update_clock(nowstr)
	sleep(0.1)



 

sleep(10)


hh = 18
mm = 35


try:
	while True:
#		led.print(hh + mm)
		led.brightness = random.random() * 0.75
		sleep(0.05)
		d = int(random.random() * 4)
#		led.set_digit_raw(d, 0x00)
		sleep(0.01)
finally:
	led.brightness = 0


#while True:
#	display.colons[0] = True
#
#	sleep(1)
#	display.colons[0] = False
#	sleep(1)


