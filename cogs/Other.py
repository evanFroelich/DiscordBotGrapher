import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import random





class Ping(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(name="ping", description="pong!")
    async def ping(self, interaction: discord.Interaction):

        gamesDB = "games.db"
        games_conn = sqlite3.connect(gamesDB)
        games_curs = games_conn.cursor()

        games_curs.execute(
            '''INSERT INTO CommandLog (GuildID, UserID, CommandName)
               VALUES (?, ?, ?)''',
            (interaction.guild.id, interaction.user.id, "ping")
        )

        games_conn.commit()
        games_curs.close()
        games_conn.close()

        rand = random.random()
        payload = ""

        if rand < .2: payload = "pong"
        elif rand < .4: payload = "song"
        elif rand < .6: payload = "dong"
        elif rand < .8: payload = "long"
        elif rand < .99: payload = "kong"
        else: payload = "you found the special message. here is your gold star!"

        await interaction.response.send_message(payload)

class DevOnly(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(name="dev-only", description="developer only command")
    async def dev_only_command(self, interaction: discord.Interaction):
        #sync command tree
        if interaction.user.id == 100344687029665792:  # replace with your Discord user ID
            await self.tree.sync()
            await interaction.response.send_message("Command tree synced.")
        else:
            await interaction.response.send_message("not for you",ephemeral=True)
        #await interaction.response.send_message("This is a developer only command.")


class Test(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(name="test", description="test command")
    async def test_command(self, interaction: discord.Interaction):
        view = discord.ui.View()
        test_select_menu = TestSelectMenu()
        view.add_item(test_select_menu)
        #await interaction.response.send_message("This is a test command.", view=view)
        modal = TestModal()
        await interaction.response.send_modal(modal)

class TestModal(discord.ui.Modal, title="Test Modal"):
    def __init__(self):
        super().__init__()
        #add a text input to the modal
        self.test_input = discord.ui.TextInput(label="Test Input", placeholder="Enter something...", required=True)
        #add the select menu to the modal
        self.test_select_menu = TestSelectMenu()
        #self.add_item(self.test_select_menu)
        self.add_item(self.test_input)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"You entered: {self.test_input.value}")

class TestSelectMenu(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Option 1", description="This is the first option", value="1"),
            discord.SelectOption(label="Option 2", description="This is the second option", value="2"),
            discord.SelectOption(label="Option 3", description="This is the third option", value="3"),
        ]
        super().__init__(placeholder="Choose an option", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"You selected {self.values[0]}")


async def setup(client: commands.Bot):
    await client.add_cog(Ping(client))
    await client.add_cog(Test(client))
    await client.add_cog(DevOnly(client))