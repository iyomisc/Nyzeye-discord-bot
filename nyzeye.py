"""
Nyzeye Discord Bot for Nyzo Cryptocurrency
"""

import asyncio
from discord.ext import commands
import discord
from cogs.NyzoWatcher import NyzoWatcher
from cogs.Nyzo import Nyzo
from cogs.extra import Extra
from cogs.Wallets import Wallet
from modules.config import CONFIG, SHORTCUTS

__version__ = '1.0'

BOT_PREFIX = 'Nyzeye '

bot = commands.Bot(command_prefix=BOT_PREFIX)

CHECKING_BANS = False


@bot.event
async def on_ready():
    """
    This function is not guaranteed to be the first event called.
    Likewise, this function is not guaranteed to only be called once.
    This library implements reconnection logic and thus will end up calling this event whenever a RESUME request fails.
    """
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

    if "broadcast_restart" in CONFIG and CONFIG["broadcast_restart"]:
        await bot.get_channel(CONFIG['bot_channel'][0])\
            .send("I just restarted, if one of your commands didn't get an answer, just resend it.")

    bot.loop.create_task(monitor_impersonators())


@bot.event
async def on_message(message):
    """Called when a message is created and sent to a server."""
    for search, replace in SHORTCUTS.items():
        if message.content.startswith(search):
            message.content = message.content.replace(search, replace, 1)

    if not message.content.startswith(BOT_PREFIX):
        return

    if bot.user.id != message.author.id:  # check not a bot message
        print("Got {} from {}".format(message.content, message.author.display_name))
    else:
        return

    if type(message.channel) == discord.TextChannel and message.channel.id not in CONFIG['bot_channel'] \
            and not message.content.startswith('Nyzeye tip'):
        print('Unauth channel')
    else:
        print("answering")
        await message.add_reaction('⏳')  # Hourglass
        try:
            # only here, will process commands
            await bot.process_commands(message)
            print("Success")
        except Exception as e:
            print(e)

        finally:

            await message.remove_reaction('⏳', bot.user)  # Hourglass


@bot.command()
async def about(ctx):
    """Nyzeye bot general info"""
    await ctx.send(
        "Nyzeye bot Version {}\nI'm your Nyzo butler. Type `Nyzeye help` for a full commands list.".format(__version__))


async def background_task(cog_list):
    await bot.wait_until_ready()
    while not bot.is_closed:
        for cog in cog_list:
            try:
                await cog.background_task(bot=bot)
            except Exception as e:
                print(e)
        await asyncio.sleep(60)


async def monitor_impersonators():
    await bot.wait_until_ready()
    # Make sure config is lowercase - this becomes a set, therefore unique names.
    while not bot.is_closed:
        await ban_scammers()
        await asyncio.sleep(120)


def is_scammer(member):
    for badword in CONFIG["scammer_keywords"]:
        if badword in member.display_name.lower():
            return True
        if badword in member.name.lower():
            return True
    for badhash in CONFIG["scammer_avatars"]:
        if badhash == member.avatar:
            return True
    return False


async def ban_scammers():
    global CHECKING_BANS
    if CHECKING_BANS:
        # Avoid re-entrance.
        return
    try:
        CHECKING_BANS = True
        print("Checking spammers...", CONFIG["scammer_keywords"])
        # start = time()
        members = list(bot.get_all_members())
        for member in members:
            if is_scammer(member):
                print(member.display_name, member.name)
        scammers = [member for member in members if is_scammer(member)]
        print("{} spammers". format(len(scammers)))
        for scammer in scammers:
            await bot.get_channel(CONFIG['impersonator_info_channel']).send("Spammer - " + scammer.mention + " banned")
            await scammer.ban()

            print('Spammer - {} banned'.format(scammer.name))

    except Exception as e:
        print("Exception ban_scammers", str(e))
    finally:
        CHECKING_BANS = False


if __name__ == '__main__':
    nyzo_watcher = NyzoWatcher()
    wallet = Wallet()
    bot.add_cog(nyzo_watcher)
    bot.add_cog(Nyzo())
    bot.add_cog(Extra())
    bot.add_cog(wallet)
    bot.loop.create_task(background_task([nyzo_watcher, wallet]))

    bot.run(CONFIG['token'])
