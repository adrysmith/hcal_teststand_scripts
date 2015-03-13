from hcal_teststand import *
from qie_card_valid import *
import numpy
import sys

def set_ped(port, i, n):		# n is the decimal representation of the pedestal register.
	assert isinstance(n, int)
	if abs(n) > 31:
		print "ERROR: You must enter a decimal integer between -31 and 31. The pedestals have not been changed."
	else:
		if n <= 0:
			n = abs(n)
		else:
			n = n + 32
		n_str = "{0:#04x}".format(n)		# The "#" prints the "0x". The number of digits to pad with 0s must include these "0x", hence "4" instead of "2".
	#	commands = ["put HF1-2-QIE{0}_PedestalDAC 0x3F".format(i) for i in range(24)]
		commands = ["put HF1-2-QIE{0}_PedestalDAC {1}".format(i, n_str)]
		raw_output = ngccm_commands(crate_port, commands)
		# Maybe I should include something here to make sure the command didn't return an error? I'd have to go in and edit "ngccm_commands" to determine this.

def set_ped_all(port, n):		# n is the decimal representation of the pedestal register.
	# This function is faster than running "set_ped" 24 times.
	assert isinstance(n, int)
	if abs(n) > 31:
		print "ERROR: You must enter a decimal integer between -31 and 31. The pedestals have not been changed."
	else:
		if n <= 0:
			n = abs(n)
		else:
			n = n + 32
		n_str = "{0:#04x}".format(n)		# The "#" prints the "0x". The number of digits to pad with 0s must include these "0x", hence "4" instead of "2".
	#	commands = ["put HF1-2-QIE{0}_PedestalDAC 0x3F".format(i) for i in range(24)]
		commands = ["put HF1-2-QIE{0}_PedestalDAC {1}".format(i+1, n_str) for i in range(24)]
		raw_output = ngccm_commands_fast(crate_port, commands)

def get_channel_map(ip, crate_port):
	# This function gets each active link and tries to map each channel inside to a board QIE number, as assigned by ngccm software.
	channels = []
	links = uhtr_get_active_links(ip_uhtr)
	set_ped_all(crate_port, 31)
	if (len(links) != 6):
		print "ERROR: Not all of the links are active. A channel map can't be identified."
		print ">> The activated links are {0}.".format(links)
	else:
		for n in range(24):
#		for n in [24]:
			n += 1
			print n
			channel = {
				"number": n,
				"link": -1,
				"sublink": -1,
				"targets": [],
			}
			set_ped(crate_port, n, -31)
			for l in links:
				uhtr_read = get_data_from_uhtr(ip, 10, l)
				data = parse_uhtr_raw(uhtr_read["output"])
#				print data["adc"]
				for sl in range(4):
					adc_avg = numpy.mean([i_bx[sl] for i_bx in data["adc"]])
#					print adc_avg
					if (adc_avg == 0):
						channel["targets"].append([l, sl])
			if ( len(channel["targets"]) == 1 ):
				channel["link"] = channel["targets"][0][0]
				channel["sublink"] = channel["targets"][0][1]
			else:
				print "ERROR: The map is not one-to-one!"
				print ">> Checking n = {0} resulted in {1}.".format(n, channel["targets"])
			channels.append(channel)
			set_ped(crate_port, n, 31)
	set_ped_all(crate_port, 6)
	return channels

if __name__ == "__main__":
#	ip_uhtr = "192.168.29.40"
	ip_uhtr = "192.168.100.16"
	crate_port = 4242

	# This part prints out a channel map:
#	channels = get_channel_map(ip_uhtr, crate_port)
##	print channels
#	bad = []
#	for ch in channels:
#		if ch["link"] == -1:
#			bad.append([ch["number"], ch["targets"]])
#			print "QIE{0} is messed up: {1}.".format(ch["number"], ch["targets"])
#		else:
#			print "QIE{0} maps to Link {1}, Sublink {2}.".format(ch["number"], ch["link"], ch["sublink"])
	
	# This part reads in 100 BXs of data:
	set_ped_all(crate_port, 6)
	links = uhtr_get_active_links(ip_uhtr)
	print "The activated links are {0}.".format(links)
	for link in links:
		print "==== Link {0} ====".format(link)
		uhtr_read = get_data_from_uhtr(ip_uhtr, 300, link)
		data = parse_uhtr_raw(uhtr_read["output"])
#		print data["adc"]
		print "Read in {0} bunch crossings.".format(len(data["adc"]))
		for i in range(4):
			print "Channel {0}: ADC_avg = {1:.2f} (sigma = {2:.2f})".format(i, numpy.mean([i_bx[i] for i_bx in data["adc"]]), numpy.std([i_bx[i] for i_bx in data["adc"]]))
