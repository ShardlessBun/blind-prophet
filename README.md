# blind-prophet
For the Blind Prophet Discord ~~Gsheet~~ bot.

## Environment variables:
| Name                         | Description                                                                                                                                              | Used by/for                        | Required |
|------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------|----------|
| `ADMIN_GUILDS`               | Guilds where the `Admin` command group commands are available                                                                                            | DEV Team for command restrictions  | No       |
| `BOT_OWNERS`                 | Listed as the owners of the Bot for `Admin` command group command checks                                                                                 | DEV Team for command checks        | No       | 
| `BOT_TOKEN`                  | The token for your bot as found on the Discord Developer portal. See this documentation for more details: https://docs.pycord.dev/en/master/discord.html | Connections to Discord API         | **Yes**  |   
| `COMMAND_PREFIX`             | The command prefix used for this Bot's commands. For example, '>' would be the command prefix in `>rp @TestUser`. *Default is `>`*                       | Non-slash command prefix           | **Yes**  |
| `DASHBOARD_REFRESH_INTERVAL` | Refresh interval for dashboards in minutes. *Default is 15 minutes if not set.*                                                                          | `Dashboards` cog for task interval | No       |
| `DATABASE_URL`               | Full Postgres database URL. Example: `postgresql://<user>:<password>@<server>:<port>/<database>`                                                         | Connection to DB                   | **Yes**  |
| `GUILD`                      | Debug guilds for the bot. Used for non-production versions only.                                                                                         | Guild IDs for debugging            | No       |


## Roles:
All assumed roles by the bot.
* **Loremaster**: Adventure/Lore overseer
* **Lead DM**: Helps manage adventures/DM's
* **Quester**: Players eligible for adventures
* **Fledgling**: Members who have yet to create a character
* **Shopkeeper**: Shopkeer role for members who own shops. 

### Faction Roles
Used by the faction commands. Each faction should have a Role with the same name
* **Guild Initiate**: Inital role for starting characters 
* **Guild Member**: Role for characters who have completed initial quests
* **Order of the Copper Dragons**: Nerds
* **Silent Whispers**: Naruto fans
* **Silver Wolves**: #TeamJacob
* **Crimson Blades**: Lookin for a fight
* **Clover Conclave**: Likes trees
* **Sunstone Lotus**: Huff paint
* **Falcon Eyes**: Reads/watches a lot of Sherlock Holmes
* **Azure Guardians**: Thicc blue line

### Arena Roles
For any TextChannel used for the `Arena` command group, should have a corresponding Role with the same name.