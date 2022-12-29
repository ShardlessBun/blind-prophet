import asyncio
import logging

import discord.utils
from discord import SlashCommandGroup, ApplicationContext, TextChannel, Option, Message
from discord.ext import commands, tasks

from ProphetBot.bot import BpBot
from ProphetBot.constants import DASHBOARD_REFRESH_INTERVAL
from ProphetBot.helpers import get_dashboard_from_category_channel_id, get_last_message
from ProphetBot.models.db_objects import RefCategoryDashboard, DashboardType, Shop, Adventure
from ProphetBot.models.embeds import ErrorEmbed, RpDashboardEmbed, ShopDashboardEmbed, AdventureDashboardEmbed
from ProphetBot.models.schemas import RefCategoryDashboardSchema, ShopSchema, AdventureSchema
from ProphetBot.queries import insert_new_dashboard, get_dashboards, delete_dashboard, update_dashboard, get_shops, \
    get_adventure_by_guild
from timeit import default_timer as timer

log = logging.getLogger(__name__)


def setup(bot: commands.Bot):
    bot.add_cog(Dashboards(bot))


class Dashboards(commands.Cog):
    bot: BpBot
    dashboard_commands = SlashCommandGroup("dashboard", "Dashboard commands")

    def __init__(self, bot):
        self.bot = bot
        print(f'Cog \'Dashboards\' loaded')

    @commands.Cog.listener()
    async def on_ready(self):
        await asyncio.sleep(6.0)
        log.info(f"Reloading dashboards every {DASHBOARD_REFRESH_INTERVAL} minutes.")
        await self.update_dashboards.start()

    @dashboard_commands.command(
        name="rp_create",
        description="Creates a dashboard which shows the status of RP channels in this category"
    )
    async def dashboard_rp_create(self, ctx: ApplicationContext,
                                  excluded_channel_1: Option(TextChannel, "The first channel to exclude",
                                                             required=False, default=None),
                                  excluded_channel_2: Option(TextChannel, "The second channel to exclude",
                                                             required=False, default=None),
                                  excluded_channel_3: Option(TextChannel, "The third channel to exclude",
                                                             required=False, default=None),
                                  excluded_channel_4: Option(TextChannel, "The fourth channel to exclude",
                                                             required=False, default=None),
                                  excluded_channel_5: Option(TextChannel, "The fifth channel to exclude",
                                                             required=False, default=None)):
        """
        Creates a RP Dashboard in the channel to show channel availability

        :param ctx: Context
        :param excluded_channel_1: TextChannel to exclude from the dashboard
        :param excluded_channel_2: TextChannel to exclude from the dashboard
        :param excluded_channel_3: TextChannel to exclude from the dashboard
        :param excluded_channel_4: TextChannel to exclude from the dashboard
        :param excluded_channel_5: TextChannel to exclude from the dashboard
        """

        await ctx.defer()

        dashboard: RefCategoryDashboard = await get_dashboard_from_category_channel_id(ctx)

        if dashboard is not None:
            return await ctx.respond(embed=ErrorEmbed(description="There is already a dashboard for this category. "
                                                                  "Delete that before creating another"),
                                     ephemeral=True)

        excluded_channels = list(set(filter(
            lambda c: c is not None,
            [excluded_channel_1, excluded_channel_2, excluded_channel_3, excluded_channel_4, excluded_channel_5]
        )))

        # Create post with dummy text in it
        interaction = await ctx.respond("Fetching dashboard data. This may take a moment")
        msg: Message = await ctx.channel.fetch_message(interaction.id)
        await msg.pin(reason=f"RP Dashboard for {ctx.channel.category.name} created by {ctx.author.name}")

        dType = ctx.bot.compendium.get_object("c_dashboard_type", "RP")

        dashboard = RefCategoryDashboard(category_channel_id=ctx.channel.category.id,
                                         dashboard_post_channel_id=ctx.channel_id,
                                         dashboard_post_id=msg.id,
                                         excluded_channel_ids=[c.id for c in excluded_channels],
                                         dashboard_type=dType.id)

        async with ctx.bot.db.acquire() as conn:
            await conn.execute(insert_new_dashboard(dashboard))

        await self.update_dashboard(dashboard)

    @dashboard_commands.command(
        name="shop_create",
        description="Creates a dashboard showing available shops"
    )
    async def dashboard_shop_create(self, ctx: ApplicationContext):
        await ctx.defer()

        dashboard: RefCategoryDashboard = await get_dashboard_from_category_channel_id(ctx)

        if dashboard is not None:
            return await ctx.respond(embed=ErrorEmbed(description="There is already a dashboard for this category. "
                                                                  "Delete that before creating another"),
                                     ephemeral=True)

        # Create post with dummy text in it
        interaction = await ctx.respond("Fetching dashboard data. This may take a moment")
        msg: Message = await ctx.channel.fetch_message(interaction.id)
        await msg.pin(reason=f"Shop dashboard created by {ctx.author.name}")

        dType = ctx.bot.compendium.get_object("c_dashboard_type", "SHOP")

        dashboard = RefCategoryDashboard(category_channel_id=ctx.channel.category.id,
                                         dashboard_post_channel_id=ctx.channel_id,
                                         dashboard_post_id=msg.id,
                                         excluded_channel_ids=[],
                                         dashboard_type=dType.id)

        async with ctx.bot.db.acquire() as conn:
            await conn.execute(insert_new_dashboard(dashboard))

        await self.update_dashboard(dashboard)

    @dashboard_commands.command(
        name="adventure_create",
        description="Creates a dashboard showing active adventures"
    )
    async def dashboard_adventure_create(self, ctx: ApplicationContext):
        await ctx.defer()

        dashboard: RefCategoryDashboard = await get_dashboard_from_category_channel_id(ctx)

        if dashboard is not None:
            return await ctx.respond(embed=ErrorEmbed(description="There is already a dashboard for this category. "
                                                                  "Delete that before creating another"),
                                     ephemeral=True)

        # Create post with dummy text in it
        interaction = await ctx.respond("Fetching dashboard data. This may take a moment")
        msg: Message = await ctx.channel.fetch_message(interaction.id)
        await msg.pin(reason=f"Shop dashboard created by {ctx.author.name}")

        dType = ctx.bot.compendium.get_object("c_dashboard_type", "ADVENTURE")

        dashboard = RefCategoryDashboard(category_channel_id=ctx.channel.category.id,
                                         dashboard_post_channel_id=ctx.channel_id,
                                         dashboard_post_id=msg.id,
                                         excluded_channel_ids=[],
                                         dashboard_type=dType.id)

        async with ctx.bot.db.acquire() as conn:
            await conn.execute(insert_new_dashboard(dashboard))

        await self.update_dashboard(dashboard)

    @dashboard_commands.command(
        name="rp_exclude",
        description="Add a channel to the exclusions list"
    )
    async def dashboard_rp_exclude(self, ctx: ApplicationContext,
                                   excluded_channel: Option(TextChannel, description="Channel to exclude",
                                                            required=True)):
        """
        Add a channel to the exclusions list

        :param ctx: Context
        :param excluded_channel: TextChannel to exclude from the dashboard
        """
        await ctx.defer()

        dashboard: RefCategoryDashboard = await get_dashboard_from_category_channel_id(ctx)

        if dashboard is None:
            return await ctx.respond(embed=ErrorEmbed(description=f"No dashboard found for this category"),
                                     ephemeral=True)

        dashboard.excluded_channel_ids.append(excluded_channel.id)

        async with ctx.bot.db.acquire() as conn:
            await conn.execute(update_dashboard(dashboard))

        await self.update_dashboard(dashboard)
        await ctx.respond(f"Exclusion added", ephemeral=True)

    async def update_dashboard(self, dashboard: RefCategoryDashboard):
        """
        Primary method to update a dashboard

        :param dashboard: RefCategoryDashboard to update
        """

        original_message = await dashboard.get_pinned_post(self.bot)

        if original_message is None or not original_message.pinned:
            async with self.bot.db.acquire() as conn:
                return await conn.execute(delete_dashboard(dashboard))

        dType: DashboardType = self.bot.compendium.get_object("c_dashboard_type", dashboard.dashboard_type)
        channels = dashboard.channels_to_check(self.bot)

        if dType is not None and dType.value.upper() == "RP":
            channels_dict = {
                "Magewright": [],
                "Available": [],
                "In Use": []
            }

            g: discord.Guild = dashboard.get_category_channel(self.bot).guild
            magewright_role = discord.utils.get(g.roles, name="Magewright")

            for c in channels:
                last_message = await get_last_message(c)

                if last_message is None or last_message.content in ["```\n​\n```", "```\n \n```"]:
                    channels_dict["Available"].append(c.mention)
                elif magewright_role is not None and magewright_role.mention in last_message.content:
                    channels_dict["Magewright"].append(c.mention)
                else:
                    channels_dict["In Use"].append(c.mention)

            category = dashboard.get_category_channel(self.bot)
            return await original_message.edit(content='', embed=RpDashboardEmbed(channels_dict, category.name))

        elif dType is not None and dType.value.upper() == "SHOP":
            shop_dict = {}
            g: discord.Guild = dashboard.get_category_channel(self.bot).guild

            for shop_type in self.bot.compendium.c_shop_type[0].values():
                shop_dict[shop_type.value] = []

            async with self.bot.db.acquire() as conn:
                async for row in conn.execute(get_shops(g.id)):
                    if row is not None:
                        shop: Shop = ShopSchema(self.bot.compendium).load(row)
                        shop_dict[shop.type.value].append(shop)

            return await original_message.edit(content='', embed=ShopDashboardEmbed(g, shop_dict))

        elif dType is not None and dType.value.upper() == "ADVENTURE":
            adventures = {}
            g: discord.Guild = dashboard.get_category_channel(self.bot).guild

            adventures[1] = []
            adventures[2] = []
            adventures[3] = []
            adventures[4] = []
            async with self.bot.db.acquire() as conn:
                async for row in conn.execute(get_adventure_by_guild(g.id)):
                    adventure: Adventure = AdventureSchema(self.bot.compendium).load(row)
                    a_dict = {
                        "adventure": adventure,
                        "dms": [],
                        "players": []}
                    adventures[adventure.tier.id].append(a_dict)

            for tier in adventures.keys():
                for a in adventures[tier]:
                    adventure = a["adventure"]
                    members = discord.utils.get(g.roles, id=adventure.role_id).members

                    if len(members) > 0:
                        for p in members:
                            if p.id in adventure.dms:
                                a["dms"].append(p)
                            else:
                                a["players"].append(p)

            return await original_message.edit(content='', embed=AdventureDashboardEmbed(g, adventures))

    # --------------------------- #
    # Tasks
    # --------------------------- #
    @tasks.loop(minutes=DASHBOARD_REFRESH_INTERVAL)
    async def update_dashboards(self):
        start = timer()
        async with self.bot.db.acquire() as conn:
            async for row in conn.execute(get_dashboards()):
                dashboard: RefCategoryDashboard = RefCategoryDashboardSchema().load(row)
                await self.update_dashboard(dashboard)
        end = timer()
        log.info(f"DASHBOARD: Channel status dashboards updated in [ {end - start:.2f} ]s")