#!/usr/bin/env python

# WSGI-style path setup
import os,sys
sys.path.append("/home/ecanada/django")
sys.path.append("/home/ecanada/django/ircbot_app")
os.environ["DJANGO_SETTINGS_MODULE"] = "ircbot_app.settings"

# django
from ircbot.models import IRCUser, IRCHost, IRCCommand, IRCAction

# irc
from ircutils import bot, format, start_all

# python
import ConfigParser

class DjangoBot(bot.SimpleBot):
	### events ###
	#TODO: support IRCChannels
	def on_welcome(self, event):
		self.join( configs['CHANNEL'] )

		if configs['NICKSERV']:
			self.identify( configs['NS_PASS'] )

	def on_ctcp_version(self, event):
		self.send_ctcp_reply(event.source, "VERSION", ["LeelaBot v0"])

	#TODO: remove core logic from event handler
	def on_message(self, event):
		actions = IRCAction.objects.filter(performed=False)
		for each in actions:
			c = each.command.command.split()
			if c[0] == "MODE":
				self.execute( str(c[0]), str(event.target), str(c[1]), str(each.args) )
			else:
				if len(each.args) == 1:
					self.execute( str(c[0]), str(event.target), str(each.args) )
				else:
					qargs = each.args.split("\"")
					#TODO: I hate this.
					if len(qargs) == 1:
						if each.command.color:
							self.execute( str(c[0]), str(event.target), trailing=format.color(str(qargs[0]), format.RED) )
						else:
							self.execute( str(c[0]), str(event.target), trailing=str(qargs[0]) )
					else:
						if each.command.color:
							self.execute( str(c[0]), str(event.target), str(qargs[0]), trailing=str(qargs[1]) )
						else:
							self.execute( str(c[0]), str(event.target), str(qargs[0]), trailing=format.color(str(qargs[1]), format.RED) )
			each.performed = True
			each.save()

	def on_join(self, event):
		users = IRCUser.objects.filter(irchost__hostname=event.host)

		if users:
			user = users[0]
			if user.automode:
				c = user.automode.command.command.split()
				self.execute( str(c[0]), str(event.target), str(c[1]), str(event.source) )

def config_parsing():
	# open config file
	try:
		config = ConfigParser.ConfigParser()
		config.read('bot.cfg')
	except:
		print "configuration file could not be opened!"
		print sys.exc_info()
		sys.exit(1)

	# read configuration settings
	configs = {}
	try:
	# database
		configs['NICK'] = config.get('irc', 'nick')
		configs['SERVER'] = config.get('irc', 'server')
		configs['CHANNEL'] = config.get('irc', 'channel')
		configs['NICKSERV'] = config.get('irc', 'nickserv')
		configs['NS_PASS'] = config.get('irc', 'ns_pass')
	except:
		print "invalid or incomplete configuration data provided."
		print sys.exc_info()
		sys.exit(1)

	return configs


if __name__ == "__main__":
	configs = config_parsing()

	bot = DjangoBot( configs['NICK'] )
	bot.connect( configs['SERVER'] )
	bot.start()
