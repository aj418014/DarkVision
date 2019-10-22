#!/usr/bin/python

import threading
import time
import datetime
import argparse
import netaddr
import sys
import logging
from scapy.all import *
from pprint import pprint
from logging.handlers import RotatingFileHandler


NAME = 'spifi'
DESCRIPTION = "a tool for logging the number of unique 802.11 devices in an area over time"

DEBUG = False

macSet = set()

def report(reporter, seconds, live, time_fmt, delimiter):
	# list of output fields
	fields = []

	# determine preferred time format 
	log_time = str(int(time.time()))
	if time_fmt == 'iso':
		log_time = datetime.now().isoformat()

	fields.append(log_time)
	fields.append(str(len(macSet)))
	reporter.info(delimiter.join(fields))
	macSet.clear()

def build_packet_callback(time_fmt, logger, delimiter, mac_info, ssid, rssi):
	def packet_callback(packet):
		
		if not packet.haslayer(Dot11):
			return

		# we are looking for management frames with a probe subtype
		# if neither match we are done here
		if packet.type != 0 or packet.subtype != 0x04 or packet.addr2 in macSet:
			return

		# list of output fields
		fields = []

		# determine preferred time format 
		log_time = str(int(time.time()))
		if time_fmt == 'iso':
			log_time = datetime.now().isoformat()

		fields.append(log_time)

		# append the mac address itself
		fields.append(packet.addr2)
		macSet.add(packet.addr2)

		# parse mac address and look up the organization from the vendor octets
		if mac_info:
			try:
				parsed_mac = netaddr.EUI(packet.addr2)
				fields.append(parsed_mac.oui.registration().org)
			except netaddr.core.NotRegisteredError, e:
				fields.append('UNKNOWN')

		# include the SSID in the probe frame
		if ssid:
			fields.append(packet.info)
			
		if rssi:
			rssi_val = -(256-ord(packet.notdecoded[-4:-3]))
			fields.append(str(rssi_val))

		logger.info(delimiter.join(fields))

	return packet_callback

def main():
	parser = argparse.ArgumentParser(description=DESCRIPTION)
	parser.add_argument('-i', '--interface', help="capture interface")
	parser.add_argument('-t', '--time', default='iso', help="output time format (unix, iso)")
	parser.add_argument('-o', '--output', default='/dev/null', help="logging output location")
	parser.add_argument('-O', '--report-output', default='reports.log', help="report output location")
	parser.add_argument('-b', '--max-bytes', default=5000000, help="maximum log size in bytes before rotating")
	parser.add_argument('-c', '--max-backups', default=99999, help="maximum number of log files to keep")
	parser.add_argument('-d', '--delimiter', default='\t', help="output field delimiter")
	parser.add_argument('-f', '--mac-info', action='store_true', help="include MAC address manufacturer")
	parser.add_argument('-s', '--ssid', action='store_true', help="include probe SSID in output")
	parser.add_argument('-r', '--rssi', action='store_true', help="include rssi in output")
	parser.add_argument('-D', '--debug', action='store_true', help="enable debug output")
	parser.add_argument('-l', '--log', action='store_true', help="enable scrolling live view of the logfile")
	parser.add_argument('-I', '--report-interval', default=60, help="time in seconds between reports")
	args = parser.parse_args()

	if not args.interface:
		print "error: capture interface not given, try --help"
		sys.exit(-1)
	
	DEBUG = args.debug

	# setup our rotating logger
	logger = logging.getLogger(NAME)
	logger.setLevel(logging.INFO)
	handler = RotatingFileHandler(args.output, maxBytes=args.max_bytes, backupCount=args.max_backups)
	logger.addHandler(handler)

	#setup report logger
	reporter = logging.getLogger(NAME + "_reports")
	reporter.setLevel(logging.INFO)
	reportHandler = RotatingFileHandler(args.report_output, maxBytes=args.max_bytes, backupCount=args.max_backups)
	reporter.addHandler(reportHandler)

	if args.log:
		logger.addHandler(logging.StreamHandler(sys.stdout))
		reporter.addHandler(logging.StreamHandler(sys.stdout))

	built_packet_cb = build_packet_callback(args.time, logger, 
		args.delimiter, args.mac_info, args.ssid, args.rssi)
	#reporter_args = [reporter, args.report_interval, args.log, args.time]
	rt = RepeatedTimer(args.report_interval, report, reporter, args.report_interval, args.log, args.time, args.delimiter)
	sniff(iface=args.interface, prn=built_packet_cb, store=0)


#This class is used to run reports periodically. Credit to Stackoverflow user "eraoul". https://stackoverflow.com/a/40965385
class RepeatedTimer(object):
  def __init__(self, interval, function, *args, **kwargs):
    self._timer = None
    self.interval = interval
    self.function = function
    self.args = args
    self.kwargs = kwargs
    self.is_running = False
    self.next_call = time.time()
    self.start()

  def _run(self):
    self.is_running = False
    self.start()
    self.function(*self.args, **self.kwargs)

  def start(self):
    if not self.is_running:
      self.next_call += self.interval
      self._timer = threading.Timer(self.next_call - time.time(), self._run)
      self._timer.start()
      self.is_running = True

  def stop(self):
    self._timer.cancel()
    self.is_running = False

if __name__ == '__main__':
	main()
