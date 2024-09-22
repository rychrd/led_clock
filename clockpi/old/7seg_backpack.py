#! /usr/bin/env python3

import board
from adafruit_ht16k33.segments import BigSeg7x4

from time import sleep
import random

# import oscmethod as osm
from osc4py3.oscmethod import *
from osc4py3.as_allthreads import *


# setup I2C display
i2c = board.I2C()
led = BigSeg7x4(i2c)
led.brightness = 0.0
global RAMP
RAMP = False

#OSC setup

def msg_handler(s, x, y):
	print(f"OSC message is {s} {x} {y}")
	update_clock(str(x))
	if s == "flicker":
		flicker()


osc_startup(execthreadscount=1)
osc_udp_server('192.168.0.59', 54321, 'clockpi_1')

osc_method("/clock1/*", msg_handler)


# time formatting
def format_time(clocktime):

	if len(clocktime) < 4:
		clocktime = clocktime.rjust(4, '0')
	_hh = clocktime[0:2]
	_mm = clocktime[2:4]
	_hh = int(_hh) % 24
	_mm = int(_mm) % 60
	_time = f"{str(_hh).rjust(2, '0')}{str(_mm).rjust(2, '0')}"
#	print(f'{_hh} {_mm} {_time}')
	
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
	_hhmm = ""
	for num in t:
		_hhmm += str(num).rjust(2, '0')
	return _hhmm


def inc_time(hh, mm):

	mm += 1
	if (mm > 59):
		mm = mm % 60
		hh = hh + 1
	hh = hh % 24
	return hh, mm


def ramp_time(now, speed = 0.1):

	_now = time_to_int(now)
	while RAMP == True:
		_now = inc_time(*_now)
		update_clock(int_to_str(_now))
		sleep(speed)
#		print(RAMP)
	

# display control

def brightness(level):
	led.brightness = level


def flicker():
	while True:
#		led.print(hh + mm)
		led.brightness = random.random() * 0.75
		sleep(0.05)
		d = int(random.random() * 4)
#		led.set_digit_raw(d, 0x00)
		sleep(0.01)


def blank_display():
	for d in range(4):
		led.set_digit_raw(d, 0x00)
	led.colons[0] = False


try:

	led.print("12:58")

	sleep(3)

	update_clock("307")

	RAMP = True
	now = "0412"
	update_clock(now)
	ramp_time(now)
	while True:
#		osc_process()


		sleep(0.5)
	RAMP = False

finally:
	led.brightness = 0
	for d in range(4):
		led.set_digit_raw(d, 0x00)
	osc_terminate()

#hh = 18
#mm = 35


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
	for d in range(4):
		led.set_digit_raw(d, 0x00)



