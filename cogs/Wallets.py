"""
Nyzo wallets specific cog
"""

from discord.ext import commands
from modules.database import Db
from random import randint, shuffle
from math import floor, ceil
from nyzostrings.nyzostringprefilleddata import NyzoStringPrefilledData
from nyzostrings.nyzostringencoder import NyzoStringEncoder
from modules.helpers import async_get
from modules.config import CONFIG
from pynyzo.clienthelpers import NyzoClient
import time
import discord



DB_PATH = 'data/wallets.db'
MAIN_ADDRESS = "b34b3320b0291be2cd063f049bdef05ba57f313a60c173c3abce4b770e4e10b5"
MAIN_ID = "id__8bdbcQ2NahMzRgp_19Mv-5LCwR4Ypc5RNYMeiVtejy2TGnPC3AqE"
LAST_HEIGHT_FILE = "data/last_height.txt"
NYZO_CLIENT = NyzoClient()
with open("private/wallet_key.txt") as f:
    PRIVATE_KEY = f.read().strip()


class Wallet(commands.Cog):
    """Nyzeye wallet commands"""
    def __init__(self):
        self.db = Db(DB_PATH)
        self.db.execute("CREATE TABLE IF NOT EXISTS balances(user_id TEXT PRIMARY KEY, balance INT DEFAULT 0)")
        self.db.execute("CREATE TABLE IF NOT EXISTS transactions(sender TEXT, recipient TEXT, amount INT, "
                        "fee INT DEFAULT 0, type TEXT, offchain BOOL DEFAULT 1, id TEXT, timestamp INT)")

    @staticmethod
    async def safe_send_message(recipient, message):
        try:
            if not recipient.dm_channel:
                await recipient.create_dm()

            await recipient.dm_channel.send(message)
        except Exception as e:
            print(e)

    def remove_transaction(self, tx_id):
        for sender, recipient, amount, type, timestamp in \
                self.db.get("SELECT sender, recipient, amount, type, timestamp FROM transactions WHERE id=?", (tx_id,)):

            if type == "withdraw":
                self.update_balance(sender, amount)
                self.db.execute(
                    "DELETE FROM transactions WHERE sender=? AND recipient=? AND amount=? AND type=? AND timestamp=?",
                    (sender, recipient, amount, type, timestamp))
                print("removed transaction {}, {}, {}, {}, {}".format(sender, recipient, amount, type, timestamp))
            else:
                print("did not remove transaction {}, {}, {}, {}, {}".format(sender, recipient, amount, type, timestamp))

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

        elif tx_type == "withdraw":
            self.update_balance(sender, -amount)

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

    @commands.command()
    async def balance(self, ctx):
        """Shows your balance"""
        balance = self.get_balance(str(ctx.author.id))
        await ctx.send("You have ∩{:0.6f}".format(balance/10**6))

    @commands.command()
    async def tip(self, ctx, user: discord.User, amount: str='1'):
        """Usage: !tip @user amount' if not specified, amount=1, Sends some nyzo to another user"""
        if self.insert_transaction(str(ctx.author.id), str(user.id), floor(float(amount) * 10 ** 6), "tip"):
            await ctx.message.add_reaction('👍')
            await self.safe_send_message(user, "You've been tipped ∩{:0.6f} by {} ({})!"
                                         .format(float(amount), ctx.author.mention, ctx.author.display_name))
        else:
            await ctx.message.add_reaction('👎')

    @commands.command()
    async def rain(self, ctx, total_amount: str, how_many_users: str='10'):
        """Usage: !rain total_amount how_many_users' if not specified, how_many_users=10, Sends some nyzo to random users"""
        try:
            if "/" in total_amount:
                data = total_amount.split("/")
                total_amount = float(data[0])
                how_many_users = float(data[1])

            total_amount = float(total_amount)
            how_many_users = int(how_many_users)

            if total_amount <= 0 or how_many_users <= 0:
                raise ValueError

            if how_many_users > 100:
                how_many_users = 100

            if how_many_users < 1:
                how_many_users = 1

            if total_amount > 1000:
                total_amount = 1000

            if total_amount < 0.1 * how_many_users:
                how_many_users = int(total_amount / 0.1)

            if self.get_balance(str(ctx.author.id)) < total_amount * 10 ** 6:
                raise ValueError

            individual_amount = total_amount / how_many_users
            members = ctx.guild.members
            shuffle(members)

            final_message = "{} sent ∩{:0.6f} each to: ".format(ctx.author.mention, individual_amount)
            message = "Yeah! You got ∩{:0.6f} from the rain of {} ({}) from the Nyzo discord!" \
                .format(individual_amount, ctx.author, ctx.author.display_name)

            for member in members:
                if how_many_users <= 0:
                    break

                if str(member.status) != "offline" and not member.bot and member.name != ctx.author.name:
                    for role in member.roles:
                        if role.name == "Validated":
                            if self.insert_transaction(str(ctx.author.id), str(member.id),
                                                       floor(individual_amount * 10 ** 6), "rain"):
                                final_message += member.mention + " "
                                await self.safe_send_message(member, message)
                                how_many_users -= 1
                            break

            await ctx.send(final_message)
            await ctx.message.add_reaction('👍')
            return
        except Exception as e:
            print(e)
        await ctx.message.add_reaction('👎')

    @commands.command()
    async def deposit(self, ctx, block_id: int=-1):
        """Used to deposit Nyzo on you account"""
        if block_id != -1:
            count = 0
            successed = 0
            result = await async_get("{}/block/{}".format(CONFIG["api_url"], block_id), is_json=True)
            for block in result:
                for transaction in block["value"]["transactions"]:
                    if transaction["value"]["receiver_identifier"] == MAIN_ADDRESS and \
                            transaction["value"]["sender_data"]:
                        count += 1
                        if self.deposit_transaction(transaction["value"]["amount"] -
                                                    ceil(transaction["value"]["amount"] * 0.0025),
                                                    bytes.fromhex(transaction["value"]["sender_data"]).decode("utf-8"),
                                                    transaction["value"]["signature"],
                                                    transaction["value"]["sender_identifier"]):
                            successed += 1
            await ctx.send("{} deposit transactions found in block {}\nSuccessfuly processed {}".format(count, block_id,
                                                                                                        successed))
        else:
            nyzostring = NyzoStringEncoder.encode(NyzoStringPrefilledData.from_hex(MAIN_ADDRESS,
                                                                                   str(ctx.author.id).encode().hex()))
            await ctx.send("To deposit nyzo on your account, send a transaction to `{}` with `{}` in the data field\n"
                           "Or use this nyzostring: `{}`\nYou will get a message once the deposit is validated."
                           .format(MAIN_ID, ctx.author.id, nyzostring))

    @commands.command()
    async def withdraw(self, ctx, recipient: str, amount: float):
        """Used to withdraw Nyzo to another address"""
        if amount <= 0:
            await ctx.send("You can't send negative or null amounts")
            return

        if amount * (10 ** 6) - int(amount * (10 ** 6)) != 0:
            await ctx.send("You can't send more than 6 decimals")
            return

        try:
            nyzo_string, recipient = NYZO_CLIENT.normalize_address(recipient, as_hex=True)
        except ValueError:
            await ctx.send("Wrong address format. 64 bytes as hex or id_ nyzostring required")
            return

        if self.get_balance(ctx.author.id) < amount * (10 ** 6):
            await ctx.send("You don't have enough nyzo :(")
            return

        unique_id = str(randint(10 ** 20, 10 ** 30))
        self.insert_transaction(ctx.author.id, recipient, int(amount * (10 ** 6)), "withdraw", offchain=False, tx_id=unique_id)
        await ctx.send("Transaction will be forwarded to the cycle with data {}, you will get a new message when "
                       "the transaction is validated".format(unique_id))
        try:
            result = await NYZO_CLIENT.async_safe_send(recipient, amount=amount, data=unique_id, key_=PRIVATE_KEY, max_tries=5, verbose=True)
        except Exception as e:
            print(e)
            await ctx.send("Something went wrong while sending transaction {}, please contact @iyomisc".format(unique_id))
            return

        if result["sent"] is True:
            await ctx.send("Transaction {} successfully passed in block {}".format(unique_id, result["height"]))
            self.db.execute("UPDATE transactions SET fee=? WHERE id=?", (result["height"], unique_id))
        else:
            if not result["error"]:
                await ctx.send("transaction {} has not been accepted by the cycle:\nnotice: {}".format(
                    unique_id, result["notice"]))
            else:
                if result["notice"]:
                    await ctx.send("transaction {} has not been forwarded to the cycle\nerror: {}\nnotice: {}".format(
                        unique_id, result["error"], result["notice"]))
                else:
                    await ctx.send("transaction {} has not been forwarded to the cycle\nerror: {}".format(
                        unique_id, result["error"]))
            self.remove_transaction(unique_id)

    async def background_task(self, bot=None):
        try:
            with open(LAST_HEIGHT_FILE) as f:
                previous_height = int(f.read())

        except Exception as e:
            print(e)
            previous_height = 0

        count = 0
        succeeded = 0
        result = await async_get("{}/tx_since_to/{}/{}".format(CONFIG["api_url"], previous_height, MAIN_ADDRESS),
                                 is_json=True)
        new_height = result["end_height"]
        for transaction in result["txs"]:
            if transaction["recipient"] == MAIN_ADDRESS and transaction["data"]:
                count += 1
                if self.deposit_transaction(transaction["amount_after_fees"], transaction["data"],
                                            transaction["signature"], transaction["sender"]):
                    succeeded += 1
                    try:
                        await self.safe_send_message(await bot.get_user(int(transaction["data"])),
                                                     "∩{:0.6f} have been deposited on your account!"
                                                     .format(transaction["amount_after_fees"]/(10**6)))
                    except Exception as e:
                        print("Could not send message", e)
        print("{} deposit transactions found from {} to {}\nSuccessfully processed {}".format(count, previous_height,
                                                                                              new_height, succeeded))

        with open(LAST_HEIGHT_FILE, "w") as f:
            f.write(str(new_height))
