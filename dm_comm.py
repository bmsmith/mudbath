import dm_global, dm_ansi, datetime

CHANNELS = {}


def load_channels():
	channels_d = dm_global.db_conn.execute_query("SELECT name, active, private FROM channels;")

	for channel_data in channels_d:
		CHANNELS[channel_data[0]] = Channel(channel_data[0], channel_data[1], channel_data[2])


class Channel:
	def __init__(self, name, active=True, private=False):
		self.name = name
		self.users = []
		self.hushed_users = []
		self.gagged_users = []
		self.banned_users = []
		self.private = private
		self.CHANNEL_COMMANDS = {
			'ban': (self.ban, "/ban - Bans a specific user.", dm_global.MODERATOR),
			'hush': (self.hush, "/hush - Hushes a particular user, which prevents user from sending messages", dm_global.MODERATOR),
			'gag': (self.gag, "/gag - Gags a user, which is like a shadowban", dm_global.MODERATOR)
		}
		CHANNELS[name] = self
	def unplug_user(self, user):
		"""
		Unplug a user from the channel.
		"""
		if user in self.users:
			self.users.remove(user)
			self.broadcast("%sUser %s disconnected%s from %s" % (dm_ansi.RED, account_name, self.name, dm_ansi.CLEAR))
			return "User successfully disconnected from channel"
		else:
			return "User not connected to channel"
	def broadcast(self, message, exceptions=[]):
		"""
		Send a message to everyone!
		"""
		for user in self.users:
			if user is None:
				self.users.remove(user)
			elif user not in exceptions:
				user.client.send(message)
		return "Message broadcast successfully"
	def hush(self, user):
		"""
		Hush user so they can still see messages but not send them. 
		"""
		if user in self.hushed_users:
			return "User already hushed"
		else:
			self.hushed_users.append(user)
			return "User hushed"
	def plug(self, user):
		"""
		Plug a user into the channel
		"""
		if user in self.banned_users:
			return "User is banned"
		elif user in self.users:
			return "User already in channel"
		else:
			self.users.append(user)
			self.broadcast("User %s has joined channel %s\n" % (user.a_account_name, self.name))
			
	def gag(self, user):
		"""
		Gag is like shadowban
		"""
		if user in self.gagged_users:
			return "User is already gagged!"
		else:
			self.gagged_users.append(user)
			return "Gagged"

	def ban(self, user):
		"""
		BAN HAMMER!
		"""
		if user in self.users:
			self.unplug_user(user)
		if user in self.banned_users:
			return "User already banned"
		else:
			self.banned_users.append(user)
			return "User added to banlist"
	def format_message(self, message, user, is_me=False):
		usertag = ""
		if is_me:
			usertag = "*%s " % (user.a_account_name)
		else:
			usertag = "%s: " % (user.a_account_name)
		return "%s(%s)%s[%s]%s%s%s%s" % (dm_ansi.BGREEN + dm_ansi.BOLD + dm_ansi.WHITE, self.name, dm_ansi.CLEAR, datetime.datetime.now().strftime("%X"), dm_ansi.YELLOW + dm_ansi.BOLD, usertag, dm_ansi.CLEAR, message + "\n")
	def msg(self, message, user):
		"""
		Called when a user sends a message
		"""
		message.lstrip()
		if user in self.hushed_users:
			return "You're not able to send messages to that channel!"
		elif user in self.gagged_users:
			return self.format_message(message, user) # Gagged user can't see that they're banned.
		elif user.silenced:
			return "You have been silenced. Please contact an admin."
		elif len(message) > 0:
			if message[0] == '/':
				command = ""
				args = ""
				space_index = message.find(' ')
				if space_index == -1:
					command = message[1:]
				else:
					command = message[1:space_index]
					args = message[space_index + 1:]
				if command in self.CHANNEL_COMMANDS:
					user.client.send(self.CHANNEL_COMMANDS[command][0](args))
					return
			self.broadcast(self.format_message(message, user))
			dm_global.db_conn.log_channel(user.a_account_name, self.name, message)
			return ""
		else:
			return "Type in a message after the channel name. Example: '%s Hello!'" % (self.name)
	def handle_input(self, message, user):
		if user in self.users:
			return self.msg(message, user)
		else:
			return "You're not connected to that channel!"
