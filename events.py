import asyncio

def events(bot):
	# Some events are not included for security purposes
	bot.events={'on_connect':[],
							'on_disconnect':[],
							'on_ready':[],
							'on_shard_ready':[],
							'on_resumed':[],
							'on_error':[],
							'on_socket_raw_receive':[],
							'on_socket_raw_send':[],
							'on_typing':[],
							'on_message':[],
							'on_message_delete':[],
							'on_bulk_message_delete':[],
							'on_raw_message_delete':[],
							'on_raw_bulk_message_delete':[],
							'on_message_edit':[],
							'on_raw_message_edit':[],
							'on_reaction_add':[],
							'on_raw_reaction_add':[],
							'on_reaction_remove':[],
							'on_raw_reaction_remove':[],
							'on_reaction_clear':[],
							'on_raw_reaction_clear':[],
							'on_reaction_clear_emoji':[],
							'on_raw_reaction_clear_emoji':[],
							'on_private_channel_delete':[],
							'on_private_channel_create':[],
							'on_private_channel_update':[],
							'on_private_channel_pins_update':[],
							'on_guild_channel_delete':[],
							'on_guild_channel_create':[],
							'on_guild_channel_update':[],
							'on_guild_channel_pins_update':[],
							'on_guild_integrations_update':[],
							'on_webhooks_update':[],
							'on_member_join':[],
							'on_member_remove':[],
							'on_member_update':[],
							'on_user_update':[],
							'on_guild_join':[],
							'on_guild_remove':[],
							'on_guild_update':[],
							'on_guild_role_create':[],
							'on_guild_role_delete':[],
							'on_guild_role_update':[],
							'on_guild_emojis_update':[],
							'on_guild_available':[],
							'on_guild_unavailable':[],
							'on_voice_state_update':[],
							'on_member_ban':[],
							'on_member_unban':[],
							'on_invite_create':[],
							'on_invite_delete':[]
							}

	@bot.event
	async def on_connect():
		for func in bot.events['on_connect']:
			asyncio.ensure_future(func())

	@bot.event
	async def on_disconnect():
		for func in bot.events['on_disconnect']:
			asyncio.ensure_future(func())

	@bot.event
	async def on_ready():
		for func in bot.events['on_ready']:
			asyncio.ensure_future(func())

	@bot.event
	async def on_shard_ready(shard_id):
		for func in bot.events['on_shard_ready']:
			asyncio.ensure_future(func(shard_id))

	@bot.event
	async def on_resumed():
		for func in bot.events['on_resumed']:
			asyncio.ensure_future(func())

	@bot.event
	async def on_error(event, *args, **kwargs):
		raise #TODO: get this working
		#for func in bot.events['on_error']:
			#asyncio.ensure_future(func(event, *args, **kwargs))

	@bot.event
	async def on_socket_raw_receive(msg):
		for func in bot.events['on_socket_raw_receive']:
			asyncio.ensure_future(func(msg))

	@bot.event
	async def on_socket_raw_send(payload):
		for func in bot.events['on_socket_raw_send']:
			asyncio.ensure_future(func(payload))

	@bot.event
	async def on_typing(channel, user, when):
		for func in bot.events['on_typing']:
			asyncio.ensure_future(func(channel, user, when))

	@bot.event
	async def on_message(message):
		for func in bot.events['on_message']:
			asyncio.ensure_future(func(message))

	@bot.event
	async def on_message_delete(message):
		for func in bot.events['on_message_delete']:
			asyncio.ensure_future(func(message))

	@bot.event
	async def on_bulk_message_delete(messages):
		for func in bot.events['on_bulk_message_delete']:
			asyncio.ensure_future(func(messages))

	@bot.event
	async def on_raw_message_delete(payload):
		for func in bot.events['on_raw_message_delete']:
			asyncio.ensure_future(func(payload))

	@bot.event
	async def on_raw_bulk_message_delete(payload):
		for func in bot.events['on_raw_bulk_message_delete']:
			asyncio.ensure_future(func(payload))

	@bot.event
	async def on_message_edit(before, after):
		for func in bot.events['on_message_edit']:
			asyncio.ensure_future(func(before, after))

	@bot.event
	async def on_raw_message_edit(payload):
		for func in bot.events['on_raw_message_edit']:
			asyncio.ensure_future(func(payload))

	@bot.event
	async def on_reaction_add(reaction, user):
		for func in bot.events['on_reaction_add']:
			asyncio.ensure_future(func(reaction, user))

	@bot.event
	async def on_raw_reaction_add(payload):
		for func in bot.events['on_raw_reaction_add']:
			asyncio.ensure_future(func(payload))

	@bot.event
	async def on_reaction_remove(reaction, user):
		for func in bot.events['on_reaction_remove']:
			asyncio.ensure_future(func(reaction, user))

	@bot.event
	async def on_raw_reaction_remove(payload):
		for func in bot.events['on_raw_reaction_remove']:
			asyncio.ensure_future(func(payload))

	@bot.event
	async def on_reaction_clear(message, reactions):
		for func in bot.events['on_reaction_clear']:
			asyncio.ensure_future(func(message, reactions))

	@bot.event
	async def on_raw_reaction_clear(payload):
		for func in bot.events['on_raw_reaction_clear']:
			asyncio.ensure_future(func(payload))

	@bot.event
	async def on_reaction_clear_emoji(reaction):
		for func in bot.events['on_reaction_clear_emoji']:
			asyncio.ensure_future(func(reaction))

	@bot.event
	async def on_raw_reaction_clear_emoji(payload):
		for func in bot.events['on_raw_reaction_clear_emoji']:
			asyncio.ensure_future(func(payload))

	@bot.event
	async def on_private_channel_delete(channel):
		for func in bot.events['on_private_channel_delete']:
			asyncio.ensure_future(func(channel))

	@bot.event
	async def on_private_channel_create(channel):
		for func in bot.events['on_private_channel_create']:
			asyncio.ensure_future(func(channel))

	@bot.event
	async def on_private_channel_update(before, after):
		for func in bot.events['on_private_channel_update']:
			asyncio.ensure_future(func(before, after))

	@bot.event
	async def on_private_channel_pins_update(channel, last_pin):
		for func in bot.events['on_private_channel_pins_update']:
			asyncio.ensure_future(func(channel, last_pin))

	@bot.event
	async def on_guild_channel_delete(channel):
		for func in bot.events['on_guild_channel_delete']:
			asyncio.ensure_future(func(channel))

	@bot.event
	async def on_guild_channel_create(channel):
		for func in bot.events['on_guild_channel_create']:
			asyncio.ensure_future(func(channel))

	@bot.event
	async def on_guild_channel_update(before, after):
		for func in bot.events['on_guild_channel_update']:
			asyncio.ensure_future(func(before, after))

	@bot.event
	async def on_guild_channel_pins_update(channel, last_pin):
		for func in bot.events['on_guild_channel_pins_update']:
			asyncio.ensure_future(func(channel, last_pin))

	@bot.event
	async def on_guild_integrations_update(guild):
		for func in bot.events['on_guild_integrations_update']:
			asyncio.ensure_future(func(guild))

	@bot.event
	async def on_webhooks_update(channel):
		for func in bot.events['on_webhooks_update']:
			asyncio.ensure_future(func(channel))

	@bot.event
	async def on_member_join(member):
		for func in bot.events['on_member_join']:
			asyncio.ensure_future(func(member))

	@bot.event
	async def on_member_remove(member):
		for func in bot.events['on_member_remove']:
			asyncio.ensure_future(func(member))

	@bot.event
	async def on_member_update(before, after):
		for func in bot.events['on_member_update']:
			asyncio.ensure_future(func(before, after))

	@bot.event
	async def on_user_update(before, after):
		for func in bot.events['on_user_update']:
			asyncio.ensure_future(func(before, after))

	@bot.event
	async def on_guild_join(guild):
		for func in bot.events['on_guild_join']:
			asyncio.ensure_future(func(guild))

	@bot.event
	async def on_guild_remove(guild):
		for func in bot.events['on_guild_remove']:
			asyncio.ensure_future(func(guild))

	@bot.event
	async def on_guild_update(before, after):
		for func in bot.events['on_guild_update']:
			asyncio.ensure_future(func(before, after))

	@bot.event
	async def on_guild_role_create(role):
		for func in bot.events['on_guild_role_create']:
			asyncio.ensure_future(func(role))

	@bot.event
	async def on_guild_role_delete(role):
		for func in bot.events['on_guild_role_delete']:
			asyncio.ensure_future(func(role))

	@bot.event
	async def on_guild_role_update(before, after):
		for func in bot.events['on_guild_role_update']:
			asyncio.ensure_future(func(before, after))

	@bot.event
	async def on_guild_emojis_update(guild, before, after):
		for func in bot.events['on_guild_emojis_update']:
			asyncio.ensure_future(func(guild, before, after))

	@bot.event
	async def on_guild_available(guild):
		for func in bot.events['on_guild_available']:
			asyncio.ensure_future(func(guild))

	@bot.event
	async def on_guild_unavailable(guild):
		for func in bot.events['on_guild_unavailable']:
			asyncio.ensure_future(func(guild))

	@bot.event
	async def on_voice_state_update(member, before, after):
		for func in bot.events['on_voice_state_update']:
			asyncio.ensure_future(func(member, before, after))

	@bot.event
	async def on_member_ban(guild, user):
		for func in bot.events['on_member_ban']:
			asyncio.ensure_future(func(guild, user))

	@bot.event
	async def on_member_unban(guild, user):
		for func in bot.events['on_member_unban']:
			asyncio.ensure_future(func(guild, user))

	@bot.event
	async def on_invite_create(invite):
		for func in bot.events['on_invite_create']:
			asyncio.ensure_future(func(invite))

	@bot.event
	async def on_invite_delete(invite):
		for func in bot.events['on_invite_delete']:
			asyncio.ensure_future(func(invite))