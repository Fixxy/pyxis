import re, sys, socket, urllib, urllib.request, urllib.error, json, codecs, time
from bs4 import BeautifulSoup
from modules import parse, proxy, blowfish

pandora_api_url = '://internal-tuner.pandora.com/services/json/?'
hdr = {'User-agent': 'Pyxis', 'Content-type': 'text/plain'}

ENCRYPT_PASS = '2%3WCL*JU$MP]4'
DECRYPT_PASS = 'U#IO$RZPAB%VX2'

# encode/decode using blowfish in ECB mode and convert to hexcode
def encrypt(s):
	encrypt_blowfish = blowfish.Cipher(ENCRYPT_PASS.encode('utf-8'))
	temp = b''
	for i in range(0, len(s), 8):
		print('%s >>> %s' % (s[i:i+8], codecs.encode(encrypt_blowfish.encrypt_block(padding(s[i:i+8],8)), 'hex_codec')))
		temp += (codecs.encode(encrypt_blowfish.encrypt_block(padding(s[i:i+8],8)), 'hex_codec'))
	return temp
	
def decrypt(s):
	decrypt_blowfish = blowfish.Cipher(DECRYPT_PASS.encode('utf-8'))
	temp = b''
	for i in range(0, len(s), 16):
		temp += (decrypt_blowfish.decrypt_block(padding(codecs.decode(s[i:i+16], 'hex_codec'), 8))).rstrip(b'\x08')
	return temp
	
# add nulls for a proper block size
def padding(block, block_size):
	return block + (b'\0' * (block_size - len(block)))

# partner login + user login
def pandora_connect():
	# step 1: partner login
	data_step1 = {
		'deviceModel':'D01',
		'username':'pandora one',
		'password':'TVCKIBGS9AO9TSYLNNFUML0743LH82D',
		'version':'5'
	}
	partner_info = json_call('auth.partnerLogin', data_step1)
	
	# sync time decrypt/calc
	sync_time_raw = partner_info['syncTime'].encode('utf-8')
	pandora_time = int(decrypt(sync_time_raw)[4:14])
	global time_offset
	time_offset = pandora_time - time.time()
	sync_time = int(time.time() + time_offset)
	print('offset:%s ; syncTime:%s\r\n' % (time_offset, sync_time))
	
	# step 2: user login
	data_step2 = {
		'loginType':'user',
		'username':'',
		'password':''
	}
	data_step2['partnerAuthToken'] = partner_info['partnerAuthToken']
	data_step2['syncTime'] = sync_time
	
	global url_args
	url_args['partnerId'] = partner_info['partnerId']
	url_args['partnerAuthToken'] = partner_info['partnerAuthToken']
	
	user_info = json_call('auth.userLogin', data_step2, url_args, en_blowfish = True)
	
	url_args['userId'] = user_info['userId']
	url_args['userAuthToken'] = user_info['userAuthToken']
	
	print(url_args)
	
	return url_args
	
	
def pandora_get_stations():
	global time_offset
	global url_args
	sync_time = int(time.time() + time_offset)
	
	data = {
		'userAuthToken':url_args['userAuthToken'],
		'syncTime':sync_time
	}
	result = json_call('user.getStationList', data, url_args, en_blowfish = True, https = False)
	
	stations = {}
	for s in result['stations']:
		stations[s['stationId']] = s['stationName']
	
	for i in range(0, len(stations)):
		print('%s) %s' % (i, s(i)))
	
	station_num = input('Select station: ')
	print(stations[station_num])
	return stations[station_num]
	
def pandora_get_playlist(station_id):
	global time_offset
	global url_args
	sync_time = int(time.time() + time_offset)
	
	data = {
		'userAuthToken':url_args['userAuthToken'],
		'additionalAudioUrl': 'HTTP_32_AACPLUS_ADTS,HTTP_64_AACPLUS_ADTS',
		'syncTime':sync_time,
		'stationToken':station_id
	}
	result = json_call('station.getPlaylist', data, url_args, en_blowfish = True, https = True)
	
	print(result)
	
	return
	

def json_call(method, data, url_args = None, en_blowfish = False, https = True):
	data = json.dumps(data).encode('utf-8')
	
	# encrypt using blowfish in needed
	print('[client] %s' % data)
	if en_blowfish:
		data = encrypt(data)
		print('[encrypted-client] %s' % data)
	
	# add url args
	url_args_string = ''
	if url_args:
		if 'partnerId' in url_args:
			url_args_string += ('&partner_id=%s' % url_args['partnerId'])
		if 'userId' in url_args:
			url_args_string += ('&user_id=%s' % url_args['partnerId'])
		if 'userAuthToken' in url_args:
			url_args_string += ('&auth_token=%s' % url_args['userAuthToken'])
		elif 'partnerAuthToken' in url_args:
			url_args_string += ('&auth_token=%s' % url_args['partnerAuthToken'])
			
	protocol = 'https' if https else 'http'
	
	url = protocol + pandora_api_url + 'method=' + method + url_args_string
	print('url: %s' % url)
	output = parse.return_data(url, None, None, data, hdr)
	print('[pandora] %s\r\n' % json.loads(output))
	
	'''
	while True:
		try:
			output = parse.return_data(url, None, None, data, hdr)
			print('[pandora] %s\r\n' % json.loads(output)['result'])
			break
		except:
			print('[pandora] ERROR. Trying again')
	'''
	
	return json.loads(output)['result']
	
# main()
time_offset = 0
url_args = {}

pandora_connect()

station_id = pandora_get_stations()

pandora_get_playlist(station_id)