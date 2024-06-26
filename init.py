import asyncio
import logging
import sys
import traceback
from os import listdir
import discord
from discord import Intents, ApplicationContext, Embed
from discord.ext import commands
from ProphetBot.bot import BpBot
from ProphetBot.constants import BOT_TOKEN, DEFAULT_PREFIX, DEBUG_GUILDS
from ProphetBot.helpers import get_character, get_player_adventures, get_shop, is_owner, is_admin
from ProphetBot.models.db_objects import PlayerCharacter, Shop

intents = Intents.default()
intents.members = True
intents.message_content = True

# TODO: Error embeds instead of straight ctx.responds for consistency


class MyHelpCommand(commands.MinimalHelpCommand):
    async def send_pages(self):
        destination = self.get_destination()
        e = discord.Embed(color=discord.Color.blurple(), description='')
        for page in self.paginator.pages:
            e.description += page
        await destination.send(embed=e)


log_formatter = logging.Formatter("%(asctime)s %(name)s: %(message)s")
handler = logging.StreamHandler(sys.stdout)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)
log = logging.getLogger("bot")

# Because Windows is terrible
if sys.version_info >= (3, 8) and sys.platform.lower().startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

bot = BpBot(command_prefix=DEFAULT_PREFIX,
            description='ProphetBot - Created and maintained by Nick!#8675 and Alesha#0362',
            case_insensitive=True,
            help_command=MyHelpCommand(),
            intents=intents,
            debug_guilds=DEBUG_GUILDS
            )

for filename in listdir('ProphetBot/cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'ProphetBot.cogs.{filename[:-3]}')


@bot.command()
async def ping(ctx):
    print("Pong")
    await ctx.send(f'Pong! Latency is {round(bot.latency * 1000)}ms.')\

@bot.command(name="asay")
@commands.check(is_admin)
async def admin_say(ctx: ApplicationContext, channel_id, msg):
    channel = discord.utils.get(ctx.guild.channels, id=int(channel_id))
    if channel is not None:
        try:
            await channel.send(msg)
        except:
            log.warning('Unable to send message')
    return await ctx.respond("No channel found")


@bot.event
async def on_application_command_error(ctx: ApplicationContext, error):
    """
    Handle various exceptions and issues

    :param ctx: Context
    :param error: The error that was raised
    """

    # Prevent any commands with local error handling from being handled here
    if hasattr(ctx.command, 'on_error'):
        return

    if isinstance(error, discord.errors.CheckFailure):
        return await ctx.respond(f'You do not have required permissions for `{ctx.command}`')
    if isinstance(error.original, AttributeError):
        log.warning("Attribue Errror: '{}'".format(error))
        return await ctx.respond(f"Try again in a minute, and if doesn't work let us know")
    else:
        log.warning("Error in command: '{}'".format(ctx.command))
        for line in traceback.format_exception(type(error), error, error.__traceback__):
            log.warning(line)
        try:
            return await ctx.respond(f'Something went wrong. Let us know if it keeps up!')
        except:
            log.warning('Unable to respond')


@bot.event
async def on_application_command(ctx):
    try:
        if ctx.selected_options is not None:
            params = "".join([f" [{p['name']}: {p['value']}]" for p in ctx.selected_options])
        else:
            params = ""
        log.info(
            "cmd: chan {0.channel} [{0.channel.id}], serv: {0.guild} [{0.guild.id}],"
            " auth: {0.user} [{0.user.id}]: {0.command} ".format(ctx) + params
        )
    except AttributeError:
        log.info("Command in PM with {0.message.author} ({0.message.author.id}): {0.message.content}.".format(ctx))

# @bot.event
# async def on_member_remove(member):
#     if exit_channel := discord.utils.get(member.guild.channels, name="exit"):
#         character: PlayerCharacter = await get_character(bot, member.id, member.guild.id)
#         adventures = await get_player_adventures(bot, member)
#
#         embed = Embed(title=f'{str(member)}')
#
#         if member.nick is not None:
#             embed.title += f" ( `{member.nick}` )"
#         else:
#             embed.title += f"( No nickname )"
#
#         embed.title += f" has left the server.\n\n"
#
#         if character is None:
#             roles = []
#             for r in member.roles:
#                 if 'everyone' in r.name:
#                     pass
#                 else:
#                     roles.append(r)
#
#             value="\n".join(f'\u200b - {r.mention}' for r in roles)
#
#             embed.add_field(name="Roles", value=value, inline=False)
#
#         else:
#             embed.description=f"**Character:** {character.name}\n" \
#                               f"**Level:** {character.get_level()}\n" \
#                               f"**Faction:** {character.faction.value}"
#
#         if shopkeeper_role := discord.utils.get(member.guild.roles, name="Shopkeeper"):
#             if shopkeeper_role in member.roles:
#                 shop: Shop = await get_shop(bot, member.id, member.guild.id)
#                 if shop is None:
#                     value = "Has role, but no shop found"
#                 else:
#                     value = f"{shop.name}"
#             else:
#                 value = "*None*"
#         embed.add_field(name=f"Shopkeeper", value=value, inline=False)
#
#         if len(adventures['player']) > 0 or len(adventures['dm']) > 0:
#             value = "".join([f'\u200b - {a.name}*\n' for a in adventures['dm']])
#             value +="\n".join([f'\u200b - {a.name}' for a in adventures['player']])
#             count = len(adventures['player']) + len(adventures['dm'])
#         else:
#             value = "*None*"
#             count = 0
#         embed.add_field(name=f"Adventures ({count})", value=value, inline=False)
#
#         arenas = []
#         for r in member.roles:
#             if 'arena' in r.name.lower():
#                 arenas.append(r)
#
#         if len(arenas) > 0:
#             value = "\n".join(f'\u200b - {r.mention}' for r in arenas)
#             count = len(arenas)
#         else:
#             value = "*None*"
#             count = 0
#         embed.add_field(name=f"Arenas ({count})", value=value, inline=False)
#
#         try:
#             await exit_channel.send(embed=embed)
#         except Exception as error:
#             if isinstance(error, discord.errors.HTTPException):
#                 log.error(f"ON_MEMBER_REMOVE: Error sending message to exit channel in "
#                           f"{member.guild.name} [ {g.id} ] for {member.name} [ {member.id} ]")


bot.run(BOT_TOKEN)
