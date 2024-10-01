#!/usr/local/bin env python3

# This version runs the RAMP function in a thread
# import board
# from adafruit_ht16k33.segments import BigSeg7x4

from time import sleep
import random
import logging
import threading
from socket import gethostbyname
from os import getlogin

#from osc4py3.oscbuildparse import decode_packet


# Logging Setup
logging.basicConfig(
	format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("osc")
logger.setLevel(logging.DEBUG)

import osc4py3.oscmethod as osm

from osc4py3.oscmethod import *
from osc4py3.as_comthreads import *
from osc4py3.oscbuildparse import OSCInvalidRawError

# setup I2C display
# i2c = board.I2C()
# led = BigSeg7x4(i2c)
# led.brightness = 0.0
# led.colons[0] = True

# init global states ;)
ramp = False
now = "0000"
speed = 0.1
flk = False
level = 0.0
bo = True
lock = threading.Lock()

# Get the clock id from local file
filename = 'oscID'
def read_oscID(file):
	try:
		with open(file, 'r') as f:
			for line in f:
				if not line.isspace():
					c_id = line.rstrip()
				return c_id
	except FileNotFoundError as fe:
		print(f'ID file not found default id 1 used')
		return 1

clock_id = '1' #(read_oscID(filename))
print(f'clock_id is {clock_id}')

# IP ADDRESS - CHANGE HOST IF REASSIGNING CLOCK 
ipaddr = '192.168.0.20'
#('clocks05.local')
print(f"clock {clock_id} IP is {ipaddr}")

# OSC callbacks before starting listener
def msg_handler(addr, *args):

	print(f'OSC address is {addr}')
	method = addr.split('/')[-1]
	print(f'method is {method}')

	if len(args) >= 1:
		x = args[0]

		print(f"OSC argument is {x}")

		if method == "time":
			global bo
			global now
			if str(x).isdigit():
				with lock:
					now = str(x)
					update_clock(now)
				bo = True
				display_control(bo)


		if method == "brightness":
			set_brightness(x)


		if method == "flicker":
			global flk
			if flk and x:
				pass
			elif not (flk and x):
				flk = x
				run_thread(flicker)



		if method == "bo":
			if x == 0:
				bo = False
				display_control(bo)
			elif x == 1:
				bo = True
				display_control(bo)

		if method == "changeID":
			write_oscID(filename, x)


def msg_handler2(addr, *args):

	method = addr.split('/')[-1]
	global ramp
 
	if method == "ramp":
		if len(args):
			_ramp = args[0]
			if (not ramp) and _ramp:
				ramp = True
				run_thread(ramp_loop)
			else:
				ramp = False
		
		elif len(args) == 2:
			global speed
			_ramp = args[0]
			if (not ramp) and _ramp:
				speed = abs(0.999 - args[1])
				ramp = True			
				run_thread(ramp_loop)
			else:
				ramp = False
    

# OSC init  
OSCaddress = f"/clock/{clock_id}/*"
logger.info("osc address is %s", OSCaddress)

osc_startup(logger=logger)

osc_udp_server(ipaddr, 54321, 'clockpi_05')
# osc_broadcast_server('broadcast', 54322, 'clock_bc5')

osc_method(OSCaddress, msg_handler, argscheme=osm.OSCARG_ADDRESS + osm.OSCARG_DATAUNPACK)
osc_method(OSCaddress, msg_handler2, argscheme=osm.OSCARG_ADDRESS + osm.OSCARG_DATAUNPACK)

# try to catch errors in OSC processing threads
def processOSC():
	try:
		osc_process()
	except OSCInvalidRawError as re:
		print(f'Raw error {re}')
  

	
# time formatting, time as string
def format_time(clocktime):
	if len(clocktime) < 4:
		clocktime = clocktime.rjust(4, '0')
   
	_hh = clocktime[0:2]
	_mm = clocktime[2:4]
	_time = f"{_hh.rjust(2, '0')}{_mm.rjust(2, '0')}"
	return _time


def update_clock(time):
#	led.print(format_time(time))
	print(format_time(time), end='\r')


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
	if mm > 59:
		mm = mm % 60
		hh = hh + 1
	hh = hh % 24
	return hh, mm


# ramps run the main thread prior to v005(this one). This function isn't called.
def ramp_time(speed = 0.995):
    
	global now
	_now = time_to_int(now)
	_now = inc_time(*_now)
	sleep(speed)
	now = _now
	yield int_to_str(_now)


def ramp_loop():
    
	global speed
	global now	

	while ramp:
		with lock:
			now = int_to_str(inc_time(*time_to_int(now)))
   
		print(f'ramping..\n{now} ', end='\r')
		sleep(speed)


def minute_tick():
    
	global now
	while True:
		sleep(60)
		if not ramp:
			now = int_to_str(inc_time(*time_to_int(now)))


# display control and fx
def set_brightness(val):
    
	global level
	level = val
#	led.brightness = level


def flicker():

	global level, flk
	start_level = level

	while flk:
		offset = random.random()*0.75 - level
#		led.brightness = abs(level + offset)
		print('flickering...', end = '\n')
		sleep(0.01)
		d = int(random.random() * 10) % 4

		if not bo:
			set_brightness(start_level)
			return

#		led.set_digit_raw(d, 0x00)
		sleep(0.06)
		update_clock(now)
	
	set_brightness(start_level)


def display_control(bool):
    
	global now
	if not bool:
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
		print('unable to save OSC id to disk')
		return


# ------------------------ End of Functions ---------------------- #

if __name__  ==  '__main__':

	run_thread(minute_tick)
	update_clock(now)
	
# event loop - wait for OSC commands and increment time.
	try:
		while True:
			#	processOSC()
				osc_process()
				sleep(0.5)
				if bo:
					update_clock(now)
     
	except OSCInvalidRawError as re:
				print('bad OSC string {re}')
    	
	finally:
#		led.brightness = 0
		for d in range(4):
#			led.set_digit_raw(d, 0x00)
			pass
#		led.colons[0] = False
		print('Exiting...')
		osc_terminate()
