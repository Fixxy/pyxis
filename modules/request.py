import urllib, urllib.request, ssl, logging
from bs4 import BeautifulSoup
from modules import config

# get html / via proxy
def return_data(url, proxy, data, hdr, enable_proxy = True):
	timeout = int(config.get_from_config('proxy','timeout'))
	
	if (proxy == None and enable_proxy):
		proxy = config.get_from_config('proxy','proxy')
	
	proxy_tls_handler = urllib.request.HTTPSHandler(context=ssl.SSLContext(ssl.PROTOCOL_TLS))
	proxy_handler = urllib.request.ProxyHandler({'http': proxy, 'https': proxy})
	
	if enable_proxy:
		logging.debug('retrieving via proxy %s' % (proxy))
		opener = urllib.request.build_opener(proxy_tls_handler, proxy_handler)
	else:
		opener = urllib.request.build_opener(proxy_tls_handler)
	urllib.request.install_opener(opener)
	
	req = urllib.request.Request(url, data=data, headers=hdr)
	output = urllib.request.urlopen(req, timeout=timeout).read()
	return output

# get inner html from tag
def get_tag_data(html, tag, mode, classid):
	list = None
	if mode == 0: #id
		soup = BeautifulSoup(html, 'html.parser')
		list = soup.find_all(tag, id=classid)
	elif mode == 1: #class
		soup = BeautifulSoup(html, 'html.parser')
		list = soup.find_all(tag, class_=classid)
	else: #nothing
		soup = BeautifulSoup(html, 'html.parser')
		list = soup.find_all(tag)
	return list