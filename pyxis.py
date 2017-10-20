import re, sys, socket, urllib, urllib.request, urllib.error, json, codecs, time, configparser, subprocess, logging
from bs4 import BeautifulSoup
from modules import request, config, proxy
from external import blowfish

logging.basicConfig(level=logging.DEBUG)

hdr = {'User-agent': 'Pyxis', 'Content-type': 'text/plain'}
pandora_api_url = config.get_from_config('pandora','api_url')
device_model = config.get_from_config('pandora','device_model')
partner_username = config.get_from_config('pandora','partner_username')
partner_password = config.get_from_config('pandora','partner_password')
version = config.get_from_config('pandora','version')
encrypt_pass = config.get_from_config('pandora','encrypt_pass')
decrypt_pass = config.get_from_config('pandora','decrypt_pass')

username = config.get_from_config('pandora_user','username')
password = config.get_from_config('pandora_user','password')

# encode/decode using blowfish in ECB mode and convert to hexcode
def encrypt(s):
	encrypt_blowfish = blowfish.Cipher(encrypt_pass.encode('utf-8'))
	temp = b''
	for i in range(0, len(s), 8):
		logging.debug('%s >>> %s' % (s[i:i+8], codecs.encode(encrypt_blowfish.encrypt_block(padding(s[i:i+8],8)), 'hex_codec')))
		temp += (codecs.encode(encrypt_blowfish.encrypt_block(padding(s[i:i+8],8)), 'hex_codec'))
	return temp
	
def decrypt(s):
	decrypt_blowfish = blowfish.Cipher(decrypt_pass.encode('utf-8'))
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
	print('(i) Logging in')
	data_step1 = {
		'deviceModel':device_model,
		'username':partner_username,
		'password':partner_password,
		'version':version
	}
	partner_info = json_call('auth.partnerLogin', data_step1)['result']
	
	# sync time decrypt/calc
	sync_time_raw = partner_info['syncTime'].encode('utf-8')
	pandora_time = int(decrypt(sync_time_raw)[4:14])
	global time_offset
	time_offset = pandora_time - time.time()
	sync_time = int(time.time() + time_offset)
	logging.debug('offset:%s ; syncTime:%s' % (time_offset, sync_time))
	
	data_step2 = {
		'loginType':'user',
		'username':username,
		'password':password
	}
	data_step2['syncTime'] = sync_time
	
	global url_args
	url_args['partnerId'] = partner_info['partnerId']
	
	# check old auth partner parameter
	try:
		url_args['partnerAuthToken'] = config.last_authtoken(None, 'partner_auth_token')
		data_step2['partnerAuthToken'] = config.last_authtoken(None, 'partner_auth_token')
		print('> Checking if old partnerAuthToken works (%s)' % url_args['partnerAuthToken'])
		user_info = json_call('auth.userLogin', data_step2, url_args, en_blowfish = True)['result']
	except:
		url_args['partnerAuthToken'] = partner_info['partnerAuthToken']
		data_step2['partnerAuthToken'] = partner_info['partnerAuthToken']
		print('> Using a new partnerAuthToken (%s)' % url_args['partnerAuthToken'])
		user_info = json_call('auth.userLogin', data_step2, url_args, en_blowfish = True)['result']
		config.last_authtoken(url_args['partnerAuthToken'], 'partner_auth_token', get = False)
		
	url_args['userId'] = user_info['userId']
	url_args['userAuthToken'] = user_info['userAuthToken']
	logging.debug(url_args)
	
	return url_args
	
# self-explanatory
def pandora_get_stations():
	global time_offset
	global url_args
	
	data = { }
	sync_time = int(time.time() + time_offset)
	new_user_auth_token = url_args['userAuthToken']
	data['syncTime'] = sync_time
	
	# step 2: user login
	# check old user auth token
	try:
		data['userAuthToken'] = config.last_authtoken(None, 'user_auth_token')
		url_args['userAuthToken'] = config.last_authtoken(None, 'user_auth_token')
		print('> Checking if old userAuthToken works (%s)' % url_args['userAuthToken'])
		output = json_call('user.getStationList', data, url_args, en_blowfish = True, https = False)['result']
	except:
		data['userAuthToken'] = new_user_auth_token
		url_args['userAuthToken'] = new_user_auth_token
		
		print('> Using a new userAuthToken (%s)' % url_args['userAuthToken'])
		output = json_call('user.getStationList', data, url_args, en_blowfish = True, https = False)['result']
		config.last_authtoken(new_user_auth_token, 'user_auth_token', get = False)
	
	print('\r\n(i) Stations:')
	result = output['stations']
	for i in range(0, len(result)):
		print(i, result[i]['stationId'], result[i]['stationName'])

	station_num = input('Select station: ')
	station_id = result[int(station_num)]['stationId']
	return station_id
	
# self-explanatory
def pandora_get_playlist(station_id):
	global time_offset
	global url_args
	sync_time = int(time.time() + time_offset)
	
	data = {
		'userAuthToken':url_args['userAuthToken'],
		'syncTime':sync_time,
		'stationToken':station_id,
		'additionalAudioUrl':'HTTP_32_AACPLUS_ADTS,HTTP_128_MP3',
		'includeTrackLength':True
	}
	print('\r\n(i) Retrieving the playlist')
	output = json_call('station.getPlaylist', data, url_args, en_blowfish = True, https = True)['result']
	
	tracks = output['items']
	for t in tracks:
		try:
			url = t['audioUrlMap']['lowQuality']['audioUrl'] #mediumQuality
			print('Now playing "%s" by "%s" from "%s"' % (t['songName'], t['artistName'], t['albumName']))
			logging.debug('url:%s\r\n' % url)
			
			# play dat thing
			play(url, t['trackLength'])
		except:
			print('### adToken:%s' % t['adToken'])
			#TODO: should probably do something with it, no idea what yet
	return
	
# json call routine
def json_call(method, data, url_args = None, en_blowfish = False, https = True):
	data = json.dumps(data).encode('utf-8')
	
	# encrypt using blowfish in needed
	logging.debug('[client] %s' % data)
	if en_blowfish:
		data = encrypt(data)
		logging.debug('[encrypted-client] %s' % data)
	
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
	logging.debug('url: %s' % url)
	output = request.return_data(url, None, None, data, hdr)
	
	logging.debug(json.loads(output))
	func_out = json.loads(output)
	
	return func_out
	
# play the audio stream via mplayer | TODO: find a better solution
def play(url, track_length):
	#https://web.archive.org/web/20151212195644/http://www.keyxl.com/aaa2fa5/302/MPlayer-keyboard-shortcuts.htm
	print('q - skip, p - pause, 9 and 0	- decrease/increase volume')
	p = subprocess.Popen(['mplayer\mplayer', url], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	
	for line in p.stdout:
		if line.startswith(b'A:'):
			pass
		else:
			logging.debug(line)
	return
	
# main()
time_offset = 0
url_args = {}

print('Welcome to Pyxis')
proxy.setup()
pandora_connect()
station_id = pandora_get_stations()
while True:
	pandora_get_playlist(station_id)