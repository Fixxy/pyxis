import urllib, urllib.request, ssl
from bs4 import BeautifulSoup

# get html / via proxy
def return_data(url, enable_proxy, proxy_address, data, hdr):
	proxy_tls_handler = urllib.request.HTTPSHandler(context=ssl.SSLContext(ssl.PROTOCOL_TLS))
	if (enable_proxy == 0) :
		proxy_handler = urllib.request.ProxyHandler({})
		timeout=120
	else:
		proxy_handler = urllib.request.ProxyHandler({'https': proxy_address})
		timeout=20
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