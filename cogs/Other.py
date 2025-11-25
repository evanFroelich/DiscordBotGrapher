import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import random
import json





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
        games_conn = sqlite3.connect("games.db")
        games_conn.row_factory = sqlite3.Row
        games_curs = games_conn.cursor()
        games_curs.execute('''SELECT * FROM ShadowListQueue order by ID asc limit 1''')
        row = games_curs.fetchone()
        #print the contents of the row
        printstr=""
        for key in row.keys():
            printstr += f"{key}: {row[key]}\n"
        print(printstr)
        if row:
            if interaction.user.id != 100344687029665792:  #replace with your user id
                await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)
                return
            shadowAnswers=[]
            if row["ShadowAnswers"] is not None:
                shadowAnswers = json.loads(row["ShadowAnswers"])
            view = discord.ui.View()
            approveButton=decisionButton(label="Approve", style=discord.ButtonStyle.green, ID=row["ID"], shadowAnswers=shadowAnswers, QID=row["QID"])
            denyButton=decisionButton(label="Deny", style=discord.ButtonStyle.red, ID=row["ID"], shadowAnswers=shadowAnswers, QID=row["QID"])
            view.add_item(approveButton)
            view.add_item(denyButton)
            await interaction.response.send_message(f"Question: {row['Question']}\nGiven answer: {row['GivenAnswer']}\nShadow answers: {row['ShadowAnswers']}\nUser answer: {row['UserAnswer']}\nLLMResponse: {row['LLMResponse']}", view=view)

class decisionButton(discord.ui.Button):
    def __init__(self, label: str, style: discord.ButtonStyle, ID: int, shadowAnswers: list[str], QID: int):
        super().__init__(label=label, style=style)
        self.ID = ID
        self.QID = QID
        self.shadowAnswers = shadowAnswers

    async def callback(self, interaction: discord.Interaction):
        #make sure only my user id can use this button
        if interaction.user.id == 100344687029665792:  #replace with your user id
            games_conn = sqlite3.connect("games.db")
            games_conn.row_factory = sqlite3.Row
            games_curs = games_conn.cursor()
            #get the row from the ShadowListQueue table with the matching ID
            games_curs.execute('''SELECT * FROM ShadowListQueue WHERE ID=?''', (self.ID,))
            row = games_curs.fetchone()
            if self.label == "Approve":
                #get the ShadowAnswers from the database
                self.shadowAnswers.append(row["UserAnswer"])
                games_curs.execute('''UPDATE QuestionList SET ShadowAnswers=? WHERE ID=?''', (json.dumps(self.shadowAnswers), self.QID))
                games_conn.commit()
            games_curs.execute('''DELETE FROM ShadowListQueue WHERE ID=?''', (self.ID,))
            games_conn.commit()
            #grab the next entry from the ShadowListQueue
            games_curs.execute('''SELECT * FROM ShadowListQueue order by ID asc limit 1''')
            row = games_curs.fetchone()
            if row:
                view = discord.ui.View()
                shadowAnswers=[]
                if row["ShadowAnswers"] is not None:
                    shadowAnswers = json.loads(row["ShadowAnswers"])
                approveButton=decisionButton(label="Approve", style=discord.ButtonStyle.green, ID=row["ID"], shadowAnswers=shadowAnswers, QID=row["QID"])
                denyButton=decisionButton(label="Deny", style=discord.ButtonStyle.red, ID=row["ID"], shadowAnswers=shadowAnswers, QID=row["QID"])
                view.add_item(approveButton)
                view.add_item(denyButton)
                await interaction.response.edit_message(content=f"Question: {row['Question']}\nGiven answer: {row['GivenAnswer']}\nShadow answers: {row['ShadowAnswers']}\nUser answer: {row['UserAnswer']}\nLLMResponse: {row['LLMResponse']}", view=view)
            games_curs.close()
            games_conn.close()


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