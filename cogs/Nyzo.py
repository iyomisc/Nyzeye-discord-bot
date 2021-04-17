"""
Nyzo specific cog
"""

from discord.ext import commands
from modules.helpers import async_get
import time
import json

BALANCES_PATH = 'api/balances.json'
MARKETS = ["citex", "qtrade", "bihodl", "qbtc", "bilaxy", "hotbit", "hoo"]  # Markets we want to list


class Nyzo(commands.Cog):
    """Basic nyzo commands"""
    def __init__(self):
        self.balances = {}
        self.last_update = 0

    async def get_all_balances(self):
        if self.last_update < time.time() - 60 * 1:  # 1 min cache
            with open(BALANCES_PATH) as f:
                self.balances = json.load(f)
            self.last_update = time.time()
        return self.balances

    @commands.command()
    async def price(self, ctx):
        """Shows Nyzo price"""

        url = "https://api.coingecko.com/api/v3/coins/nyzo/tickers"
        api = await async_get(url, is_json=True)
        sorted_api = sorted(api["tickers"], key=lambda ticker: ticker["market"]["identifier"] + " " + ticker["target"])
        prices = []
        for market in sorted_api:
            if market["market"]["identifier"] in MARKETS:
                if market["target"] == "BTC":
                    prices.append(
                        "▸ {:0.8f} BTC or {:0.3f} USD on {}".format(market["last"], market["converted_last"]["usd"],
                                                                    market["market"]["name"]))
                if market["target"] == "ETH":
                    prices.append(
                        "▸ {:0.8f} ETH or {:0.3f} USD on {}".format(market["last"], market["converted_last"]["usd"],
                                                                    market["market"]["name"]))
                if market["target"] == "USDT":
                    prices.append(
                        "▸ {:0.8f} USDT or {:0.3f} USD on {}".format(market["last"], market["converted_last"]["usd"],
                                                                     market["market"]["name"]))
                if market["target"] == "CNYT":
                    prices.append(
                        "▸ {:0.8f} CNYT or {:0.3f} USD on {}".format(market["last"], market["converted_last"]["usd"],
                                                                     market["market"]["name"]))
        prices = "\n".join(prices)
        await ctx.send("Nyzo price is:\n{}".format(prices))

    @commands.command()
    async def balanceof(self, ctx, verifier_id):
        """Shows the balance of the given identifier"""
        balances = await self.get_all_balances()
        short_id = verifier_id[:4] + "." + verifier_id[-4:]
        if short_id in balances:
            message = "Balance of {}:\n∩".format(verifier_id)
            message += str(balances[short_id][1])
        else:
            message = "No such id: {}".format(verifier_id)

        await ctx.send(message)

        """
        if short_id in balances:
            em = discord.Embed(description=balances[short_id][1], colour=discord.Colour.green())
            em.set_author(name="Balance of {}:".format(id))
            await self.bot.say(embed=em)
        else:
            em = discord.Embed(colour=discord.Colour.red())
            em.set_author(name="No such id: {}".format(id))
            await self.bot.say(embed=em)
        """
