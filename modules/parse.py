import urllib, urllib.request, ssl, socket
from bs4 import BeautifulSoup
from modules import proxy, socks
from modules.sockshandler import SocksiPyHandler

# get html / via proxy
def return_data(url, proxy_ip, proxy_port, data, hdr, enable_proxy = True):
	timeout=30
	if (proxy_ip == None and enable_proxy):
		proxy_ip, proxy_port = proxy.get_from_config()
	
	proxy_tls_handler = urllib.request.HTTPSHandler(context=ssl.SSLContext(ssl.PROTOCOL_TLS))
	
	proxy_socks_handler = SocksiPyHandler(socks.SOCKS5, proxy_ip, proxy_port)
	
	if enable_proxy:
		print('retrieving via proxy %s:%s' % (proxy_ip, proxy_port))
		opener = urllib.request.build_opener(proxy_socks_handler, proxy_tls_handler)
	else:
		opener = urllib.request.build_opener(proxy_tls_handler)
	
	#opener = urllib.request.build_opener(proxy_tls_handler)
	
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