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
		#print('%s >>> %s' % (s[i:i+8], codecs.encode(encrypt_blowfish.encrypt_block(padding(s[i:i+8],8)), 'hex_codec'))) # SHOW HOW IT WORKS
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
	partner_info = json_call('auth.partnerLogin', data_step1)['result']
	
	# sync time decrypt/calc
	sync_time_raw = partner_info['syncTime'].encode('utf-8')
	pandora_time = int(decrypt(sync_time_raw)[4:14])
	global time_offset
	time_offset = pandora_time - time.time()
	sync_time = int(time.time() + time_offset)
	print('offset:%s ; syncTime:%s' % (time_offset, sync_time))
	
	# step 2: user login
	data_step2 = {
		'loginType':'user',
		'username':'',
		'password':''
	}
	data_step2['syncTime'] = sync_time
	
	global url_args
	url_args['partnerId'] = partner_info['partnerId']
	
	# check old auth partner parameter
	try:
		url_args['partnerAuthToken'] = proxy.last_authtoken(None, 'partner_auth_token')
		data_step2['partnerAuthToken'] = proxy.last_authtoken(None, 'partner_auth_token')
		print('\r\n>> Checking if old partnerAuthToken works (%s)' % url_args['partnerAuthToken'])
		user_info = json_call('auth.userLogin', data_step2, url_args, en_blowfish = True)['result']
	except:
		url_args['partnerAuthToken'] = partner_info['partnerAuthToken']
		data_step2['partnerAuthToken'] = partner_info['partnerAuthToken']
		print('\r\n>> Using a new partnerAuthToken (%s)' % url_args['partnerAuthToken'])
		user_info = json_call('auth.userLogin', data_step2, url_args, en_blowfish = True)['result']
		proxy.last_authtoken(url_args['partnerAuthToken'], 'partner_auth_token', get = False)
		
	url_args['userId'] = user_info['userId']
	url_args['userAuthToken'] = user_info['userAuthToken']
	print(url_args)
	
	return url_args
	
# self-explanatory
def pandora_get_stations():
	global time_offset
	global url_args
	
	data = { }
	sync_time = int(time.time() + time_offset)
	new_user_auth_token = url_args['userAuthToken']
	data['syncTime'] = sync_time
	
	# check old user auth token
	try:
		data['userAuthToken'] = proxy.last_authtoken(None, 'user_auth_token')
		url_args['userAuthToken'] = proxy.last_authtoken(None, 'user_auth_token')
		print('\r\n>> Checking if old userAuthToken works (%s)' % url_args['userAuthToken'])
		output = json_call('user.getStationList', data, url_args, en_blowfish = True, https = False)['result']
	except:
		data['userAuthToken'] = new_user_auth_token
		url_args['userAuthToken'] = new_user_auth_token
		
		print('\r\n>> Using a new userAuthToken (%s)' % url_args['userAuthToken'])
		output = json_call('user.getStationList', data, url_args, en_blowfish = True, https = False)['result']
		proxy.last_authtoken(new_user_auth_token, 'user_auth_token', get = False)
	
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
		'includeTrackLength':True,	#debug
		'audioAdPodCapable': True,	#debug
		'includeTrackLength':True,	#debug
		'xplatformAdCapable':True	#debug
		
		
	}
	output = json_call('station.getPlaylist', data, url_args, en_blowfish = True, https = True)['result']
	
	tracks = output['items']
	for t in tracks:
		#print(t)
		print('%s by %s from %s' % (t['songName'], t['artistName'], t['albumName']))
	
	return
	
# json call routine
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
	
	print(json.loads(output))
	func_out = json.loads(output)
	
	return func_out
	
# main()
time_offset = 0
url_args = {}

pandora_connect()
station_id = pandora_get_stations()
pandora_get_playlist(station_id)