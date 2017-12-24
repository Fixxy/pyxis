import re, sys, socket, urllib, urllib.request, urllib.error, json, codecs, time, configparser, subprocess, logging, threading
from bs4 import BeautifulSoup
from modules import request, config, proxy
from external import blowfish
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QUrl, QCoreApplication, QThread, pyqtSignal

logging.basicConfig(level=logging.DEBUG)
# load stuff from INI file
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

class App(QWidget):
	def __init__(self):
		super().__init__()
		self.title = 'Pyxis'
		self.left = 200
		self.top = 150
		self.width = 500
		self.height = 300
		self.initUI()
	
	def initUI(self):
		self.setWindowTitle(self.title)
		self.setGeometry(self.left, self.top, self.width, self.height)
		
		#img
		#TODO: change placeholder img
		self.albumImg = QLabel(self)
		img = QPixmap('placeholder.png')
		self.albumImg.setPixmap(img)
		
		#labels
		self.songTitle = QLabel(self)
		self.songTitle.move(250,20)
		self.songTitle.setText('#SongName                ')
		self.songArtist = QLabel(self)
		self.songArtist.move(250,30)
		self.songArtist.setText('#ArtistName                ')
		self.albumName = QLabel(self)
		self.albumName.move(250,40)
		self.albumName.setText('#albumName                ')
		
		#button
		self.button = QPushButton('Start', self)
		self.button.move(250, 60)
		self.button.clicked.connect(self.playButton)
		
		self.show()
	
	def playButton(self):
		self.songTitle.setText('Initializing')
		
		#run thread
		self.myThread = testThread()
		self.myThread.start()
		self.myThread.labelSignal.connect(self.changeLabel)
		
	def changeLabel(self, name, artist, album, url):
		self.songTitle.setText(name)
		self.songArtist.setText(artist)
		self.albumName.setText(album)
		
		data = urllib.request.urlopen(url).read()
		img = QPixmap()
		img.loadFromData(data)
		self.albumImg.setPixmap(img)
	
class testThread(QThread):
	# Create the signal
	labelSignal = pyqtSignal(str, str, str, str)
	
	def __init__(self):
		QThread.__init__(self)
	
	def __del__(self):
		self.wait()

	def run(self):
		print('Welcome to Pyxis')
		proxy.setup()

		p = Pandora()
		p.connect()
		station_id = p.get_stations()

		while True:
			tracks = p.get_playlist(self, station_id)
			print('(i) Starting playback')
			for t in tracks:
				try:
					url = t['audioUrlMap']['lowQuality']['audioUrl'] #mediumQuality
					playing = 'Now playing "%s" by "%s" from "%s"' % (t['songName'], t['artistName'], t['albumName'])
					if t['songRating'] == 1:
						playing = ('%s <3' % playing)
					print(playing)
					# Emit the signal and play
					self.labelSignal.emit(t['songName'], t['artistName'], t['albumName'], t['albumArtUrl'])
					p.play(url)
				except:
					print('### adToken:%s' % t['adToken'])
					#self.get_ad(t['adToken'])

