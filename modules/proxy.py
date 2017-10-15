import re, socket, urllib, urllib.request, urllib.error, configparser, json
from modules import parse

testHTML = None
pandora_check = 'https://internal-tuner.pandora.com/services/json/?method=test.checkLicensing'
hdr = {'Accept': 'text/html', 'User-Agent' : 'Fiddler'}
config_file = 'pyxis.ini'

def find_new():
	html = parse.return_data('https://www.socks-proxy.net/', None, None, None, hdr, enable_proxy = False)
	table = parse.get_tag_data(html, 'table', 0, 'proxylisttable')[0].tbody
	rows = table.find_all('tr')
	for row in rows:
		r = row.find_all('td')
		print('Checking: %s:%s' % (r[0].get_text(),r[1].get_text()))
		try:
			proxy_ip = r[0].get_text()
			proxy_port = int(r[1].get_text())
			testHTML = parse.return_data(pandora_check, proxy_ip, proxy_port, None, hdr)
			if (json.loads(testHTML)['result']['isAllowed']):
				print('it works (%s)' % testHTML)
			replace_config(r[0].get_text(), r[1].get_text())
			break
		except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionRefusedError, modules.socks.ProxyConnectionError) as e:
			print('this one doesn\'t work (%s)' % e)
	return proxy_ip, proxy_port
	
# get proxy from config file
def get_from_config():
	config = configparser.ConfigParser()
	config.read(config_file)
	proxy_ip = config['proxy']['socks5']
	proxy_port = int(config['proxy']['socks5_port'])
	return proxy_ip, proxy_port
	
# check if old one works, if not find_new()
def setup():
	proxy_ip, proxy_port = get_from_config()
	print('Checking %s:%s' % (proxy_ip, proxy_port))
	try:
		testHTML = parse.return_data(pandora_check, proxy_ip, proxy_port, None, hdr)
		print('testHTML: %s' % testHTML)
		if (json.loads(testHTML)['result']['isAllowed']):
			print('old proxy works')
	except:
		print('old proxy doesn\'t work, let\'s find a new one')
		proxy_ip, proxy_port = find_new()
	
	return
	
# replace proxy
def replace_config(proxy_ip, proxy_port):
	config = configparser.ConfigParser()
	config.read(config_file)
	config['proxy']['socks5'] = proxy_ip
	config['proxy']['socks5_port'] = proxy_port
	with open(config_file, 'w') as configfile:
		config.write(configfile)
	return