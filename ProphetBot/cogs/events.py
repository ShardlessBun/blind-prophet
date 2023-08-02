import logging

import discord
import re
from discord import Embed
from discord.ext import commands

from ProphetBot.bot import BpBot
from ProphetBot.helpers import get_character, get_player_adventures, get_shop, get_or_create_guild
from ProphetBot.models.db_objects import PlayerCharacter, Shop

log = logging.getLogger(__name__)


def setup(bot: commands.Bot):
    bot.add_cog(Events(bot))

class Events(commands.Cog):
    bot: BpBot

    def __init__(self, bot):
        self.bot = bot
        log.info(f'Cog \'Events\' loaded')
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if exit_channel := discord.utils.get(member.guild.channels, name="exit"):
            character: PlayerCharacter = await get_character(self.bot, member.id, member.guild.id)
            adventures = await get_player_adventures(self.bot, member)

            embed = Embed(title=f'{str(member)}')

            if member.nick is not None:
                embed.title += f" ( `{member.nick}` )"
            else:
                embed.title += f"( No nickname )"

            embed.title += f" has left the server.\n\n"

            if character is None:
                value = "\n".join(f'\u200b - {r.mention}' for r in member.roles if 'everyone' not in r.name)

                embed.add_field(name="Roles", value=value, inline=False)

            else:
                embed.description = f"**Character:** {character.name}\n" \
                                    f"**Level:** {character.get_level()}\n" \
                                    f"**Faction:** {character.faction.value}"

            if shopkeeper_role := discord.utils.get(member.guild.roles, name="Shopkeeper"):
                if shopkeeper_role in member.roles:
                    shop: Shop = await get_shop(self.bot, member.id, member.guild.id)
                    if shop is None:
                        value = "Has role, but no shop found"
                    else:
                        value = f"{shop.name}"
                else:
                    value = "*None*"
            embed.add_field(name=f"Shopkeeper", value=value, inline=False)

            if len(adventures['player']) > 0 or len(adventures['dm']) > 0:
                value = "".join([f'\u200b - {a.name}*\n' for a in adventures['dm']])
                value += "\n".join([f'\u200b - {a.name}' for a in adventures['player']])
                count = len(adventures['player']) + len(adventures['dm'])
            else:
                value = "*None*"
                count = 0
            embed.add_field(name=f"Adventures ({count})", value=value, inline=False)

            arenas = [r for r in member.roles if 'arena' in r.name.lower()]

            if len(arenas) > 0:
                value = "\n".join(f'\u200b - {r.mention}' for r in arenas)
                count = len(arenas)
            else:
                value = "*None*"
                count = 0
            embed.add_field(name=f"Arenas ({count})", value=value, inline=False)

            try:
                await exit_channel.send(embed=embed)
            except Exception as error:
                if isinstance(error, discord.errors.HTTPException):
                    log.error(f"ON_MEMBER_REMOVE: Error sending message to exit channel in "
                              f"{member.guild.name} [ {member.guild.id} ] for {member.name} [ {member.id} ]")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        g = await get_or_create_guild(self.bot.db, member.guild.id)

        if (entrance_channel := discord.utils.get(member.guild.channels, name="entrance")) and g.greeting:
            message = g.greeting

            pattern = r'{#([^}]*)}'
            channels = re.findall(pattern, message)
            for c in channels:
                ch = discord.utils.get(member.guild.channels, name=c)
                message = message.replace("{#"+c+"}", f"{ch.mention}") if ch.mention else message

            message = message.replace("{user}", f"{member.mention}")

            await entrance_channel.send(message)

            if fledgling_role := discord.utils.get(member.guild.roles, name="Fledgling"):
                if fledgling_role not in member.roles:
                    await member.add_roles(fledgling_role, reason="Joined the server")

