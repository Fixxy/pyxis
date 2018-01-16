import socket, urllib, urllib.request, urllib.error, json, logging, math, re
from modules import request, config

pandora_check = ('https%smethod=test.checkLicensing' % config.get_from_config('pandora','api_url'))
hdr = {'Accept': 'text/html', 'User-Agent' : 'Fiddler'}

#
#TODO:
# - unify check_proxy() and setup()
# - add proxy source picker
# - 
#

def find_new():
	html = request.return_data('https://www.socks-proxy.net/', None, None, None, hdr, enable_proxy = False)
	table = request.get_tag_data(html, 'table', 0, 'proxylisttable')[0].tbody
	rows = table.find_all('tr')
	for row in rows:
		r = row.find_all('td')
		check = check_proxy(r[0].get_text(), r[1].get_text())
		if (check):
			return
	
def find_new_xroxy():
	xroxy_url = 'http://www.xroxy.com/proxylist.php?type=Socks5&ssl=ssl&country=US&sort=reliability&desc=true'
	html = request.return_data(xroxy_url, None, None, None, hdr, enable_proxy = False)
	# get number of pages
	links = request.get_tag_data(html, 'small', 1, '')
	for link in links:
		if 'proxies selected' in str(link):
			total = int(link.b.get_text())
	page_num = math.ceil(total/10)
	#print('Number of pages: %s' % page_num)
	
	for i in range(0, page_num-1):
		#print('Page #%s' % i)
		url_new = ('%s&pnum=%s' % (xroxy_url, i))
		html = request.return_data(url_new, None, None, None, hdr, enable_proxy = False)
		try:
			check = cycle_rows(html, 'row0')
			if (check):
				return
			else:
				check = cycle_rows(html, 'row1')
				if (check):
					return
		except:
			pass
	
def check_proxy(ip, port):
	print('(i) Checking new proxy %s:%s' % (ip, port))
	try:
		data = request.return_data(pandora_check, ip, int(port), None, hdr)
		if (json.loads(data)['result']['isAllowed'] == 1):
			print('> Found one! (%s)' % data)
			config.replace_config(ip, port)
			return True
		else:
			print('> This proxy doesn\'t work with Pandora.com')
	except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionRefusedError, TypeError) as e:
		print('> Exception (%s)' % e)
		pass
	
	
def cycle_rows(html, type):
	rows = request.get_tag_data(html, 'tr', 1, type)
	for row in rows:
		ip = re.search('host\=(.*?)\&', str(row.td)).group(1)
		port = re.search('port\=(.*?)\&', str(row.td)).group(1)
		check = check_proxy(ip, port)
		if (check):
			return True
	return False
	
# check if old one works, if not find_new()
def setup():
	proxy_ip = config.get_from_config('proxy','socks5')
	proxy_port = int(config.get_from_config('proxy','socks5_port'))
	print('(i) Checking old proxy %s:%s' % (proxy_ip, proxy_port))
	try:
		data = request.return_data(pandora_check, proxy_ip, proxy_port, None, hdr)
		if (json.loads(data)['result']['isAllowed'] == 1):
			print('> Old proxy works! (%s)' % data)
		else:
			print('> Old proxy doesn\'t work, let\'s find a new one')
			#find_new()
			find_new_xroxy()
	except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionRefusedError, TypeError) as e:
		print('> Exception (%s)' % e)
		#find_new()
		find_new_xroxy()