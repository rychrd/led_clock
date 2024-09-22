#!/usr/bin/env python3

# import board
# from adafruit_ht16k33.segments import BigSeg7x4

from time import sleep
import time
import random
import logging
import threading
from socket import gethostbyname
from os import getlogin

# Logging Setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("osc")
logger.setLevel(logging.INFO)

# import oscmethod as osm
from osc4py3.oscmethod import *
from osc4py3.as_comthreads import *

# setup I2C display
# i2c = board.I2C()
# led = BigSeg7x4(i2c)
# led.brightness = 0.0
# led.colons[0] = True

# init global states ;)
RAMP = False
now = "0000"
speed = 0.1
FLK = False
level = 0.0
BO = True


# Get the clock id from file
filename = 'oscID'
def read_oscID(file):
	try:
		with open(file, 'r') as f:
			for line in f:
				if not line.isspace():
					id = line
				return id
	except FileNotFoundError as fe:
		print(f'ID file not found default id 1 used')
		return 1

clock_id = '5' # int(read_oscID(filename))
print(f'clock_id is {clock_id}')

# IP ADDRESS - CHANGE HOST IF REASSIGNING CLOCK 
ipaddr = gethostbyname('clocks05.local')
print(f"clock {clock_id} IP is {ipaddr}")

# OSC callbacks before starting listener
def msg_handler(*args):

	if len(args) == 2:
		s, x = args
		global FLK

		print(f"OSC message is {s} {x}")

		if s == "time":
			global BO
			global now
			if str(x).isdigit():
				now = str(x)
				update_clock(now)
				BO = True
				display_control(BO)


		if s == "brightness":
			set_brightness(x)


		if s == "flicker":
			if x == 1 and not FLK:
				FLK = True
				run_thread(flicker)
			elif x == 0:
				FLK = False

		if s == "bo":
			if x == 0:
				BO = False
				display_control(BO)
			elif x == 1:
				BO = True
				display_control(BO)

		if s == "changeID":
			id = x
			write_oscID(filename, id)


def msg_handler2(*args):

	print(args)
	global RAMP
	if args[0] == "ramp":
		if len(args) == 2:
			RAMP = args[1]
		elif len(args) == 3:
			global speed
			RAMP = args[1]
			speed = abs(0.999 - args[2])


# OSC init  
OSCaddress = f"/clock/"
osc_startup(logger=logger)

osc_udp_server(ipaddr, 54321, 'clockpi_05')
osc_broadcast_server('10.0.10.255', 54322, 'clock_bc5')

osc_method(OSCaddress, msg_handler)
osc_method(OSCaddress, msg_handler2)

# use a thread to process message
def processOSC():
	while True:
		try:
			osc_process()
		except OSCInvalidRawError as re:
			print(f'bad OSC formatting check address: {re}')
			raise 
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
#	led.print(format_time(time))
	print(format_time(time))

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
#	led.brightness = level


def flicker():
	global level
	start_level = level

	while FLK == True:
		offset = random.random()*0.75 - level
#		led.brightness = abs(level + offset)
		sleep(0.01)
		d = int(random.random() * 10) % 4

		if BO == False:
			set_brightness(start_level)
			return

#		led.set_digit_raw(d, 0x00)
		sleep(0.06)
		update_clock(now)
	
	set_brightness(start_level)


def display_control(bool):
	global now
	if bool == False:
#		led.colons[0] = False
		for d in range(4):
#			led.set_digit_raw(d, 0x00)
			pass
	else:
		update_clock(now)
#		led.colons[0] = True

def run_thread(func):
	t = threading.Thread(target=func, daemon=True)
	t.start()


def write_oscID(file, id):
	try:
		with open(file, 'w') as f:
			f.write(str(id))
			print(f'wrote id {id} to file')
	except (IOError, OSError) as fe:
		print('unable to modify OSC id on disk')
		return


# End of Functions ---------------------------------- 
#
# Main loop

if __name__  ==  '__main__':

	run_thread(processOSC)
	run_thread(minute_tick)
	update_clock(now)

# event loop - normal time or ramp.
	try:
		while True:
			
			while RAMP == True:
				now = next(ramp_time(speed))
				if BO == True:
					update_clock(now)
			sleep(0.5)
			if BO == True:
				update_clock(now)
	finally:
#		led.brightness = 0
#		for d in range(4):
#			led.set_digit_raw(d, 0x00)
#		led.colons[0] = False

		osc_terminate()
