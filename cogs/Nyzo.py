"""
Nyzo specific cog
"""

from discord.ext import commands
from modules.helpers import async_get


class Nyzo:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='price', brief="Shows Nyzo price", pass_context=True)
    async def price(self, ctx):
        MARKETS = ["citex", "qtrade"]  # Markets we want to list
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
        prices = "\n".join(prices)
        await self.bot.say("Nyzo price is:\n{}".format(prices))
