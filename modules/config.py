import configparser
config_file = 'pyxis.ini'

# get proxy from config file
def get_from_config(s, p):
	config = configparser.ConfigParser()
	config.read(config_file)
	value = config[s][p]
	return value
	
# get old / set new authpartnertoken
def last_authtoken(token, type, get = True):
	config = configparser.ConfigParser()
	config.read(config_file)
	if get:
		last_authtoken = config['pandora'][type]
	else:
		config['pandora'][type] = token
		with open(config_file, 'w') as configfile:
			config.write(configfile)
		last_authtoken = token
	return last_authtoken
	
# replace proxy
def replace_config(proxy_ip, proxy_port):
	config = configparser.ConfigParser()
	config.read(config_file)
	config['proxy']['socks5'] = proxy_ip
	config['proxy']['socks5_port'] = proxy_port
	with open(config_file, 'w') as configfile:
		config.write(configfile)
	return