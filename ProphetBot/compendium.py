import asyncio
import logging
from timeit import default_timer as timer
from types import NoneType

from ProphetBot.models.db_objects.item_objects import ItemBlacksmith, ItemWondrous, ItemConsumable, ItemScroll
from ProphetBot.models.schemas.category_schema import *
from ProphetBot.models.schemas.item_schema import ItemBlacksmithSchema, ItemWondrousSchema, ItemConsumableSchema, \
    ItemScrollSchema
from ProphetBot.queries import get_blacksmith_items, get_wondrous_items, get_consumable_items, get_scroll_items
from ProphetBot.queries.category_queries import *

log = logging.getLogger(__name__)


async def get_table_values(conn, query, obj, schema) -> []:
    d1 = dict()
    d2 = dict()
    ary = []
    async for row in conn.execute(query):
        val: obj = schema.load(row)
        d1[val.id] = val

        if hasattr(val, "value"):
            d2[val.value] = val
        elif hasattr(val, "avg_level"):
            d2[val.avg_level] = val
        elif hasattr(val, "name"):
            d2[val.name] = val
    ary.append(d1)
    ary.append(d2)
    return ary


class Compendium:

    # noinspection PyTypeHints
    def __init__(self):

        """
        Structure will generally be:
        self.attribute[0] = dict(object.id) = object
        self.attribute[1] = dict(object.value) = object

        This can help ensure o(1) for lookups on id/value. o(n) for any filtering
        """

        self.c_rarity = []
        self.c_blacksmith_type = []
        self.c_consumable_type = []
        self.c_magic_school = []
        self.c_character_class = []
        self.c_character_subclass = []
        self.c_character_race = []
        self.c_character_subrace = []
        self.c_global_modifier = []
        self.c_host_status = []
        self.c_arena_tier = []
        self.c_adventure_tier = []
        self.c_adventure_rewards = []
        self.c_shop_type = []
        self.c_activity = []
        self.c_faction = []
        self.c_dashboard_type = []
        self.c_level_caps = []
        self.c_shop_tier = []

        # Items
        self.blacksmith = []
        self.wondrous = []
        self.consumable = []
        self.scroll = []

    async def reload_categories(self, bot):
        start = timer()

        if not hasattr(bot, "db"):
            return

        async with bot.db.acquire() as conn:
            self.c_rarity = await get_table_values(conn, get_c_rarity(), Rarity, RaritySchema())
            self.c_blacksmith_type = await get_table_values(conn, get_c_blacksmith_type(), BlacksmithType,
                                                            BlacksmithTypeSchema())
            self.c_consumable_type = await get_table_values(conn, get_c_consumable_type(), ConsumableType,
                                                            ConsumableTypeSchema())
            self.c_magic_school = await get_table_values(conn, get_c_magic_school(), MagicSchool,
                                                         MagicSchoolSchema())
            self.c_character_class = await get_table_values(conn, get_c_character_class(), CharacterClass,
                                                            CharacterClassSchema())
            self.c_character_subclass = await get_table_values(conn, get_c_character_subclass(),
                                                               CharacterSubclass, CharacterSubclassSchema())
            self.c_character_race = await get_table_values(conn, get_c_character_race(), CharacterRace,
                                                           CharacterRaceSchema())
            self.c_character_subrace = await get_table_values(conn, get_c_character_subrace(), CharacterSubrace,
                                                              CharacterSubraceSchema())
            self.c_global_modifier = await get_table_values(conn, get_c_global_modifier(), GlobalModifier,
                                                            GlobalModifierSchema())
            self.c_host_status = await get_table_values(conn, get_c_host_status(), HostStatus,
                                                        HostStatusSchema())
            self.c_arena_tier = await get_table_values(conn, get_c_arena_tier(), ArenaTier, ArenaTierSchema())
            self.c_adventure_tier = await get_table_values(conn, get_c_adventure_tier(), AdventureTier,
                                                           AdventureTierSchema())
            self.c_adventure_rewards = await get_table_values(conn, get_c_adventure_rewards(), AdventureRewards,
                                                              AdventureRewardsSchema())
            self.c_shop_type = await get_table_values(conn, get_c_shop_type(), ShopType, ShopTypeSchema())
            self.c_activity = await get_table_values(conn, get_c_activity(), Activity, ActivitySchema())
            self.c_faction = await get_table_values(conn, get_c_faction(), Faction, FactionSchema())
            self.c_dashboard_type = await get_table_values(conn, get_c_dashboard_type(), DashboardType,
                                                           DashboardTypeSchema())
            self.c_level_caps = await get_table_values(conn, get_c_level_caps(), LevelCaps, LevelCapsSchema())
            self.c_shop_tier = await get_table_values(conn, get_c_shop_tiers(), ShopTier, ShopTierSchema())

        end = timer()
        log.info(f'COMPENDIUM: Categories reloaded in [ {end - start:.2f} ]s')

    async def load_items(self, bot):
        if not hasattr(bot, "db"):
            return
        else:
            start = timer()
            async with bot.db.acquire() as conn:
                self.blacksmith = await get_table_values(conn, get_blacksmith_items(), ItemBlacksmith,
                                                         ItemBlacksmithSchema(self))
                self.wondrous = await get_table_values(conn, get_wondrous_items(), ItemWondrous,
                                                       ItemWondrousSchema(self))
                self.consumable = await get_table_values(conn, get_consumable_items(), ItemConsumable,
                                                         ItemConsumableSchema(self))
                self.scroll = await get_table_values(conn, get_scroll_items(), ItemScroll,
                                                     ItemScrollSchema(self))

            end = timer()
            log.info(f"COMPENDIUM: Items reloaded in [ {end - start:.2f} ]s")

    def get_object(self, node: str, value: str | int = None):
        if hasattr(self, node):
            if len(self.__getattribute__(node)) > 0:
                try:
                    if isinstance(value, int):
                        return self.__getattribute__(node)[0][value]
                    else:
                        return self.__getattribute__(node)[1][value]
                except KeyError:
                    return None
            else:
                raise AttributeError(f"{node} has not been populated yet")
                return None
        else:
            raise KeyError(f"{node} does not exist in the compendium")
            return None
