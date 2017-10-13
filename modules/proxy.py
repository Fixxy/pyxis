import re, socket, urllib, urllib.request, urllib.error
from modules import parse

proxy_string = testHTML = None
pianobar_cfg = 'pianobar.cfg'
website = 'https://pandora.com'
hdr = {'Accept': 'text/html', 'User-Agent' : 'Fiddler'}

def find_new():
	html = parse.return_data('https://www.us-proxy.org/', '', None, hdr, enable_proxy = True)
	table = parse.get_tag_data(html, 'table', 0, 'proxylisttable')[0].tbody
	rows = table.find_all('tr')
	for row in rows:
		r = row.find_all('td')
		print('Checking: %s:%s' % (r[0].get_text(),r[1].get_text()))
		try:
			address = r[0].get_text() + ':' +  r[1].get_text()
			testHTML = parse.return_data(website, address, None, hdr)
			print('it works (%s)' % website)
			replace_config(pianobar_cfg, proxy_string, ('https://%s:%s' % (r[0].get_text(), r[1].get_text())))
			break
		except (urllib.error.URLError, socket.timeout, TimeoutError) as e:
			print('this one doesn\'t work (%s)' % e)
	return address
	
# get proxy from config file
def get_from_config():
	file = open(pianobar_cfg,'r')
	config = file.readlines()
	file.close()
	
	for s in range(0, len(config)):
		if config[s].startswith('control_proxy'):
			global proxy_string
			proxy_string = s
			print('Found (%s): %s' % (s, config[s].strip()))
			proxy = re.search('^control_proxy \= (.*?)$', config[s]).group(1)
	return proxy
	
# check if old one works, if not find_new()
def setup():
	proxy = get_from_config()
	print('Checking %s' % proxy)
	try:
		testHTML = parse.return_data(website, proxy, None, hdr)
		print('old proxy works')
		
	except:
		print('old proxy doesn\'t work, let\'s find a new one')
		proxy = find_new()
	
	return
	
# replace proxy
def replace_config(filename, string, proxy):
	file = open(filename,'r')
	data = file.readlines()
	data[string] = ('control_proxy = %s\n' % proxy)
	file.close()
	file = open(filename,'w')
	file.writelines(data)
	file.close()
	return