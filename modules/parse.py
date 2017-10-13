import urllib, urllib.request, ssl
from bs4 import BeautifulSoup

# get html / via proxy
def return_data(url, proxy_address, data, hdr, enable_proxy = True):
	timeout=30
	proxy_handler = urllib.request.ProxyHandler({'https': proxy_address}) if enable_proxy else urllib.request.ProxyHandler({})
	proxy_tls_handler = urllib.request.HTTPSHandler(context=ssl.SSLContext(ssl.PROTOCOL_TLS))
	
	opener = urllib.request.build_opener(proxy_handler, proxy_tls_handler)
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