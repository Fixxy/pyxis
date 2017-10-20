import socket, urllib, urllib.request, urllib.error, json, logging
from modules import request, config

pandora_check = ('https%smethod=test.checkLicensing' % config.get_from_config('pandora','api_url'))
hdr = {'Accept': 'text/html', 'User-Agent' : 'Fiddler'}

def find_new():
	html = request.return_data('https://www.socks-proxy.net/', None, None, None, hdr, enable_proxy = False)
	table = request.get_tag_data(html, 'table', 0, 'proxylisttable')[0].tbody
	rows = table.find_all('tr')
	for row in rows:
		r = row.find_all('td')
		print('(i) Checking new proxy %s:%s' % (r[0].get_text(),r[1].get_text()))
		try:
			proxy_ip = r[0].get_text()
			proxy_port = int(r[1].get_text())
			data = request.return_data(pandora_check, proxy_ip, proxy_port, None, hdr)
			if (json.loads(data)['result']['isAllowed'] == 1):
				print('> Found one! (%s)' % data)
				config.replace_config(r[0].get_text(), r[1].get_text())
				return
			else:
				print('> This proxy doesn\'t work (%s)')
		except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionRefusedError) as e:
			pass
	return
	
# check if old one works, if not find_new()
def setup():
	proxy_ip = config.get_from_config('proxy','socks5')
	proxy_port = int(config.get_from_config('proxy','socks5_port'))
	print('(i) Checking old proxy %s:%s' % (proxy_ip, proxy_port))
	try:
		data = request.return_data(pandora_check, proxy_ip, proxy_port, None, hdr)
		if (json.loads(data)['result']['isAllowed'] == 1):
			print('> Old proxy works! (%s)' % data)
			return
		else:
			print('> Old proxy doesn\'t work, let\'s find a new one')
			find_new()
	except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionRefusedError) as e:
		find_new()
	return