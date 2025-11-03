"""Guild handler for the Discord bot."""
import sqlite3
from utils.database import create_guild_db_entry


async def handle_guild_join(client, guild):
    """Handle guild join events."""
    DB_NAME = "My_DB"
    conn = sqlite3.connect(DB_NAME)
    curs = conn.cursor()
    curs.execute('''INSERT OR IGNORE INTO ServerSettings (GuildID) VALUES (?);''', (guild.id,))
    conn.commit()
    curs.close()
    conn.close()
    games_conn = sqlite3.connect("games.db")
    games_curs = games_conn.cursor()
    games_curs.execute('''INSERT INTO GamblingUnlockConditions (GuildID) values (?)''', (guild.id,))
    games_conn.commit()
    games_curs.execute('''INSERT INTO ServerSettings (GuildID) VALUES (?)''', (guild.id,))
    games_conn.commit()
    games_curs.execute('''INSERT OR IGNORE INTO FeatureTimers (GuildID) VALUES (?);''', (guild.id,))
    games_conn.commit()
    games_curs.execute('''INSERT OR IGNORE INTO GoofsGaffs (GuildID) VALUES (?);''', (guild.id,))
    games_conn.commit()
    games_curs.close()
    games_conn.close()


async def handle_thread_create(client, thread):
    """Handle thread create events."""
    await thread.join()

