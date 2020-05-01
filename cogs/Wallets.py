"""
Nyzo specific cog
"""

from discord.ext import commands
from modules.database import Db
from math import floor, ceil
from nyzostrings.nyzostringprefilleddata import NyzoStringPrefilledData
from nyzostrings.nyzostringencoder import NyzoStringEncoder
from modules.helpers import async_get
from modules.config import CONFIG
import time
import json
import discord


DB_PATH = 'data/wallets.db'
MAIN_ADDRESS = "b34b3320b0291be2cd063f049bdef05ba57f313a60c173c3abce4b770e4e10b5"
MAIN_ID = "id__8bdbcQ2NahMzRgp_19Mv-5LCwR4Ypc5RNYMeiVtejy2TGnPC3AqE"
LAST_HEIGHT_FILE = "data/last_height.txt"

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
        elif tx_type == "deposit":
            self.update_balance(recipient, amount)

        self.db.execute("INSERT INTO transactions(sender, recipient, amount, fee, type, offchain, id, timestamp) "
                        "values(?,?,?,?,?,?,?,?)",
                        (str(sender), str(recipient), amount, fee, tx_type, offchain, tx_id, int(time.time())))
        return True

    def deposit_transaction(self, amount, discord_id, signature, sender):
        if len(self.db.get_firsts("SELECT id FROM transactions WHERE id=?", (signature, ))):
            return False

        return self.insert_transaction(sender, discord_id, amount, "deposit", offchain=False, tx_id=signature)

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
        if self.insert_transaction(str(ctx.message.author.id), str(user.id), floor(float(amount) * 10 ** 6), "tip"):
            await self.bot.add_reaction(ctx.message, '👍')
            await self.safe_send_message(user, "You've been tipped ∩{:0.6f} by {} ({})!"
                                         .format(float(amount), ctx.message.author.mention, ctx.message.author.display_name))
        else:
            await self.bot.add_reaction(ctx.message, '👎')

    @commands.command(name='deposit', brief="Used to deposit Nyzo on you account", pass_context=True)
    async def deposit(self, ctx, block_id: int=-1):
        if block_id != -1:
            count = 0
            successed = 0
            result = await async_get("{}/block/{}".format(CONFIG["api_url"], block_id), is_json=True)
            for block in result:
                for transaction in block["value"]["transactions"]:
                    if transaction["value"]["receiver_identifier"] == MAIN_ADDRESS and transaction["value"]["sender_data"]:
                        count += 1
                        if self.deposit_transaction(transaction["value"]["amount"] - ceil(transaction["value"]["amount"] * 0.0025), bytes.fromhex(transaction["value"]["sender_data"]).decode("utf-8"), transaction["value"]["signature"], transaction["value"]["sender_identifier"]):
                            successed += 1
            await self.bot.say("{} deposit transactions found in block {}\nSuccessfuly processed {}".format(count, block_id, successed))
        else:
            nyzostring = NyzoStringEncoder.encode(NyzoStringPrefilledData.from_hex(MAIN_ADDRESS, str(ctx.message.author.id).encode().hex()))
            await self.bot.say("To deposit nyzo on your account, send a transaction to `{}` with `{}` in the data field\nOr use this nyzostring: `{}`\nYour balance will be updated a minute later.".format(MAIN_ID, ctx.message.author.id, nyzostring))

    async def background_task(self):

        try:
            with open(LAST_HEIGHT_FILE) as f:
                previous_height = int(f.read())
        except:
            previous_height = 0

        count = 0
        succeeded = 0
        result = await async_get("{}/tx_since_to/{}/{}".format(CONFIG["api_url"], previous_height, MAIN_ADDRESS), is_json=True)
        new_height = result["end_height"]
        for transaction in result["txs"]:
            if transaction["recipient"] == MAIN_ADDRESS and transaction["data"]:
                count += 1
                if self.deposit_transaction(transaction["amount_after_fees"], transaction["data"], transaction["signature"], transaction["sender"]):
                    succeeded += 1
        print("{} deposit transactions found from {} to {}\nSuccessfully processed {}".format(count, previous_height, new_height, succeeded))

        with open(LAST_HEIGHT_FILE, "w") as f:
            f.write(str(new_height))


