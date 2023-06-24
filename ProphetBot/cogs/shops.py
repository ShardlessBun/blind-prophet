import logging
import random

import d20
import discord
from discord import SlashCommandGroup, ApplicationContext, Member, Option, TextChannel, CategoryChannel
from discord.ext import commands
from texttable import Texttable

from ProphetBot.bot import BpBot
from ProphetBot.helpers import get_or_create_guild, sort_stock, \
    shop_create_type_autocomplete, get_shop, upgrade_autocomplete, roll_stock, paginate, rarity_autocomplete, confirm, \
    item_autocomplete, get_all_shops
from ProphetBot.models.db_objects import PlayerGuild, Shop
from ProphetBot.models.embeds import ErrorEmbed, NewShopEmbed, ShopEmbed, ShopSeekEmbed
from ProphetBot.queries import insert_new_shop, update_shop

log = logging.getLogger(__name__)


def setup(bot: commands.Bot):
    bot.add_cog(Shops(bot))


class Shops(commands.Cog):
    bot: BpBot
    shop_commands = SlashCommandGroup("shop", "Shop commands")
    shop_admin = SlashCommandGroup("shop_admin", "Shop administration commands")

    def __init__(self, bot):
        self.bot = bot
        log.info(f'Cog \'Shops\' loaded')

    @shop_commands.command(
        name="inventory",
        description="Roll inventory"
    )
    async def item_inventory(self, ctx: ApplicationContext):
        await ctx.defer()

        shop: Shop = await get_shop(ctx.bot, ctx.author.id, ctx.guild_id)

        if shop is None:
            return await ctx.respond(embed=ErrorEmbed(description=f"Shop not found"), ephemeral=True)

        shop.inventory_rolled = True
        async with ctx.bot.db.acquire() as conn:
            await conn.execute(update_shop(shop))


        g: PlayerGuild = await get_or_create_guild(ctx.bot.db, ctx.guild_id)

        if shop.type.id == 1:  # Consumable
            potion_table = Texttable()
            potion_table.set_cols_align(['l', 'c', 'l'])
            potion_table.set_cols_valign(['m', 'm', 'm'])
            potion_table.set_cols_width([20, 5, 7])

            potion_table.header(['Item', 'Qty', 'Cost'])
            potion_qty = 3 + shop.shelf
            potion_items = list(ctx.bot.compendium.consumable[0].values())

            potion_stock = {'Potion of Healing': random.randint(1, 4)}
            potion_stock.update(roll_stock(ctx.bot.compendium, g, potion_items, potion_qty, 4,shop.max_cost, 1))

            potion_data = []
            for p in potion_stock:
                if p == 'Potion of Healing':
                    potion_data.append([p, str(potion_stock[p]), '50'])
                else:
                    potion = ctx.bot.compendium.get_object("consumable", p)
                    potion_data.append([potion.name, str(potion_stock[p]), str(potion.cost)])

            potion_table.add_rows(sort_stock(potion_data), header=False)

            scroll_table = Texttable()
            scroll_table.set_cols_align(['l', 'c', 'l'])
            scroll_table.set_cols_valign(['m', 'm', 'm'])
            scroll_table.set_cols_width([20, 5, 7])
            scroll_table.header(['Item (lvl)', 'Qty', 'Cost'])
            scroll_qty = 6 + (3 * shop.shelf)
            scroll_items = list(ctx.bot.compendium.scroll[0].values())

            scroll_stock = roll_stock(ctx.bot.compendium, g, scroll_items, scroll_qty, 2, shop.max_cost)

            scroll_data = []
            for s in scroll_stock:
                scroll = ctx.bot.compendium.get_object("scroll", s)
                scroll_data.append([scroll.display_name(), str(scroll_stock[s]), str(scroll.cost)])

            scroll_table.add_rows(sort_stock(scroll_data), header=False)

            await ctx.delete()
            await ctx.send(f'Rolling stock for {ctx.guild.get_channel(shop.channel_id).mention}')
            await paginate(ctx, potion_table.draw())
            await paginate(ctx, scroll_table.draw())
            return

        elif shop.type.id == 2:  # Blacksmith
            smith_table = Texttable()
            smith_table.set_cols_align(['l', 'c', 'l'])
            smith_table.set_cols_valign(['m', 'm', 'm'])
            smith_table.set_cols_width([20, 5, 7])
            smith_table.header(['Item', 'Qty', 'Cost'])

            weapon_qty = 4 + shop.shelf
            weapon_type = ctx.bot.compendium.get_object("c_blacksmith_type", "Weapon")
            weapon_items = list(
                filter(lambda i: i.sub_type.id == weapon_type.id, list(ctx.bot.compendium.blacksmith[0].values())))

            weapon_stock = roll_stock(ctx.bot.compendium, g, weapon_items, weapon_qty, 1, shop.max_cost)

            weapon_data = []
            for i in weapon_stock:
                weapon = ctx.bot.compendium.get_object("blacksmith", i)
                weapon_data.append([weapon.name, str(weapon_stock[i]), weapon.display_cost()])

            smith_table.add_rows(sort_stock(weapon_data), header=False)

            armor_qty = 4 + shop.shelf
            armor_type = ctx.bot.compendium.get_object("c_blacksmith_type", "Armor")
            armor_items = list(filter(lambda i: i.sub_type.id == armor_type.id,
                                      list(ctx.bot.compendium.blacksmith[0].values())))

            armor_stock = roll_stock(ctx.bot.compendium, g, armor_items, armor_qty, 1, shop.max_cost)

            armor_data = []
            for i in armor_stock:
                armor = ctx.bot.compendium.get_object("blacksmith", i)
                armor_data.append([armor.name, str(armor_stock[i]), armor.display_cost()])

            smith_table.add_rows(sort_stock(armor_data), header=False)

            await ctx.delete()
            await ctx.send(f'Rolling stock for {ctx.guild.get_channel(shop.channel_id).mention}')
            await paginate(ctx, smith_table.draw())
            return

        elif shop.type.id == 3:  # Magic Shops
            magic_table = Texttable()
            magic_table.set_cols_align(['l', 'c', 'l'])
            magic_table.set_cols_valign(['m', 'm', 'm'])
            magic_table.set_cols_width([20, 5, 7])
            magic_table.header(['Item', 'Qty', 'Cost'])

            magic_qty = 9 + (3 * shop.shelf)
            magic_items = list(ctx.bot.compendium.wondrous[0].values())

            magic_stock = roll_stock(ctx.bot.compendium, g, magic_items, magic_qty, 1, shop.max_cost)

            magic_data = []
            for m in magic_stock:
                item = ctx.bot.compendium.get_object("wondrous", m)

                magic_data.append([item.name, str(magic_stock[m]), str(item.cost)])

            magic_table.add_rows(sort_stock(magic_data), header=False)

            await ctx.delete()
            await ctx.send(f'Rolling stock for {ctx.guild.get_channel(shop.channel_id).mention}')
            await paginate(ctx, magic_table.draw())
            return

        else:
            return await ctx.respond(embed=ErrorEmbed(description=f"Error rolling inventory"), ephemeral=True)

    @shop_commands.command(
        name="reroll_item",
        description="Re-Rolls an item"
    )
    async def item_inventory(self, ctx: ApplicationContext,
                             item: Option(str, description="Item rerolling",
                                          autocomplete=item_autocomplete, required=True)):
        await ctx.defer()

        shop: Shop = await get_shop(ctx.bot, ctx.author.id, ctx.guild_id)

        if shop is None:
            return await ctx.respond(embed=ErrorEmbed(description=f"Shop not found"), ephemeral=True)

        g: PlayerGuild = await get_or_create_guild(ctx.bot.db, ctx.guild_id)


        if shop.type.id == 1 and (item_record := ctx.bot.compendium.get_object("consumable", item)):  # Consumable
            potion_table = Texttable()
            potion_table.set_cols_align(['l', 'c', 'l'])
            potion_table.set_cols_valign(['m', 'm', 'm'])
            potion_table.set_cols_width([20, 5, 7])

            potion_table.header(['Item', 'Qty', 'Cost'])
            potion_qty = 1
            potion_items = list(ctx.bot.compendium.consumable[0].values())
            potion_stock = roll_stock(ctx.bot.compendium, g, potion_items, potion_qty, 4, shop.max_cost)

            potion_data = []
            for p in potion_stock:
                if p == 'Potion of Healing':
                    potion_data.append([p, str(potion_stock[p]), '50'])
                else:
                    potion = ctx.bot.compendium.get_object("consumable", p)
                    potion_data.append([potion.name, str(potion_stock[p]), str(potion.cost)])

            potion_table.add_rows(sort_stock(potion_data), header=False)
            await ctx.delete()
            await ctx.send(
                f'Re-rolling stock for {ctx.guild.get_channel(shop.channel_id).mention} replacing {item_record.name}')
            await paginate(ctx, potion_table.draw())
            return
        elif shop.type.id == 1 and (item_record := ctx.bot.compendium.get_object("scroll", item)):
            scroll_table = Texttable()
            scroll_table.set_cols_align(['l', 'c', 'l'])
            scroll_table.set_cols_valign(['m', 'm', 'm'])
            scroll_table.set_cols_width([20, 5, 7])
            scroll_table.header(['Item (lvl)', 'Qty', 'Cost'])
            scroll_qty = 1
            scroll_items = list(ctx.bot.compendium.scroll[0].values())

            scroll_stock = roll_stock(ctx.bot.compendium, g, scroll_items, scroll_qty, 2, shop.max_cost)

            scroll_data = []
            for s in scroll_stock:
                scroll = ctx.bot.compendium.get_object("scroll", s)
                scroll_data.append([scroll.display_name(), str(scroll_stock[s]), str(scroll.cost)])

            scroll_table.add_rows(sort_stock(scroll_data), header=False)

            await ctx.delete()
            await ctx.send(f'Re-rolling stock for {ctx.guild.get_channel(shop.channel_id).mention} replacing {item_record.name}')
            await paginate(ctx, scroll_table.draw())
            return

        elif shop.type.id == 2 and (item_record := ctx.bot.compendium.get_object("blacksmith", item)):  # Blacksmith
            smith_table = Texttable()
            smith_table.set_cols_align(['l', 'c', 'l'])
            smith_table.set_cols_valign(['m', 'm', 'm'])
            smith_table.set_cols_width([20, 5, 7])
            smith_table.header(['Item', 'Qty', 'Cost'])

            if item_record.sub_type.value.lower() == "weapon":
                weapon_qty = 1
                weapon_type = ctx.bot.compendium.get_object("c_blacksmith_type", "Weapon")
                weapon_items = list(
                    filter(lambda i: i.sub_type.id == weapon_type.id, list(ctx.bot.compendium.blacksmith[0].values())))

                weapon_stock = roll_stock(ctx.bot.compendium, g, weapon_items, weapon_qty, 1, shop.max_cost)

                weapon_data = []
                for i in weapon_stock:
                    weapon = ctx.bot.compendium.get_object("blacksmith", i)
                    weapon_data.append([weapon.name, str(weapon_stock[i]), weapon.display_cost()])

                smith_table.add_rows(sort_stock(weapon_data), header=False)
            elif item_record.sub_type.value.lower() == "armor":
                armor_qty = 1
                armor_type = ctx.bot.compendium.get_object("c_blacksmith_type", "Armor")
                armor_items = list(filter(lambda i: i.sub_type.id == armor_type.id,
                                          list(ctx.bot.compendium.blacksmith[0].values())))

                armor_stock = roll_stock(ctx.bot.compendium, g, armor_items, armor_qty, 1, shop.max_cost)

                armor_data = []
                for i in armor_stock:
                    armor = ctx.bot.compendium.get_object("blacksmith", i)
                    armor_data.append([armor.name, str(armor_stock[i]), armor.display_cost()])

                smith_table.add_rows(sort_stock(armor_data), header=False)
            else:
                return ctx.respond(embed=ErrorEmbed("Can't reroll this item"), ephemeral=True)

            await ctx.delete()
            await ctx.send(f'Re-rolling stock for {ctx.guild.get_channel(shop.channel_id).mention} replacing {item_record.name}')
            await paginate(ctx, smith_table.draw())
            return

        elif shop.type.id == 3 and (item_record := ctx.bot.compendium.get_object("wondrous", item)):  # Magic Shops
            magic_table = Texttable()
            magic_table.set_cols_align(['l', 'c', 'l'])
            magic_table.set_cols_valign(['m', 'm', 'm'])
            magic_table.set_cols_width([20, 5, 7])
            magic_table.header(['Item', 'Qty', 'Cost'])

            magic_qty = 1
            magic_items = list(ctx.bot.compendium.wondrous[0].values())

            magic_stock = roll_stock(ctx.bot.compendium, g, magic_items, magic_qty, 1, shop.max_cost)

            magic_data = []
            for m in magic_stock:
                mItem = ctx.bot.compendium.get_object("wondrous", m)

                magic_data.append([mItem.name, str(magic_stock[m]), str(mItem.cost)])

            magic_table.add_rows(sort_stock(magic_data), header=False)

            await ctx.delete()
            await ctx.send(f'Re-rolling stock for {ctx.guild.get_channel(shop.channel_id).mention} replacing {item_record.name}')
            await paginate(ctx, magic_table.draw())
            return
        else:
            return await ctx.respond(embed=ErrorEmbed(description=f"Error re-rolling inventory"), ephemeral=True)

    @shop_commands.command(
        name="max_cost",
        description="Sets the maximum item cost for the shop inventory"
    )
    async def shop_max_cost(self, ctx: ApplicationContext,
                            max_cost: Option(int, description="Maximum inventory cost, leave blank for no cap")):
        await ctx.defer()

        shop: Shop = await get_shop(ctx.bot, ctx.author.id, ctx.guild_id)

        if shop is None:
            return await ctx.respond(embed=ErrorEmbed(description=f"No shop found owned by {ctx.author.mention}"),
                                     ephemeral=True)

        shop.max_cost = max_cost

        async with self.bot.db.acquire() as conn:
            await conn.execute(update_shop(shop))

        return await ctx.respond(embed=ShopEmbed(ctx, shop))

    @shop_commands.command(
        name="seek",
        description="Log a seek, or set number of seeks available"
    )
    async def shop_seek(self, ctx: ApplicationContext,
                        rarity: Option(str, description="Seek item rarity", required=False,
                                       autocomplete=rarity_autocomplete),
                        phrase: Option(str, description="Flavor text for the roll", required=False),
                        num_seeks: Option(int, description="Number of seeks available", required=False,
                                          min_value=0)):
        await ctx.defer()

        shop: Shop = await get_shop(ctx.bot, ctx.author.id, ctx.guild_id)

        if shop is None:
            return await ctx.respond(embed=ErrorEmbed(description=f"No shop found owned by {ctx.author.mention}"),
                                     ephemeral=True)

        if num_seeks is not None and num_seeks > shop.network + 1:
            return await ctx.respond(embed=ErrorEmbed(description=f"Can't set seeks larger than {shop.network + 1}.\n"
                                                                  f"Consider upgrades."), ephemeral=True)
        elif num_seeks is not None:
            shop.seeks_remaining = num_seeks
            await ctx.respond(f'{shop.seeks_remaining} of {shop.network + 1} seeks remaining.')
        elif shop.seeks_remaining == 0:
            return await ctx.respond(embed=ErrorEmbed(description=f"No more seeks remaining."),
                                     ephemeral=True)
        else:
            if shop.seek_roll is None:
                return await ctx.respond(embed=ErrorEmbed(description=f"No seek roll defined. "
                                                                      f"Please run `/shop set_seek_roll` first"),
                                         ephemeral=True)
            else:
                item_r = ctx.bot.compendium.get_object("c_rarity", rarity)
                dc = None if item_r is None else item_r.seek_dc
                roll = d20.roll(shop.seek_roll)
                shop.seeks_remaining -= 1
                await ctx.respond(embed=ShopSeekEmbed(shop, roll, dc, phrase))

        async with self.bot.db.acquire() as conn:
            await conn.execute(update_shop(shop))



    @shop_commands.command(
        name="info",
        description="Get the information for a shop"
    )
    async def shop_info(self, ctx: ApplicationContext,
                        channel: Option(TextChannel, description="Shop Channel", required=False)):
        await ctx.defer()

        if channel is None:
            channel = ctx.channel

        shop: Shop = await get_shop(ctx.bot, None, None, channel.id)

        if shop is None:
            shop: Shop = await get_shop(ctx.bot, ctx.author.id, ctx.guild_id, None)

        if shop is None:
            return await ctx.respond(embed=ErrorEmbed(description=f"No shop found."),
                                     ephemeral=True)

        return await ctx.respond(embed=ShopEmbed(ctx, shop))

    @shop_commands.command(
        name="set_seek_roll",
        description="Set the seek roll for a shop"
    )
    async def shop_seek_roll(self, ctx: ApplicationContext,
                             roll: Option(str, description="Roll string for the shop", required=True)):
        await ctx.defer()

        shop: Shop = await get_shop(ctx.bot, ctx.author.id, ctx.guild_id)

        if shop is None:
            return await ctx.respond(embed=ErrorEmbed(description=f"No shop found owned by {ctx.author.mention}"),
                                     ephemeral=True)

        try:
            d20.roll(roll)
        except:
            return await ctx.respond(embed=ErrorEmbed(description=f"Roll string `{roll}` is not valid"), ephemeral=True)

        shop.seek_roll = roll

        async with self.bot.db.acquire() as conn:
            await conn.execute(update_shop(shop))

        return await ctx.respond(embed=ShopEmbed(ctx, shop))


    @shop_admin.command(
        name="create",
        description="Opens a new shop"
    )
    async def shop_create(self, ctx: ApplicationContext,
                          name: Option(str, description="Shop name", required=True),
                          type: Option(str, description="Shop type", autocomplete=shop_create_type_autocomplete,
                                       required=True),
                          owner: Option(Member, description="Shop owner", required=True),
                          category_channel: Option(CategoryChannel, description="Shop Channel Category", required=True),
                          shelf: Option(int, description="# of shelf upgrades", required=False, default=0),
                          network: Option(int, description="# of network upgrades", required=False, default=0),
                          mastery: Option(int, description="# of mastery upgrades", required=False, default=0)):
        await ctx.defer()

        shop: Shop = await get_shop(ctx.bot, owner.id, ctx.guild_id)

        if shop is not None:
            return await ctx.respond(embed=ErrorEmbed(description=f"{owner.mention} already owns shop {shop.name}.\n"
                                                                  f"Please inactivate first before opening a new shop"),
                                     ephemeral=True)

        shop_type = ctx.bot.compendium.get_object("c_shop_type", type)
        if shop_type is None:
            return await ctx.respond(embed=ErrorEmbed(description="Invalid shop type"), ephemeral=True)

        chan_perms = dict()
        chan_perms[owner] = discord.PermissionOverwrite(manage_channels=True,
                                                        manage_messages=True)

        shop_channel = await ctx.guild.create_text_channel(
            name=name,
            category=category_channel,
            overwrites=chan_perms,
            reason=f"Opening shop {name}"
        )

        await shop_channel.send(f'{owner.mention} welcome to your new shop.\n'
                                  f'Go ahead and set everything up.\n'
                                  f'1. Make sure you can delete this message\n')

        shop = Shop(guild_id=ctx.guild_id, name=name, type=shop_type, owner_id=owner.id, channel_id=shop_channel.id,
                    shelf=shelf, network=network, mastery=mastery, seeks_remaining=network+1, max_cost=None, seek_roll=None,
                    active=True, inventory_rolled=False)

        async with self.bot.db.acquire() as conn:
            await conn.execute(insert_new_shop(shop))

        shopkeep_role = discord.utils.get(ctx.guild.roles, name="Shopkeeper")

        if shopkeep_role and (shopkeep_role not in owner.roles):
            await owner.add_roles(shopkeep_role, reason=f"Opening shop {name}")

        if sub_role := discord.utils.get(ctx.guild.roles, name=shop_type.value):
            if sub_role not in owner.roles:
                await owner.add_roles(sub_role, reason=f"Opening shop {name}")

        log.info(f"Finished opening shop {name}")

        await sort_shops(ctx, category_channel)

        return await ctx.respond(embed=NewShopEmbed(ctx, shop))

    @shop_admin.command(
        name="upgrade",
        description="Upgrades a shop"
    )
    async def shop_upgrade(self, ctx: ApplicationContext,
                           owner: Option(Member, description="Shop owner", required=True),
                           type: Option(str, description="Upgrade type", autocomplete=upgrade_autocomplete,
                                        required=True),
                           num: Option(int, description="Number of upgrades if more than 1", required=False,
                                       default=1)):

        await ctx.defer()

        shop: Shop = await get_shop(ctx.bot, owner.id, ctx.guild_id)

        if shop is None:
            return await ctx.respond(embed=ErrorEmbed(description=f"No shop found owned by {owner.mention}"),
                                     ephemeral=True)

        if type.upper() == 'SHELF':
            shop.shelf += num
        elif type.upper() == 'NETWORK':
            shop.network += num
            shop.seeks_remaining += num
        elif type.upper() == 'MASTERY':
            shop.mastery += num
        else:
            return await ctx.respond(embed=ErrorEmbed(description=f"Upgrade type not found"), ephemeral=True)

        async with self.bot.db.acquire() as conn:
            await conn.execute(update_shop(shop))

        return await ctx.respond(embed=ShopEmbed(ctx, shop))

    @shop_admin.command(
        name="close",
        description="Close a shop"
    )
    async def close_shop(self, ctx: ApplicationContext,
                         owner: Option(Member, description="Shop Owner", required=True)):
        await ctx.defer()

        shop: Shop = await get_shop(ctx.bot, owner.id, ctx.guild_id)

        if shop is None:
            return await ctx.respond(embed=ErrorEmbed(description=f"No shop found owned by {owner.mention}"),
                                     ephemeral=True)

        to_end = await confirm(ctx, f"Are you sure you want to close {shop.name}? (Reply with yes/no)", True)

        if to_end is None:
            return await ctx.respond(f'Timed out waiting for a response or invalid response.', delete_after=10)
        elif not to_end:
            return await ctx.respond(f'Ok, cancelling.', delete_after=10)

        shop.active = False

        async with self.bot.db.acquire() as conn:
            await conn.execute(update_shop(shop))

        shopkeep_role = discord.utils.get(ctx.guild.roles, name="Shopkeeper")

        if shopkeep_role and (shopkeep_role in owner.roles):
            await owner.remove_roles(shopkeep_role, reason=f"Closing shop {shop.name}")

        if old_role := discord.utils.get(ctx.guild.roles, name=shop.type.value):
            if old_role in owner.roles:
                await owner.remove_roles(old_role, reason=f"Closing shop")

        return await ctx.respond(f'{shop.name}  owned by {owner.mention} closed.')

    @shop_admin.command(
        name="convert",
        description="Convert a shop to a different shop type"
    )
    async def shop_convert(self, ctx: ApplicationContext,
                           owner: Option(Member, description="Shop Owner", required=True),
                           type: Option(str, description="Shop type to convert to",
                                        autocomplete=shop_create_type_autocomplete, required=True)):
        await ctx.defer()

        shop: Shop = await get_shop(ctx.bot, owner.id, ctx.guild_id)

        if shop is None:
            return await ctx.respond(embed=ErrorEmbed(description=f"No shop found owned by {owner.mention}"),
                                     ephemeral=True)

        s_type = ctx.bot.compendium.get_object("c_shop_type", type)

        if old_role := discord.utils.get(ctx.guild.roles, name=shop.type.value):
            if old_role in owner.roles:
                await owner.remove_roles(old_role, reason=f"Converting shop")

        if new_role := discord.utils.get(ctx.guild.roles, name=s_type.value):
            if new_role not in owner.roles:
                await owner.add_roles(new_role, reason=f"Converting shop")

        shop.type = s_type
        shop.inventory_rolled = False

        async with self.bot.db.acquire() as conn:
            await conn.execute(update_shop(shop))

        await sort_shops(ctx, ctx.guild.get_channel(shop.channel_id).category)

        return await ctx.respond(embed=ShopEmbed(ctx, shop))

    @commands.command("sort")
    async def s_sort(self, ctx: ApplicationContext):
        cat = ctx.guild.get_channel(1055210358794633219)
        await sort_shops(ctx, cat)


async def sort_shops(ctx:ApplicationContext, text_category: CategoryChannel):
    shops = await get_all_shops(ctx.bot, ctx.guild.id)
    s_shops = {}

    for type in ctx.bot.compendium.c_shop_type[1]:
        s_shops[type] = [ctx.guild.get_channel(shop.channel_id) for shop in shops if shop.type.value == type]
        s_shops[type].sort(key=lambda x: x.name)

    start = len(text_category.channels) - len(shops)

    channels =text_category.channels[:start]

    channels = channels + s_shops["Consumables"] + s_shops["Blacksmith"] + s_shops["Magic items"]

    if len(channels) != len(text_category.channels):
        log.error(f"Sort shops indexing issue. There are some non-shop channels intermixed")

    for c in channels:
        await c.edit(position=channels.index(c))




