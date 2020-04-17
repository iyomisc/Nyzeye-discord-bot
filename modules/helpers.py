"""
Helpers for the Nyzeye discord bot
"""
from datetime import datetime

import aiohttp
from discord.ext import commands
from json import loads as json_loads

def ts_to_string(timestamp):
    return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')


HTTP_SESSION = None


async def async_get(url, is_json=False):
    """Async gets an url content.

    If is_json, decodes the content
    """
    global HTTP_SESSION
    if not HTTP_SESSION:
        HTTP_SESSION = aiohttp.ClientSession()
    # async with aiohttp.ClientSession() as session:
    async with HTTP_SESSION.get(url) as resp:
        if is_json:
            return json_loads(await resp.text())
        else:
            return await resp.text()


def is_channel(channel_id):
    """No more used, kept for history"""
    def predicate(ctx):
        # print("server", ctx.message.server)
        if not ctx.message.server:
            # server = None means PM
            return True
        # print("Channel id {} private {}".format(ctx.message.channel.id, ctx.message.channel.is_private))
        return ctx.message.channel.id in channel_id
    return commands.check(predicate)

