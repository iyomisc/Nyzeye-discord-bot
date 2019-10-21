"""
Nyzeye Discord Bot for Nyzo Cryptocurrency
"""

import asyncio
from discord.ext import commands
from cogs.NyzoWatcher import NyzoWatcher
from cogs.Nyzo import Nyzo
from modules.config import CONFIG, SHORTCUTS

__version__ = '0.10'

BOT_PREFIX = 'Nyzeye '

client = commands.Bot(command_prefix=BOT_PREFIX)


@client.event
async def on_ready():
    """
    This function is not guaranteed to be the first event called.
    Likewise, this function is not guaranteed to only be called once.
    This library implements reconnection logic and thus will end up calling this event whenever a RESUME request fails.
    """
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

    
    await client.send_message(client.get_channel(CONFIG['bot_channel'][0]), "I just restarted, if one of your commands "
                                                                            "didn't get an answer, just resend it.")

    # 625345529639075872
    #await client.http.delete_message(CONFIG['bot_channel'][0], '625345529639075872')

@client.event
async def on_message(message):
    """Called when a message is created and sent to a server."""
    for search, replace in SHORTCUTS.items():
        if message.content.startswith(search):
            message.content = message.content.replace(search, replace)

    if not message.content.startswith(BOT_PREFIX):
        return
    if client.user.id != message.author.id:  # check not a bot message
        print("Got {} from {}".format(message.content, message.author.display_name))
    if message.content.startswith('Pawer tip'):
        await client.process_commands(message)
        return
    if message.server and message.channel.id not in CONFIG['bot_channel']:
        print('Unauth channel')
    else:
        await client.add_reaction(message, '⏳')  # Hourglass
        try:
            # only here, will process commands
            await client.process_commands(message)
        finally:
            await client.remove_reaction(message, '⏳', client.user)  # Hourglass


@client.command(name='about', brief="Nyzeye bot general info", pass_context=True)
async def about(ctx):
    await client.say(
        "Nyzeye bot Version {}\nI'm your Nyzo butler. Type `Nyzeye help` for a full commands list.".format(__version__))


async def background_task(cog_list):
    await client.wait_until_ready()
    while not client.is_closed:
        for cog in cog_list:
            try:
                await cog.background_task()
            except Exception as e:
                print(e)
        await asyncio.sleep(60)


if __name__ == '__main__':
    nyzo_watcher = NyzoWatcher(client)
    client.add_cog(nyzo_watcher)
    client.add_cog(Nyzo(client))

    client.loop.create_task(background_task([nyzo_watcher]))

    client.run(CONFIG['token'])
