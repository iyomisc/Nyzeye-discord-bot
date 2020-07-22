"""
Extra cogs
"""

import discord
from discord.ext import commands
from modules.helpers import async_get


class Extra(commands.Cog):
    """Useful cogs not Nyzo specific"""

    @commands.command()
    async def ping(self, ctx):
        """pong"""
        await ctx.send('Pong')

    @commands.command()
    async def bitcoin(self, ctx):
        """Shows bitcoin price"""
        # TODO: cache
        url = 'https://api.coindesk.com/v1/bpi/currentprice/BTC.json'
        """
        response = requests.get(url)
        value = response.json()['bpi']['USD']['rate']
        """
        response = await async_get(url, is_json=True)
        value = response['bpi']['USD']['rate'].replace(',', '')
        # await client.send_message(discord.Object(id='502494064420061184'), "Bitcoin price is: " + value)
        await ctx.send("Bitcoin price is {:0.2f} USD".format(float(value)))

    @commands.command()
    async def avah(self, ctx, who: discord.Member=None):
        """Show user avatar hash"""
        if who is None:
            return

        message = "User avatar hash is `{}`".format(who.avatar)
        # TODO: list other users with this hash
        await ctx.send(message)
        members = list(ctx.bot.get_all_members())
        for member in members:
            if member.avatar == who.avatar:
                await ctx.send("Found for {}".format(member.mention))
