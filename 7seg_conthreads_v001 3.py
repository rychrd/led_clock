#! /usr/bin/env python3

import board
from adafruit_ht16k33.segments import BigSeg7x4

from time import sleep
import time
import random

import threading

# import oscmethod as osm
from osc4py3.oscmethod import *
from osc4py3.as_comthreads import *

# setup I2C display
i2c = board.I2C()
led = BigSeg7x4(i2c)
led.brightness = 0.0
led.colons[0] = True

# init global states ;)
RAMP = False
now = "0000"
speed = 0.1
FLK = False
level = 0.0
BO = True

real_time = time.time()

# OSC callback

def msg_handler(s, x):
	global FLK

	print(f"OSC message is {s} {x}")

	if s == "time":
		global now
		if str(x).isdigit():
			now = str(x)
			update_clock(now)

	if s == "brightness":
		set_brightness(x)


	if s == "flicker":
		if x == 1 and not FLK:
			FLK = True
			run_thread(flicker)
		elif x == 0:
			FLK = False

	if s == "bo":
		global BO
		print(f'{s} {x}')
		BO = x
		display_control(x)



def msg_handler2(s, x, y):

	global RAMP
	if s == "ramp":
		print(f'{s} on/off:{x} speed {y}')
		global speed
		RAMP = x
		speed = abs(0.999 - y)

# OSC IP and address mapping  
osc_startup()
osc_udp_server('192.168.4.46', 54321, 'clockpi_1')

OSCaddress = "/clock/1"

osc_method(OSCaddress, msg_handler)
osc_method(OSCaddress, msg_handler2)

# use a thread to process message
def processOSC():
	while True:
		osc_process()
		sleep(0.75)

# time formatting
def format_time(clocktime):
#	try:
	if len(clocktime) < 4:
		clocktime = clocktime.rjust(4, '0')
	_hh = clocktime[0:2]
	_mm = clocktime[2:4]
	if (not _hh.isdigit()) or (not _mm.isdigit()):		
		return now
	_hh = int(_hh) % 24
	_mm = int(_mm) % 60
	_time = f"{str(_hh).rjust(2, '0')}{str(_mm).rjust(2, '0')}"
	return _time

#	except ValueError as ve:
#		print(f'can only mod integers {ve}')
#		clocktime = now
#		raise


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

# ramps run the main thread - ie the clock is either ramping or just being a clock
def ramp_time(speed = 0.1):
	global now
	_now = time_to_int(now)
	_now = inc_time(*_now)
	sleep(speed)
	now = _now
	yield int_to_str(_now)

def minute_tick():
	global now
	while True:
		if RAMP == False:
			now = int_to_str(inc_time(*time_to_int(now)))
		sleep(60)
	sleep(2)

# display control and fx
def set_brightness(val):
	global level
	level = val
	led.brightness = level


def flicker():
	global level
	start_level = level

	while FLK == True:
#		print(FLK)
		offset = random.random()*0.75 - level
		led.brightness = abs(level + offset)
		print(abs(level+offset))
		sleep(0.01)
		d = int(random.random() * 10) % 4
#		print(d)

		if BO == False:
			set_brightness(start_level)
			return

		led.set_digit_raw(d, 0x00)
		sleep(0.01)
		update_clock(now)
	
	set_brightness(start_level)


def display_control(bool):
	global now
	if bool == False:
		led.colons[0] = False
		for d in range(4):
			led.set_digit_raw(d, 0x00)
	else:
		update_clock(now)
		led.colons[0] = True

def run_thread(func):
	t = threading.Thread(target=func, daemon=True)
	t.start()

# End of Functions ---------------------------------- 
#
# Main loop

if __name__  ==  '__main__':

	try:
		run_thread(processOSC)
		run_thread(minute_tick)

		update_clock(now)

# event loop - normal time or ramp.

		while True:
			
			while RAMP == True:
				now = next(ramp_time(speed))
				if BO == True:
					update_clock(now)
			sleep(0.5)
			if BO == True:
				update_clock(now)
	finally:
		led.brightness = 0
		for d in range(4):
			led.set_digit_raw(d, 0x00)
		led.colons[0] = False

		osc_terminate()
