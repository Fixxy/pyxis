import urllib, urllib.request, ssl, logging
from bs4 import BeautifulSoup
from modules import config
from external import socks
from external.sockshandler import SocksiPyHandler

# get html / via proxy
def return_data(url, proxy_ip, proxy_port, data, hdr, enable_proxy = True):
	timeout = int(config.get_from_config('proxy','timeout'))
	
	#DEBUG: in case you want to disable proxy completely:
	#enable_proxy = False
	
	if (proxy_ip == None and enable_proxy):
		proxy_ip = config.get_from_config('proxy','socks5')
		proxy_port = int(config.get_from_config('proxy','socks5_port'))
	
	proxy_tls_handler = urllib.request.HTTPSHandler(context=ssl.SSLContext(ssl.PROTOCOL_TLS))
	proxy_socks_handler = SocksiPyHandler(socks.SOCKS5, proxy_ip, proxy_port)
	
	if enable_proxy:
		logging.debug('retrieving via proxy %s:%s' % (proxy_ip, proxy_port))
		opener = urllib.request.build_opener(proxy_socks_handler, proxy_tls_handler)
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