class Pandora():
	time_offset = 0
	url_args = {}
	
	# encrypt/decrypt using blowfish in ECB mode and convert to hexcode
	def encrypt(self, s):
		encrypt_blowfish = blowfish.Cipher(encrypt_pass.encode('utf-8'))
		data = b''
		for i in range(0, len(s), 8):
			logging.debug('%s >>> %s' % (s[i:i+8], codecs.encode(encrypt_blowfish.encrypt_block(self.padding(s[i:i+8],8)), 'hex_codec')))
			data += (codecs.encode(encrypt_blowfish.encrypt_block(self.padding(s[i:i+8],8)), 'hex_codec'))
		return data
	
	def decrypt(self, s):
		decrypt_blowfish = blowfish.Cipher(decrypt_pass.encode('utf-8'))
		data = b''
		for i in range(0, len(s), 16):
			data += (decrypt_blowfish.decrypt_block(self.padding(codecs.decode(s[i:i+16], 'hex_codec'), 8))).rstrip(b'\x08')
		return data
	
	# add nulls for a proper block size
	def padding(self, block, block_size):
		return block + (b'\0' * (block_size - len(block)))
	
	# partner login + user login
	def connect(self):
		# step 1: partner login
		print('(i) Logging in')
		data_step1 = {
			'deviceModel':device_model,
			'username':partner_username,
			'password':partner_password,
			'version':version
		}
		partner_info = self.json_call('auth.partnerLogin', data_step1)['result']
		
		# sync time decrypt/calc
		sync_time_raw = partner_info['syncTime'].encode('utf-8')
		pandora_time = int(self.decrypt(sync_time_raw)[4:14])
		self.time_offset = pandora_time - time.time()
		sync_time = int(time.time() + self.time_offset)
		logging.debug('offset:%s ; syncTime:%s' % (self.time_offset, sync_time))
		
		data_step2 = {
			'loginType':'user',
			'username':username,
			'password':password,
			'syncTime':sync_time
		}
		
		self.url_args['partnerId'] = partner_info['partnerId']
		
		# check old auth partner parameter
		try:
			self.url_args['partnerAuthToken'] = config.last_authtoken(None, 'partner_auth_token')
			data_step2['partnerAuthToken'] = config.last_authtoken(None, 'partner_auth_token')
			print('> Checking if old partnerAuthToken works (%s)' % self.url_args['partnerAuthToken'])
			user_info = self.json_call('auth.userLogin', data_step2, self.url_args, en_blowfish = True)['result']
		except:
			self.url_args['partnerAuthToken'] = partner_info['partnerAuthToken']
			data_step2['partnerAuthToken'] = partner_info['partnerAuthToken']
			print('> Using a new partnerAuthToken (%s)' % self.url_args['partnerAuthToken'])
			user_info = self.json_call('auth.userLogin', data_step2, self.url_args, en_blowfish = True)['result']
			config.last_authtoken(self.url_args['partnerAuthToken'], 'partner_auth_token', get = False)
			
		self.url_args['userId'] = user_info['userId']
		self.url_args['userAuthToken'] = user_info['userAuthToken']
		logging.debug(self.url_args)
		
		return self.url_args
	
	# self-explanatory
	def get_stations(self):
		data = { }
		sync_time = int(time.time() + self.time_offset)
		new_user_auth_token = self.url_args['userAuthToken']
		data['syncTime'] = sync_time
		
		# step 2: user login
		# check old user auth token
		try:
			data['userAuthToken'] = config.last_authtoken(None, 'user_auth_token')
			self.url_args['userAuthToken'] = config.last_authtoken(None, 'user_auth_token')
			print('> Checking if old userAuthToken works (%s)' % self.url_args['userAuthToken'])
			output = self.json_call('user.getStationList', data, self.url_args, en_blowfish = True, https = False)['result']
		except:
			data['userAuthToken'] = new_user_auth_token
			self.url_args['userAuthToken'] = new_user_auth_token
			
			print('> Using a new userAuthToken (%s)' % self.url_args['userAuthToken'])
			output = self.json_call('user.getStationList', data, self.url_args, en_blowfish = True, https = False)['result']
			config.last_authtoken(new_user_auth_token, 'user_auth_token', get = False)
		
		print('\r\n(i) Stations:')
		result = output['stations']
		for i in range(0, len(result)):
			print(i, result[i]['stationId'], result[i]['stationName'])

		station_num = input('Select station: ')
		station_id = result[int(station_num)]['stationId']
		return station_id
	
	# self-explanatory
	def get_playlist(self, form, station_id):
		sync_time = int(time.time() + self.time_offset)
		
		data = {
			'userAuthToken':self.url_args['userAuthToken'],
			'syncTime':sync_time,
			'stationToken':station_id,
			'additionalAudioUrl':'HTTP_32_AACPLUS_ADTS,HTTP_128_MP3',
			'includeTrackLength':True
		}
		print('\r\n(i) Retrieving new playlist')
		output = self.json_call('station.getPlaylist', data, self.url_args, en_blowfish = True, https = True)['result']
		
		tracks = output['items']
		
		return tracks
	
	# get the ad's audio link
	def get_ad(self, ad_token):
		global time_offset
		global url_args
		sync_time = int(time.time() + self.time_offset)
		
		data = {
			'userAuthToken':self.url_args['userAuthToken'],
			'syncTime':sync_time,
			'adToken':ad_token,
			'supportAudioAds':True
		}
		print('\r\n(i) Receiving the ad metadata')
		output = self.json_call('ad.getAdMetadata', data, self.url_args, en_blowfish = True, https = True)['result']
		
		#output['audioUrlMap']['audioUrl']
		return
	
	# json call routine
	def json_call(self, method, data, url_args = None, en_blowfish = False, https = True):
		data = json.dumps(data).encode('utf-8')
		
		# encrypt using blowfish in needed
		logging.debug('[client] %s' % data)
		if en_blowfish:
			data = self.encrypt(data)
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
	def play(self, url):
		#https://web.archive.org/web/20151212195644/http://www.keyxl.com/aaa2fa5/302/MPlayer-keyboard-shortcuts.htm
		#p = subprocess.Popen(['mplayer\mplayer', url], stdin=subprocess.PIPE, stderr=subprocess.STDOUT).communicate
		p = subprocess.Popen(['mplayer\mplayer', url], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		
		for line in p.stdout:
			#if not (line.startswith(b'A:') or line.startswith(b'\rCache fill')):
				#logging.debug(line)
			pass
		return
'''
print('Welcome to Pyxis')
proxy.setup()

pandora = Pandora()
pandora.connect()
station_id = pandora.get_stations()

while True:
	pandora.get_playlist(station_id)
'''

if __name__ == '__main__':
	app = QApplication(sys.argv)
	ex = App()
	sys.exit(app.exec_())