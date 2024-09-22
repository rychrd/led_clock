#! /usr/bin/env python3
import socket
from subprocess import run

PORT = 44444

def setup_udp():
	hostname = socket.gethostbyaddr('localhost')[0]
	print(f'my name is {hostname}')

	udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

	try:
		udp_sock.bind(('', PORT))

	except OSError as e:
		print(f"can't bind socket to port {PORT} : {e} ..Already in use?")

	finally:

		ip, port = udp_sock.getsockname()
		print(f"listening at {hostname}, ip {ip}, port {port}")

	return udp_sock, hostname

def udp_listen(udp_sock):
	try:
		msg, pt = udp_sock.recvfrom(64)
		yield msg, pt

	except OSError as err:
		print(f'error on setup - is an instance already running? {err}')
		exit()


def sys_reboot():
	print('got a restart message')
	run(['sudo', 'shutdown', '-r', 'now'])

def sys_shutdown():
	run(['sudo', 'shutdown', '-h', 'now'])

if __name__ == '__main__':

	sock, host = setup_udp()
	try:
		while True:
			message, sender = next(udp_listen(sock))
			print(f"received message '{message.decode()}' from {sender}")

			if message == b'restart' or message == host.encode():
				sys_reboot()
			if message == b'shutdown':
				sys_shutdown()
			
			else:
				continue

	finally:

		sock.close()
