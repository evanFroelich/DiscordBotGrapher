"""Authorization utilities."""
import sqlite3
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from discord import Client


async def isAuthorized(userID: str, guildID: str, client: 'Client') -> bool:
    """Check if a user is authorized (admin or in authorized users list)."""
    guild = client.get_guild(int(guildID))
    if not guild:
        return False
    member = guild.get_member(int(userID))
    if not member:
        return False
    if member.guild_permissions.administrator:
        return True
    main_db = "MY_DB"
    main_conn = sqlite3.connect(main_db)
    main_curs = main_conn.cursor()
    main_curs.execute("SELECT AuthorizedUsers FROM ServerSettings WHERE GuildID = ?", (guildID,))
    result = main_curs.fetchone()
    if result and result[0]:
        authorized_users = json.loads(result[0])
        if str(userID) in authorized_users:
            return True
        return False
    return False

