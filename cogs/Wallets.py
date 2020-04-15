"""
Nyzo specific cog
"""

from discord.ext import commands
from modules.database import Db
import time
import json
import discord

DB_PATH = 'data/wallets.db'


class Wallet:
    def __init__(self, bot):
        self.bot = bot
        self.db = Db(DB_PATH)
        self.db.execute("CREATE TABLE IF NOT EXISTS balances(user_id TEXT PRIMARY KEY, balance INT DEFAULT 0)")
        self.db.execute("CREATE TABLE IF NOT EXISTS transactions(sender TEXT, recipient TEXT, amount INT, "
                        "fee INT DEFAULT 0, type TEXT, offchain BOOL DEFAULT 1, id TEXT, timestamp INT)")

    async def safe_send_message(self, recipient, message):
        try:
            await self.bot.send_message(recipient, message)
        except Exception as e:
            print(e)

    def insert_transaction(self, sender, recipient, amount, tx_type, offchain=True, fee=0, tx_id=None):
        if offchain:
            if amount <= 0:
                return False

            if sender == recipient:
                return False
            if self.get_balance(sender) < amount + fee:
                return False
            self.update_balance(sender, -(amount + fee))
            self.update_balance(recipient, amount)

        self.db.execute("INSERT INTO transactions(sender, recipient, amount, fee, type, offchain, id, timestamp) "
                        "values(?,?,?,?,?,?,?,?)",
                        (str(sender), str(recipient), amount, fee, tx_type, offchain, tx_id, int(time.time())))
        return True

    def update_balance(self, user_id, value):
        balance = self.get_balance(str(user_id))
        self.db.execute("REPLACE INTO balances(user_id, balance) values(?, ?)", (str(user_id), balance + value))

    def get_balance(self, user_id):
        balance = self.db.get_firsts("SELECT balance from balances WHERE user_id=?", (str(user_id),))
        if not len(balance):
            return 0
        return balance[0]

    @commands.command(name='balance', brief="Shows your balance", pass_context=True)
    async def balance(self, ctx):
        balance = self.get_balance(str(ctx.message.author.id))
        await self.bot.say("You have ∩{:0.6f}".format(balance/10**6))

    @commands.command(name='tip', brief="Usage: '!tip @user amount' if not specified, amount=1, Send some nyzo to another user", pass_context=True)
    async def tip(self, ctx, user: discord.Member, amount: str='1'):
        if self.insert_transaction(str(ctx.message.author.id), str(user.id), float(amount) * 10 ** 6, "tip"):
            await self.bot.add_reaction(ctx.message, '👍')
            await self.safe_send_message(user, "You've been tipped ∩{:0.6f} by <@!{}> ({})!"
                                         .format(float(amount), ctx.message.author.id, ctx.message.author.display_name))
        else:
            await self.bot.add_reaction(ctx.message, '👎')


