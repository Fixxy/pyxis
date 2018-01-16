import re, sys, socket, urllib, urllib.request, urllib.error, json, codecs, time, configparser, logging, threading
from bs4 import BeautifulSoup
from modules import request, config, proxy, ui_main, ui_stations
from external import blowfish
from subprocess import Popen, PIPE, STDOUT
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QDialog, QGridLayout, QMainWindow
from PyQt5.QtGui import QPixmap, QCloseEvent
from PyQt5.QtCore import QRect, QUrl, QCoreApplication, QThread, pyqtSignal, QMetaObject
from queue import Queue

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

# Station list pop-up
class stations_window(QDialog, ui_stations.Ui_Dialog):
	def __init__(self, stations, queue, parent):
		self.queue = queue
		self.stations = stations
		super(stations_window, self).__init__(parent)
		self.setupUi(self)
		
		# list them in combobox
		for i in range(0, len(self.stations)):
			self.comboBox.addItem('%s - %s [%s]' % (i, self.stations[i]['stationName'], self.stations[i]['stationId']))
			
		self.pushButton.clicked.connect(self.station_select)
		
	# Send station_id to the queue
	def station_select(self):
		list_id = self.comboBox.currentIndex()
		station_id = self.stations[list_id]['stationId']
		print('\r\n(i) Selected: %s' % self.comboBox.currentText())
		self.queue.put(station_id)
		self.close()
		
class main_window(QMainWindow, ui_main.Ui_Dialog):
	def __init__(self, parent=None):
		super(main_window, self).__init__(parent)
		self.setupUi(self)
		self.pushButton.clicked.connect(self.start_button)
		self.pushButton_2.clicked.connect(lambda: self.send_command('p\n')) #pauseButton
		self.pushButton_3.clicked.connect(lambda: self.rate_button(True)) #loveButton
		self.pushButton_4.clicked.connect(lambda: self.send_command('q\n')) #skipButton
		self.pushButton_5.clicked.connect(lambda: self.rate_button(False)) #banButton
		
	# overriding standard close event
	def closeEvent(self, event):
		# do stuff
		if QCloseEvent:
			try:
				global mplayer_process
				mplayer_process.kill()
			except:
				print('Unexpected error')
			event.accept() # let the window close
		else:
			event.ignore()
	
	def start_button(self):
		self.albumImg.setText('Initializing')
		self.albumImg.adjustSize()
		
		#init pandora
		self.p = Pandora()
		
		#run thread
		self.queue = Queue()
		self.pandora_thread = connectThread(self.queue, self.p)
		self.pandora_thread.start()
		self.pandora_thread.labelSignal.connect(self.update_labels)
		self.pandora_thread.stationsSignal.connect(self.show_stations)
	
	def send_command(self, com):
		global mplayer_process
		mplayer_process.stdin.write(com.encode('utf-8', 'ignore'))
		mplayer_process.stdin.flush()
		
	def update_labels(self, name, artist, album, url, fav, track, station):
		#set labels and album img
		self.songTitle.setText(name)
		self.songTitle.adjustSize()
		self.songInfo.setText('by "%s" from "%s"' % (artist, album))
		self.songInfo.adjustSize()
		self.favOrNot.setText('Yes' if fav == 1 else 'No')
		self.favOrNot.adjustSize()
		self.current_track = track
		self.current_station = station
		
		#TODO: spawn new transparent window like Google Music does?
		data = request.return_data(url, None, None, None, hdr, enable_proxy = False)
		img = QPixmap()
		img.loadFromData(data)
		resized_img = img.scaledToWidth(130)
		self.albumImg.setPixmap(resized_img)
		self.albumImg.adjustSize()
		
	# Open pop-up and log the info
	def show_stations(self, stations):
		print('\r\n(i) Found stations:')
		for i in range(0, len(stations)):
			print(i, stations[i]['stationId'], stations[i]['stationName'])
		window = stations_window(stations, self.queue, self)
		window.show()
		
	def rate_button(self, rating):
		print('\r\n(i) Loving song...' if rating == True else '\r\n(i) Banning song...')
		self.p.rate_song(self.current_station, self.current_track, rating)
		if (rating == False):
			self.send_command('q\n')
		else:
			self.favOrNot.setText('Yes')
			self.favOrNot.adjustSize()
		
class connectThread(QThread):
	# Create the signal
	labelSignal = pyqtSignal(str, str, str, str, int, str, str)
	stationsSignal = pyqtSignal(list)
	
	def __init__(self, queue, pandora):
		self.in_queue = queue
		self.p = pandora
		QThread.__init__(self)
	
	def __del__(self):
		self.wait()

	def run(self):
		print('Welcome to Pyxis')
		proxy.setup()
		self.p.connect()
		
		# Station select window
		stations = self.p.get_stations_only()
		self.stationsSignal.emit(stations)
		
		# wait for the data in queue
		while True:
			if not self.in_queue.empty():
				station_id = self.in_queue.get()
				break
			else:
				pass
		
		while True:
			tracks = self.p.get_playlist(self, station_id)
			print('(i) Starting playback')
			for t in tracks:
				try:
					url = t['audioUrlMap']['lowQuality']['audioUrl'] #mediumQuality
					playing = 'Now playing "%s" by "%s" from "%s"' % (t['songName'], t['artistName'], t['albumName'])
					if t['songRating'] == 1:
						playing = ('%s <3' % playing)
					print(playing)
					# change labels, play audio and store data for the "Like" button
					self.labelSignal.emit(t['songName'], t['artistName'], t['albumName'], t['albumArtUrl'], t['songRating'], t['trackToken'], t['stationId'])
					self.p.play(url)
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
	def get_stations_only(self):
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
		
		result = output['stations']
		return result
	
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
		
	# rate song
	def rate_song(self, station_id, track_id, rating):
		sync_time = int(time.time() + self.time_offset)
		data = {
			'stationToken':station_id,
			'trackToken':track_id,
			'isPositive':rating,
			'userAuthToken':self.url_args['userAuthToken'],
			'syncTime':sync_time
		}
		output = self.json_call('station.addFeedback', data, self.url_args, en_blowfish = True, https = False)['result']
	
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
		
		############# RETRY TEST #############
		for i in range(0,3):
			logging.debug('Retry #%s' % i)
			try:
				output = request.return_data(url, None, None, data, hdr)
				break
			except urllib.error.URLError:
				pass
		############# RETRY TEST #############
		
		logging.debug(json.loads(output))
		func_out = json.loads(output)
		
		return func_out
	
	# play the audio stream via mplayer | TODO: find a better solution
	def play(self, url):
		global mplayer_process
		mplayer_process = Popen(['mplayer\mplayer', url], stdin=PIPE, stdout=PIPE, stderr=STDOUT)
		
		for line in mplayer_process.stdout:
			#if not (line.startswith(b'A:') or line.startswith(b'\rCache fill')):
				#logging.debug(line)
			pass

def main():
	app = QApplication(sys.argv)
	form = main_window()
	form.show()
	app.exec_()
	
if __name__ == '__main__':
    main()