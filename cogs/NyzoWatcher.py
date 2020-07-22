"""
NyzoWatcher cogs
"""

import json
import os
import sys
from discord.ext import commands
from modules.WatchDB import WatchDb
import time

STATUS_PATH = 'api/status.json'
LAST_NAME_UPDATE = 0


class NyzoWatcher(commands.Cog):
    """Nyzo verifier specific Commands"""

    def __init__(self):
        os.makedirs("data", exist_ok=True)
        self.watch_module = WatchDb()

    @staticmethod
    async def status():
        """live status"""
        with open(STATUS_PATH, 'r') as f:
            return json.load(f)

    @staticmethod
    def fill(text, final_length, char=" "):
        return text + char * (final_length - len(text))

    @commands.command()
    async def watch(self, ctx, *verifiers):
        """Adds a verifier to the watch list and warn via PM when down"""
        try:
            status = await self.status()
            await ctx.send("Verifiers:")
            for verifier in verifiers:
                if verifier:
                    verifier = verifier[:4] + "." + verifier[-4:]
                    if verifier not in status:
                        msg = "No known Verifier with id {}\n".format(verifier)
                    else:
                        self.watch_module.watch(ctx.message.author.id, verifier, status)
                        msg = "Added {}\n".format(verifier)
                    await ctx.send(msg)

        except Exception as e:
            print(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

    @commands.command()
    async def recover(self, ctx, *verifiers):
        """Allows to recover your watch list with the nyzeye list"""
        to_watch = []
        try:
            for verifier in verifiers:
                if len(verifier) == 9 and verifier[4] == ".":
                    to_watch.append(verifier)
            await self.watch(ctx, *to_watch)

        except Exception as e:
            print(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

    @commands.command()
    async def unwatch(self, ctx, *verifiers):
        """Removes a verifier from the watch list"""
        await ctx.send("Verifiers:")
        for verifier in verifiers:
            if verifier:
                verifier = verifier[:4] + "." + verifier[-4:]
                self.watch_module.unwatch(ctx.author.id, verifier)
                msg = "Removed {}\n".format(verifier)
                await ctx.send(msg)

    @commands.command()
    async def list(self, ctx, param=""):
        """shows your watch list"""
        if ctx.guild is not None:
            await ctx.send("You can only see your watch list in private chat with me.")
            return

        status = await self.status()
        verifier_list = self.watch_module.get_list(ctx.author.id, param=param)
        balances = await ctx.bot.cogs["Nyzo"].get_all_balances()

        msg = "You are watching {} {} verifier".format(len(verifier_list), param)
        if len(verifier_list) != 1:
            msg += "s"
        msg += "\n"
        total_balance = 0
        for index, verifier in enumerate(verifier_list):
            char = "-"
            icon = "?"
            if verifier[0] in status:
                if status[verifier[0]][0] >= 2:
                    char = "❌"
                balance = balances.get(verifier[0], [None, 0])[1]
                total_balance += balance
                if status[verifier[0]][2] == 0:
                    icon = "🕐"
                else:
                    icon = "✅"
                text = "`{} {}{} ∩{} {} | {}`".format(char, self.fill(verifier[0], 10), icon,
                                                      self.fill(str(balance), 15),
                                                      str(status[verifier[0]][0]), verifier[2])
                if status[verifier[0]][0] >= 2:
                    text = "**" + text + "**"
            else:
                print(" Unknown ", verifier[0])
                char = "?"
                balance = balances.get(verifier[0], [None, 0])[1]
                total_balance += balance
                text = "`{} {}{} ∩{} {} | {}`".format(char, self.fill(verifier[0], 10), icon,
                                                      self.fill(str(balance), 15), "?", verifier[2])

            msg += text + "\n"
            if not (index + 1) % 20:
                await ctx.send(msg)
                msg = ""
        msg += "Total balance: ∩{:0.2f}".format(total_balance)
        await ctx.send(msg)

    async def background_task(self, bot=None):
        status = await self.status()
        await self.watch_module.update_verifiers_status(status, bot)
        await self.watch_module.get_verifiers_status(bot)
        if time.time() > LAST_NAME_UPDATE + 3600:
            await self.watch_module.update_nickname(status)
