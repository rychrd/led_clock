#! /usr/bin/env python3

import board
from adafruit_ht16k33.segments import BigSeg7x4

from time import sleep
import time
import random
import logging
import threading
from socket import gethostbyname
from os import getlogin


#logging.basicConfig(
#    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#logger = logging.getLogger("osc")
#logger.setLevel(logging.DEBUG)

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
clock_id = 1

ipaddr = gethostbyname('clocks.local')
print(f"clock {clock_id} IP is {ipaddr}")

# OSC callbacks

def msg_handler(s, x):
	#try:
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
		if x == 0:
			BO = False
			display_control()
		elif x == 1:
			BO = True
			display_control()

	if s == "ramp":
		if x == 0:
			global RAMP
			RAMP = x

def msg_handler2(s, x, y):

	global RAMP
	if s == "ramp":
		print(f'{s} on/off:{x} speed {y}')
		global speed
		RAMP = x
		speed = abs(0.999 - y)


# OSC IP and address mapping  
osc_startup() #(logger=logger)

osc_udp_server(ipaddr, 54321, 'clockpi_01')
osc_broadcast_server('192.168.0.255', 54322, 'clock_bc')

OSCaddress = f"/clock/{clock_id}"

osc_method(OSCaddress, msg_handler)
osc_method(OSCaddress, msg_handler2)

# use a thread to process message
def processOSC():
	while True:
		osc_process()
		sleep(0.75)

# time formatting
def format_time(clocktime):
	if len(clocktime) < 4:
		clocktime = clocktime.rjust(4, '0')
	_hh = clocktime[0:2]
	_mm = clocktime[2:4]
	_time = f"{_hh.rjust(2, '0')}{_mm.rjust(2, '0')}"

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

# ramps run the main thread - ie the clock is either ramping or just being a clock
def ramp_time(speed = 0.995):
	global now
	_now = time_to_int(now)
	_now = inc_time(*_now)
	sleep(speed)
	now = _now
	yield int_to_str(_now)

def minute_tick():
	global now
	while True:
		sleep(60)
		if RAMP == False:
			now = int_to_str(inc_time(*time_to_int(now)))
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
#		print(abs(level+offset))
		sleep(0.01)
		d = int(random.random() * 10) % 4
#		print(d)

		if BO == False:
			set_brightness(start_level)
			return

		led.set_digit_raw(d, 0x00)
		sleep(0.06)
		update_clock(now)
	
	set_brightness(start_level)


def display_control():
	global now
	if BO == False:
		led.colons[0] = False
		for d in range(4):
			led.set_digit_raw(d, 0x00)
	elif BO == True:
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
