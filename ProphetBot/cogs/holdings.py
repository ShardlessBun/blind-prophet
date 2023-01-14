import logging

import discord
from discord import SlashCommandGroup, ApplicationContext, Member, Option, CategoryChannel
from discord.ext import commands
from ProphetBot.bot import  BpBot

log = logging.getLogger(__name__)


def setup(bot: commands.Bot):
    bot.add_cog(Holdings(bot))


class Holdings(commands.Cog):
    bot: BpBot
    holding_commands = SlashCommandGroup("holding_admin", "Commands related to guild specific settings")

    @holding_commands.command(
        name="create",
        description="Open a holding"
    )
    async def holding_open(self, ctx: ApplicationContext,
                           owner: Option(Member, description="Holding owner", required=True),
                           name: Option(str, description="Name of the holding", required=True),
                           category_channel: Option(CategoryChannel, description="Holding Channel Category",
                                                    required=True)):

        await ctx.defer()

        chan_perms = dict()

        chan_perms[owner] = discord.PermissionOverwrite(manage_channels=True,
                                                        manage_messages=True)

        holding_chanel = await ctx.guild.create_text_channel(
            name=name,
            category=category_channel,
            overwrites=chan_perms,
            reason=f"New holding {name}"
        )

        await holding_chanel.send(f'{owner.mention} welcome to your new holding.')
        await ctx.delete()