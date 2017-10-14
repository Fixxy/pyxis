import re, sys, socket, urllib, urllib.request, urllib.error, json, codecs, time
from bs4 import BeautifulSoup
from modules import parse, proxy, blowfish

pandora_api_url = 'https://internal-tuner.pandora.com/services/json/?'
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
def pandora_connect(proxy_address):
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
	time_offset = pandora_time - time.time()
	sync_time = int(time.time() + time_offset)
	print('offset:%s ; syncTime:%s\r\n' % (time_offset, sync_time))
	
	# step 2: user login
	data_step2 = {
		'loginType':'user',
		'username':'',
		'password':'',
		'returnStationList':True
	}
	data_step2['partnerAuthToken'] = partner_info['partnerAuthToken']
	data_step2['syncTime'] = sync_time
	
	url_args = {}
	url_args['partnerId'] = partner_info['partnerId']
	url_args['partnerAuthToken'] = partner_info['partnerAuthToken']
	
	json_call('auth.userLogin', data_step2, url_args, en_blowfish = True)
	return

def json_call(method, data, url_args = None, en_blowfish = False):
	data = json.dumps(data).encode('utf-8')
	
	# encrypt using blowfish in needed
	print('[client] %s' % data)
	if en_blowfish:
		data = encrypt(data)
		print('[encrypted-client] %s' % data)
	
	# add url args
	url_args_string = ''
	if url_args:
		if url_args['partnerId']:
			url_args_string += ('&partner_id=%s' % url_args['partnerId'])
		if url_args['partnerAuthToken']:
			url_args_string += ('&auth_token=%s' % url_args['partnerAuthToken'])
	
	url = pandora_api_url + 'method=' + method + url_args_string
	print('url: %s' % url)
	output = parse.return_data(url, proxy_address, data, hdr)
	print('[pandora] %s' % json.loads(output))
	return json.loads(output)['result']
	
try:
	proxy_address = proxy.get_from_config()
	pandora_connect(proxy_address)
except:
	# find a suitable proxy
	print('No parameters specified, looking for a new proxy')
	proxy.setup()
	print('Done!')