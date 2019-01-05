#!/usr/bin/env python3
#

if __name__ == '__main__':
	items = (
		'home_latitude',
		'home_longitude',
		'http_password',
		'mqtt_username',
		'mqtt_password',
		'tomato_username',
		'tomato_password',
		'darsky_api_key',
		'telegram_api_key',
		'telegram_chat_id',
		'pushover_api_key',
		'pushover_user_key'
	)
	
	for item in items:
		print('%s: dummy' % (item))
