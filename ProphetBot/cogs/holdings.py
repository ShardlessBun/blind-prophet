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
    holding_admin = SlashCommandGroup("holding_admin", "Commands related to holding administration")
    holding_commands = SlashCommandGroup("holding", "Commands related to your holding")


    @holding_admin.command(
        name="create",
        description="Open a holding"
    )
    async def holding_open(self, ctx: ApplicationContext,
                           owner: Option(Member, description="Holding owner", required=True),
                           name: Option(str, description="Name of the holding", required=True),
                           category_channel: Option(CategoryChannel, description="Holding Channel Category",
                                                    required=True),
                           owner_2: Option(Member, description="2nd Owner", required=False),
                           owner_3: Option(Member, description="3rd Owner", required=False)):

        await ctx.defer()

        chan_perms = dict()

        chan_perms[owner] = discord.PermissionOverwrite(manage_channels=True,
                                                        manage_messages=True)
        if owner_2 is not None:
            chan_perms[owner_2] = chan_perms[owner]

        if owner_3 is not None:
            chan_perms[owner_3] = chan_perms[owner]

        holding_chanel = await ctx.guild.create_text_channel(
            name=name,
            category=category_channel,
            overwrites=chan_perms,
            reason=f"New holding {name}"
        )

        await holding_chanel.send(f'{owner.mention} welcome to your new holding.')
        await ctx.delete()

