import discord, globals, asyncio

async def genericmsg(channel,content,status,command):
	embed = discord.Embed(colour=discord.Colour(0x2C5ECA),url=globals.apiurl+"#/"+command,title="merely "+command,description=content)

	embed.set_thumbnail(url=globals.emurl+"result.gif")
	embed.set_footer(text="merely v"+globals.ver+" - created by Yiays#5930", icon_url=globals.iconurl)

	try:
		return await channel.send(embed=embed)
	except Exception:
		return await channel.send(content+"\n\n> *consider giving merely permission to embed links for a greater experience.*")

async def make_embed(channel, message, title, description='', color=0x0063B1, author='', image='', thumbnail='', fields={}, footer='', icon='', link='', **kwargs):
	em=discord.Embed(title=title, type='rich', description=description, color=color, url=link)
	if author!='': em.set_author(name=author,icon_url=icon)
	else: em.set_author(name='merely',icon_url=globals.iconurl)
	if thumbnail!='': em.set_thumbnail(url=thumbnail)
	if image!='': em.set_image(url=image)
	for field in fields:
		em.add_field(name=field+' ', value=fields[field]+' ', inline=True if len(fields[field])<8 else False)
	if footer!='': em.set_footer(text=footer,icon_url=icon)
	else: em.set_footer(text="merely v"+globals.ver+" - created by Yiays#5930")
	try:
		if 'edit' not in kwargs:
			return await channel.send(message,embed=em)
		else:
			return await kwargs['edit'].edit(content=message,embed=em)
	except Exception as e:
		print(e)
		manualfields=''
		for field in fields:
			manualfields+='**'+field+'**\n'+fields[field]+'\n\n'
		if 'edit' not in kwargs:
			return await channel.send("{}\n***{}***({})\n{}\n{}{}\n\n> *consider giving merely permission to embed links for a greater experience.*".format(message,title,link,description,manualfields,footer))
		else:
			return await kwargs['edit'].edit(content="{}\n***{}***({})\n{}\n{}{}\n\n> *consider giving merely permission to embed links for a greater experience.*".format(message,title,link,description,manualfields,footer))
