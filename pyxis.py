import re, sys, socket, urllib, urllib.request, urllib.error, json, codecs, time
from bs4 import BeautifulSoup
from modules import parse, proxy, blowfish

pandora_api_url = 'https://internal-tuner.pandora.com/services/json/?'
hdr = {'User-agent': 'Pyxis', 'Content-type': 'text/plain'}

ENCRYPT_PASS = '2%3WCL*JU$MP]4'
DECRYPT_PASS = 'U#IO$RZPAB%VX2'

# api calls
def pandora_connect(proxy_address):
	# step 1: partner login
	data_step1 = {
		'deviceModel':'D01',
		'username':'pandora one',
		'password':'TVCKIBGS9AO9TSYLNNFUML0743LH82D',
		'version':'5'
	}
	partner_info = json_call('auth.partnerLogin', data_step1)
	
	''' test '''
	sync_time_raw = partner_info['syncTime'].encode('utf-8')
	pandora_time = int(decrypt(sync_time_raw)[4:14])
	time_offset = pandora_time - time.time()
	sync_time = int(time.time() + time_offset)
	
	print('offset:%s ; syncTime:%s ; pandora:%s \r\n' % (time_offset, sync_time, pandora_time))
	''' test '''
	
	
	
	
	
	
	
	# step 2:
	data_step2 = {
		'loginType':'user',
		'username':'',
		'password':''
	}
	data_step2['partnerId'] = partner_info['partnerId']
	data_step2['partnerAuthToken'] = partner_info['partnerAuthToken']
	data_step2['syncTime'] = sync_time
	
	print(data_step2)
	json_call('auth.userLogin', data_step2, en_blowfish = True)
	
	
	return

def json_call(method, raw_data, en_blowfish = False):
	data = json.dumps(raw_data).encode('utf-8')
	
	if en_blowfish:
		data = encrypt(data)
	print('[client] %s' % data)
	
	output = parse.return_data(('%smethod=%s' % (pandora_api_url, method)), proxy_address, data, hdr)
	print('[pandora] %s' % json.loads(output))
	return json.loads(output)['result']
	
# encode using blowfish in ECB mode and convert to hexcode
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
	
def padding(block, block_size):
	return block + (b'\0' * (block_size - len(block)))
	
'''
try:
	print(sys.argv[1])
	test = {'method': 'test.checkLicensing'}
	data1 = pandora_api_call(test)
	print(data1['result']['isAllowed'])
except:
	# find a suitable proxy
	print('No parameters specified, looking for a new proxy')
	proxy.setup()
	print('Done!')
'''

proxy_address = proxy.get_from_config()
pandora_connect(proxy_address)