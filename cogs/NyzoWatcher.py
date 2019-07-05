"""
NyzoWatcher cogs
"""

import json
import os
import sys
import discord
from discord.ext import commands
from modules.WatchDB import WatchDb

STATUS_PATH = 'api/status.json'


class NyzoWatcher:
    """Nyzo verifier specific Cogs"""

    def __init__(self, bot):
        os.makedirs("data", exist_ok=True)
        self.bot = bot
        self.bot.watch_module = WatchDb()

    async def status(self):
        """live status"""
        with open(STATUS_PATH, 'r') as f:
            return json.load(f)

    @commands.command(name='watch', brief="Add a verifier to the watch list and warn via PM when down",
                      pass_context=True)
    async def watch(self, ctx, *verifiers):
        """Adds a verifier to watch"""
        try:
            status = await self.status()
            await self.bot.say("Verifiers:")
            for verifier in verifiers:
                if verifier:
                    verifier = verifier[:4] + "." + verifier[-4:]
                    if verifier not in status:
                        msg = "No known Verifier with id {}\n".format(verifier)
                    else:
                        self.bot.watch_module.watch(ctx.message.author.id, verifier, status)
                        msg = "Added {}\n".format(verifier)
                    await self.bot.say(msg)

        except Exception as e:
            print(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

    @commands.command(name='unwatch', brief="Removes an verifier from the watch list", pass_context=True)
    async def unwatch(self, ctx, *verifiers):
        """Removes an verifier from the watch list"""
        await self.bot.say("Verifiers:")
        for verifier in verifiers:
            if verifier:
                verifier = verifier[:4] + "." + verifier[-4:]
                self.bot.watch_module.unwatch(ctx.message.author.id, verifier)
                msg = "Removed {}\n".format(verifier)
                await self.bot.say(msg)

    def fill(self, text, final_length, char=" "):
        return text + char * (final_length - len(text))

    @commands.command(name='list', brief="shows your watch list", pass_context=True)
    async def list(self, ctx):
        """print the current list"""
        status = await self.status()
        verifier_list = self.bot.watch_module.get_list(ctx.message.author.id)
        balances = await self.bot.cogs["Nyzo"].get_all_balances()

        msg = "You are watching {} verifier".format(len(verifier_list))
        if len(verifier_list) != 1:
            msg += "s"
        msg += "\n"
        total_balance = 0
        for index, verifier in enumerate(verifier_list):
            char = "-"
            if status[verifier[0]][0] >= 2:
                char = "▸"
            balance = balances.get(verifier[0], [None, 0])[1]
            total_balance += balance
            text = "`{} {}  ∩{} {} | {}`".format(char, self.fill(verifier[0], 10), self.fill(str(balance), 15),
                                                 str(status[verifier[0]][0]), verifier[2])
            if status[verifier[0]][0] >= 2:
                text = "**" + text + "**"
            msg += text + "\n"
            if not (index + 1) % 20:
                await self.bot.say(msg)
                msg = ""
        msg += "Total balance: ∩{:0.2f}".format(total_balance)
        await self.bot.say(msg)

    async def background_task(self):
        status = await self.status()
        await self.bot.watch_module.update_verifiers_status(status, self.bot)
        await self.bot.watch_module.get_verifiers_status(self.bot)
