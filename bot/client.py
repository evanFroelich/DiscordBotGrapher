"""Bot client class."""
import discord
import sqlite3
from discord import app_commands
from handlers.message_handler import handle_message
from handlers.reaction_handler import handle_reaction_add
from handlers.guild_handler import handle_guild_join, handle_thread_create
from tasks.scheduled_tasks import cleanup_abandoned_trivia_loop, package_daily_gambling, daily_question_leaderboard, set_client


class MyClient(discord.Client):
    """Main Discord bot client."""
    
    ignoreList = []
    
    def __init__(self, *, intents, **options):
        super().__init__(intents=intents, **options)
        self.tree = app_commands.CommandTree(self)
    
    async def setup_hook(self):
        """Called when the bot is setting up."""
        await self.tree.sync()
        print('synced')
    
    async def on_ready(self):
        """Called when the bot is ready."""
        print('Logged on as {0}!'.format(self.user))
        channel = self.get_channel(150421071676309504)
        if channel:
            await channel.send("rebooted")
        channel = self.get_channel(1337282148054470808)
        if channel:
            await channel.send("rebooted")
        
        DB_NAME = "My_DB"
        conn = sqlite3.connect(DB_NAME)
        curs = conn.cursor()

        with open('mainDB_Schemas.sql') as f:
            curs.executescript(f.read())
        
        game_conn = sqlite3.connect("games.db")
        game_curs = game_conn.cursor()
        with open('gamesDB_Schemas.sql') as f:
            game_curs.executescript(f.read())
        game_conn.commit()
        
        currentGuilds = [guild.id for guild in self.guilds]
        print(currentGuilds)
        for guild in currentGuilds:
            curs.execute('''INSERT OR IGNORE INTO ServerSettings (GuildID) VALUES (?);''', (guild,))
            game_curs.execute('''INSERT OR IGNORE INTO GoofsGaffs (GuildID) VALUES (?);''', (guild,))
            game_curs.execute('''INSERT OR IGNORE INTO GamblingUnlockConditions (GuildID) VALUES (?);''', (guild,))
            game_curs.execute('''INSERT OR IGNORE INTO FeatureTimers (GuildID) VALUES (?);''', (guild,))
            game_curs.execute('''INSERT OR IGNORE INTO ServerSettings (GuildID) VALUES (?);''', (guild,))

        conn.commit()
        curs.execute('''CREATE INDEX IF NOT EXISTS idx_guild_time ON Master (GuildID, UTCTime)''')
        
        curs.execute("PRAGMA temp_store = MEMORY;")
        curs.execute("PRAGMA synchronous = NORMAL;")
        curs.execute("PRAGMA journal_mode = WAL;")
        curs.execute("PRAGMA cache_size = 1000000;")
        conn.commit()
        game_conn.commit()
        curs.close()
        conn.close()
        game_curs.close()
        game_conn.close()
        
        # Set client reference for tasks
        set_client(self)
        
        # Start scheduled tasks
        if not cleanup_abandoned_trivia_loop.is_running():
            cleanup_abandoned_trivia_loop.start()
        if not package_daily_gambling.is_running():
            package_daily_gambling.start()
        if not daily_question_leaderboard.is_running():
            daily_question_leaderboard.start()
        
        await self.tree.sync()
    
    async def on_thread_create(self, thread):
        """Called when a thread is created."""
        await handle_thread_create(self, thread)
    
    async def on_guild_join(self, guild):
        """Called when the bot joins a guild."""
        await handle_guild_join(self, guild)
    
    async def on_reaction_add(self, reaction, user):
        """Called when a reaction is added."""
        await handle_reaction_add(self, reaction, user)
    
    async def on_message(self, message):
        """Called when a message is received."""
        await handle_message(self, message)

