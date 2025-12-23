import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import asyncio
import random
from datetime import datetime, timedelta
import json
import re
import time
import trueskill
from Helpers.Helpers import create_user_db_entry, numToGrade, delete_later, isAuthorized, achievementTrigger, achievement_leaderboard_generator, auction_house_command, ButtonLockout, rank_number_to_rank_name, leaderboard_generator


class GradeReport(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    @app_commands.command(name="grade-report", description="shows your grade report for the server")
    @app_commands.choices(visibility=[
        app_commands.Choice(name="public", value="public"),
        app_commands.Choice(name="private", value="private")
    ])
    async def gradereport(self, interaction: discord.Interaction, visibility: app_commands.Choice[str]):
        gamesDB = "games.db"
        games_conn = sqlite3.connect(gamesDB)
        games_curs = games_conn.cursor()
        games_curs.execute('''INSERT INTO CommandLog (GuildID, UserID, CommandName, CommandParameters) VALUES (?, ?, ?, ?)''', (interaction.guild.id, interaction.user.id, "grade-report", f"visibility: {visibility.value}"))
        games_conn.commit()
        await create_user_db_entry(interaction.guild.id, interaction.user.id)
        games_curs.execute('''select Category, Difficulty, Num_Correct, Num_Incorrect from Scores where GuildID = ? and UserID = ? order by category, difficulty''', (interaction.guild.id, interaction.user.id))
        rows = games_curs.fetchall()
        if not rows:
            await interaction.response.send_message("You have no scores recorded for this server.", ephemeral=True)
            games_curs.close()
            games_conn.close()
            return
        outstr = "```Your Grade Report:"
        accumulationStr = ""
        previousCategory = ""
        previousDifficulty = 5
        for row in rows:
            category = row[0]
            difficulty = row[1]
            num_correct = row[2]
            num_incorrect = row[3]
            total = num_correct + num_incorrect
            if total>0:
                if previousCategory != category:
                    fillSlashes=5-previousDifficulty
                    for i in range(fillSlashes):
                        accumulationStr += f"-/"
                    outstr += accumulationStr
                    outstr = outstr[:-1]
                    accumulationStr = f"\n{category:<17}"
                    
                    fillIn=difficulty-1
                    for i in range(fillIn):
                        accumulationStr += f"-/"
                elif difficulty-previousDifficulty > 1:
                    diff=difficulty-previousDifficulty
                    diff=diff-1
                    for i in range(diff):
                        accumulationStr += f"-/"
                    previousDifficulty = difficulty
                previousCategory = category
                previousDifficulty = difficulty
                percentage = (num_correct / total) * 100
                grade = await numToGrade(percentage)
                accumulationStr += f"{grade}/"
                #outstr += accumulationStr
            # if total > 0:
            #     percentage = (num_correct / total) * 100
            #     grade = await numToGrade(percentage)
            #     outstr += f"Grade {difficulty:<1}{category:<20}{grade:<4}\n"
            else:
                outstr += f"Category: {category}, Difficulty: {difficulty}, No attempts recorded.\n"
        outstr += accumulationStr
        outstr += "```"
        await interaction.response.send_message(outstr, ephemeral=(visibility.value == "private"))
        
        games_curs.close()
        games_conn.close()

class Leaderboard(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(name="leaderboard", description="various leaderboards")
    @app_commands.choices(subtype=[
        app_commands.Choice(name="bonus-points", value="pip"),
        app_commands.Choice(name="coin-flip", value="flip"),
        app_commands.Choice(name="balance", value="balance"),
        app_commands.Choice(name="achievement-score", value="achievement-score"),
        app_commands.Choice(name="ranked-dice", value="ranked-dice")
    ])
    @app_commands.choices(visibility=[
        app_commands.Choice(name="public", value="public"),
        app_commands.Choice(name="private", value="private")
    ])
    async def leaderboard(self, interaction: discord.Interaction, subtype: app_commands.Choice[str], visibility: app_commands.Choice[str]):
        gamesDB = "games.db"
        games_conn = sqlite3.connect(gamesDB)
        games_curs = games_conn.cursor()
        games_curs.execute('''INSERT INTO CommandLog (GuildID, UserID, CommandName, CommandParameters) VALUES (?, ?, ?, ?)''', (interaction.guild.id, interaction.user.id, "leaderboard", f"subtype: {subtype.value}, visibility: {visibility.value}"))
        games_conn.commit()
        games_curs.close()
        games_conn.close()
        privMsg=True if visibility.value=="private" else False
        await interaction.response.defer(thinking=True,ephemeral=privMsg)
        embed=discord.Embed(title="Leaderboard", color=0x228a65)
        embed = await leaderboard_generator(guildID = str(interaction.guild.id), type=subtype.value, visibility=privMsg, interaction=interaction, embed=embed)
        refreshButton = leaderboard_refresh_button(subtype=subtype.value, visibility=privMsg, guild_id=str(interaction.guild.id))
        view = discord.ui.View(timeout=None)
        view.add_item(refreshButton)
        msg = await interaction.followup.send(embed=embed, ephemeral=privMsg, view=view)
        if subtype.value == "flip":
            asyncio.create_task(delete_later(message=msg, time=60))
        

class leaderboard_refresh_button(discord.ui.Button):
    def __init__(self, subtype: str, visibility: bool, guild_id: str):
        super().__init__(label="Refresh Leaderboard", style=discord.ButtonStyle.primary)
        self.subtype = subtype
        self.visibility = visibility
        self.guild_id = guild_id

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Leaderboard", color=0x228a65)
        embed = await leaderboard_generator(guildID=self.guild_id, type=self.subtype, visibility=self.visibility, interaction=interaction, embed=embed)
        await interaction.response.edit_message(embed=embed)


class FlipGame(commands.Cog):
    def __init__(self, client):
        self.client = client

    @app_commands.command(name="flip",description="Flip a coin")
    async def flip_coin(self, interaction: discord.Interaction):
        #check if the user has a row with this guild in the coinFlipLeaderboard table
        games_conn=sqlite3.connect("games.db",timeout=10)
        games_curs = games_conn.cursor()
        games_curs.execute('''INSERT INTO CommandLog (GuildID, UserID, CommandName) VALUES (?, ?, ?)''', (interaction.guild.id, interaction.user.id, "flip"))
        games_conn.commit()
        #check if the users row exists
        games_curs.execute('''SELECT * FROM coinFlipLeaderboard WHERE UserID=?''', (interaction.user.id,))
        row = games_curs.fetchone()
        streak = 0
        if row is None:
            # If the row doesn't exist, create it
            games_curs.execute('''INSERT INTO coinFlipLeaderboard (UserID) VALUES (?)''', (interaction.user.id,))
        else:
            streak = row[1]  # Get the current streak from the database
        games_conn.commit()
        description=f"Your current coin flip streak is {streak}."
        flipButton = FlipButton(user_id=interaction.user.id, guild_id=interaction.guild.id)
        view = discord.ui.View(timeout=None)
        view.add_item(flipButton)
        await interaction.response.send_message(description, ephemeral=True,view=view)
        #result = "heads" if random.random() < 0.5 else "tails"
        #await interaction.followup.send(f"The coin landed on {result}!")

class FlipButton(discord.ui.Button):
    def __init__(self, user_id=None, guild_id=None):
        super().__init__(label="Flip a Coin", style=discord.ButtonStyle.primary)
        self.user_id = user_id
        self.guild_id = guild_id

    async def callback(self, interaction: discord.Interaction):
        result = 1 if random.random() < 0.5 else 0
        #update the table with +1 if heads, set to 0 if tails
        games_db = "games.db"
        games_conn = sqlite3.connect(games_db)
        games_curs = games_conn.cursor()
        if result == 1:
            #modify to also pass in the current timestamp
            games_curs.execute('''UPDATE coinFlipLeaderboard SET CurrentStreak = CurrentStreak + 1, LastFlip=?, TimesFlipped = TimesFlipped + 1, TotalHeads = TotalHeads + 1, CurrentTailsStreak = 0 WHERE UserID=?''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), interaction.user.id))
            games_conn.commit()
            await achievementTrigger(interaction.guild.id, interaction.user.id, 'CurrentStreak')
            await achievementTrigger(interaction.guild.id, interaction.user.id, 'TimesFlipped')
        else:
            games_curs.execute('''UPDATE coinFlipLeaderboard SET CurrentStreak = 0, LastFlip=?, TimesFlipped = TimesFlipped + 1, CurrentTailsStreak = CurrentTailsStreak + 1, TotalTails = TotalTails + 1 WHERE UserID=?''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), interaction.user.id))
            games_conn.commit()
        games_conn.commit()
        games_curs.execute('''SELECT * FROM coinFlipLeaderboard WHERE UserID=?''', (interaction.user.id,))
        row = games_curs.fetchone()
        #update the content of the message the button is attached to
        await interaction.response.edit_message(content=f"The coin landed on {'heads' if result == 1 else 'tails'}! your streak is now {row[1]}")
        self.label = "Flip again?"
        return

class GameSettingsGet(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    @app_commands.command(name="game-settings-get", description="Get server settings")
    async def serversettingscommandget(self, interaction: discord.Interaction):
        #get and display all values in the serversettings table for the given server
        games_conn=sqlite3.connect("games.db",timeout=10)
        games_curs = games_conn.cursor()
        games_curs.execute('''INSERT INTO CommandLog (GuildID, UserID, CommandName) VALUES (?, ?, ?)''', (interaction.guild.id, interaction.user.id, "game-settings-get"))
        games_conn.commit()
        games_curs.execute("SELECT * FROM ServerSettings WHERE GuildID = ?", (interaction.guild.id,))
        rows = games_curs.fetchall()
        if not rows:
            await interaction.response.send_message("No server settings found.")
            return
        columns= [desc[0] for desc in games_curs.description]
        settings = "\n".join([f"{col}: {val}" for col, val in zip(columns, rows[0])])
        settings = re.sub(r'\b(\d{17,19})\b', r'<#\1>', settings)
        await interaction.response.send_message(f"Server settings for {interaction.guild.name}:\n{settings}")

        games_curs.close()
        games_conn.close()

class GoofsSettingsGet(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    @app_commands.command(name="goofs-settings-get", description="Get goofs and gaffs settings")
    async def goofs_settings_command_get(self, interaction: discord.Interaction):
        # Get and display the goofs and gaffs setting for the given server
        games_conn=sqlite3.connect("games.db",timeout=10)
        games_curs = games_conn.cursor()
        games_curs.execute('''INSERT INTO CommandLog (GuildID, UserID, CommandName) VALUES (?, ?, ?)''', (interaction.guild.id, interaction.user.id, "goofs-settings-get"))
        games_conn.commit()
        games_curs.execute("SELECT * FROM GoofsGaffs WHERE GuildID = ?", (interaction.guild.id,))
        rows = games_curs.fetchall()
        if not rows:
            await interaction.response.send_message("No server settings found.")
            return
        columns= [desc[0] for desc in games_curs.description]
        settings = "\n".join([f"{col}: {val}" for col, val in zip(columns, rows[0])])
        settings = re.sub(r'\b(\d{17,19})\b', r'<#\1>', settings)
        await interaction.response.send_message(f"Goofs and Gaffs settings for {interaction.guild.name}:\n{settings}")

        games_curs.close()
        games_conn.close()

class GameSettingsSet(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    @app_commands.command(name="game-settings-set", description="Manage game settings")
    @app_commands.describe(numberofquestionsperday="Number of random questions a user can answer per day")
    @app_commands.describe(questiontimeout="Timeout in seconds for random questions that appear in the chat")
    @app_commands.describe(pipchance="The base chance that a message will trigger a bonus pip reaction. chance goes from 0 -> X over a period of time to mitigate spam. .1=10% 1=100%")
    @app_commands.describe(questionchance="The base chance that a random question will be asked in chat following a users message. .1=10% 1=100%")
    @app_commands.describe(flagshamechannel="Flag to enable or disable the shame channel feature. 1 is on 0 is off")
    @app_commands.describe(shamechannel="Channel ID for the shame channel where incorrect answers are posted")
    @app_commands.describe(flagignoredchannels=" 1 is on 0 is off")
    @app_commands.describe(ignoredchannels="Channel ID for the ignored channels to add or remove")
    @app_commands.describe(flaggoofsgaffs="Flag to enable chat response goofs and gaffs. 1 is on 0 is off")
    @app_commands.describe(flagachievements="Flag to enable or disable achievements. 1 is on 0 is off")
    async def gamesettingscommandset(self, interaction: discord.Interaction, numberofquestionsperday: int = None, questiontimeout: int = None, pipchance: float = None, questionchance: float = None, flagshamechannel: int = None, shamechannel: str = None, flagignoredchannels: int = None, ignoredchannels: str = None, flaggoofsgaffs: int = None, flagachievements: int = None):
        games_conn=sqlite3.connect("games.db",timeout=10)
        games_curs = games_conn.cursor()
        games_curs.execute('''INSERT INTO CommandLog (GuildID, UserID, CommandName, CommandParameters) VALUES (?, ?, ?, ?)''', (interaction.guild.id, interaction.user.id, "game-settings-set", f"'numberofquestionsperday': {numberofquestionsperday}, 'questiontimeout': {questiontimeout}, 'pipchance': {pipchance}, 'questionchance': {questionchance}, 'flagshamechannel': {flagshamechannel}, 'shamechannel': {shamechannel}, 'flagignoredchannels': {flagignoredchannels}, 'ignoredchannels': {ignoredchannels}, 'flaggoofsgaffs': {flaggoofsgaffs}, 'flagachievements': {flagachievements}'"))
        games_conn.commit()
        games_curs.close()
        games_conn.close()
        if not await isAuthorized(str(interaction.user.id), str(interaction.guild.id), self.client):
            await interaction.response.send_message("You are not authorized to use this command. ask an administrator to authorize you using the /addAuthorizedUser command.",ephemeral=True)
            return
        #go through each parameter and if it is not none, update the database with its new value
        games_conn=sqlite3.connect("games.db",timeout=10)
        games_curs = games_conn.cursor()
        changedSettings=""
        errorString=""
        if numberofquestionsperday is not None:
            if numberofquestionsperday < 1:
                errorString+=f"Number of questions per day must be at least 1.\n"
            else:
                games_curs.execute("UPDATE ServerSettings SET NumQuestionsPerDay = ? WHERE GuildID = ?", (numberofquestionsperday, interaction.guild.id))
                changedSettings+=f"Number of questions per day updated to {numberofquestionsperday}\n"
        if questiontimeout is not None:
            if questiontimeout < 1:
                errorString+=f"Question timeout must be at least 1 second.\n"
            else:
                games_curs.execute("UPDATE ServerSettings SET QuestionTimeout = ? WHERE GuildID = ? ", (questiontimeout, interaction.guild.id))
                changedSettings+=f"Question timeout updated to {questiontimeout}\n"
        if pipchance is not None:
            if pipchance <= 0:
                errorString+=f"Pip chance must be above 0.\n"
            else:
                games_curs.execute("UPDATE ServerSettings SET PipChance = ? WHERE GuildID = ?", (pipchance, interaction.guild.id))
                changedSettings+=f"Pip chance updated to {pipchance}\n"
        if questionchance is not None:
            if questionchance <= 0:
                errorString+=f"Question chance must be above 0.\n"
            else:
                games_curs.execute("UPDATE ServerSettings SET QuestionChance = ? WHERE GuildID = ?", (questionchance, interaction.guild.id))
                changedSettings+=f"Question chance updated to {questionchance}\n"
        if flagshamechannel is not None:
            if flagshamechannel not in [0, 1]:
                errorString+=f"Flag shame channel must be 0 or 1 to represent off or on.\n"
            else:
                games_curs.execute("UPDATE ServerSettings SET FlagShameChannel = ? WHERE GuildID = ?", (flagshamechannel, interaction.guild.id))
                changedSettings+=f"Shame channel flag updated to {flagshamechannel}\n"
        if shamechannel is not None:
            #check to see if the id is a valid channel in this server
            if int(shamechannel) not in [channel.id for channel in interaction.guild.text_channels] and int(shamechannel) not in [thread.id for thread in interaction.guild.threads]:
                errorString+=f"Shame channel must be a valid text channel or thread in this server.\n"
            else:
                games_curs.execute("UPDATE ServerSettings SET ShameChannel = ? WHERE GuildID = ?", (shamechannel, interaction.guild.id))
                changedSettings+=f"Shame channel updated to <#{shamechannel}>\n"
        if flagignoredchannels is not None:
            if flagignoredchannels not in [0, 1]:
                errorString+=f"Flag ignored channels must be 0 or 1 to represent off or on.\n"
            else:
                games_curs.execute("UPDATE ServerSettings SET FlagIgnoredChannels = ? WHERE GuildID = ?", (flagignoredchannels, interaction.guild.id))
                changedSettings+=f"Ignored channels flag updated to {flagignoredchannels}\n"
        if ignoredchannels is not None:
            #check to see if the id is a valid channel in this server
            if int(ignoredchannels) not in [channel.id for channel in interaction.guild.text_channels]:
                errorString+=f"Ignored channels must be valid text channels in this server.\n"
            else:
                #pull list from db and turn the string back into a list
                games_curs.execute("SELECT IgnoredChannels FROM ServerSettings WHERE GuildID = ?", (interaction.guild.id,))
                result = games_curs.fetchone()
                if result and result[0]:
                    ignoredchannels_list = json.loads(result[0])
                    if ignoredchannels not in ignoredchannels_list:
                        ignoredchannels_list.append(ignoredchannels)
                        ignoredchannels_json=json.dumps(ignoredchannels_list)
                        #ignoredchannels = json.dumps(ignoredchannels_list)
                        games_curs.execute("UPDATE ServerSettings SET IgnoredChannels = ? WHERE GuildID = ?", (ignoredchannels_json, interaction.guild.id))
                        changedSettings+=f"Ignored channels added <#{ignoredchannels}>\n"
                    else:
                        ignoredchannels_list.remove(ignoredchannels)
                        ignoredchannels_json = json.dumps(ignoredchannels_list)
                        games_curs.execute("UPDATE ServerSettings SET IgnoredChannels = ? WHERE GuildID = ?", (ignoredchannels_json, interaction.guild.id))
                        changedSettings+=f"Ignored channels removed <#{ignoredchannels}>\n"
                else:
                    ignoredchannels_json = json.dumps([ignoredchannels])
                    games_curs.execute("UPDATE ServerSettings SET IgnoredChannels = ? WHERE GuildID = ?", (ignoredchannels_json, interaction.guild.id))
                    changedSettings+=f"Ignored channels set to <#{ignoredchannels}>\n"

        if flaggoofsgaffs is not None:
            if flaggoofsgaffs not in [0, 1]:
                errorString+=f"Flag goofs and gaffs must be 0 or 1 to represent off or on.\n"
            else:
                games_curs.execute("UPDATE ServerSettings SET FlagGoofsGaffs = ? WHERE GuildID = ?", (flaggoofsgaffs, interaction.guild.id))
                changedSettings+=f"Goofs and gaffs flag updated to {flaggoofsgaffs}\n"
        if flagachievements is not None:
            if flagachievements not in [0, 1]:
                errorString+=f"Flag achievements must be 0 or 1 to represent off or on.\n"
            else:
                games_curs.execute("UPDATE ServerSettings SET FlagAchievements = ? WHERE GuildID = ?", (flagachievements, interaction.guild.id))
                changedSettings+=f"Achievements flag updated to {flagachievements}\n"
        games_conn.commit()
        games_curs.close()
        games_conn.close()
        outstr=""
        if changedSettings!="":
            outstr+=f"Changes:\n{changedSettings}\n"
        if errorString!="":
            outstr+=f"Errors:\n{errorString}"
        if outstr=="":
            outstr="No changes made."
        await interaction.response.send_message(outstr)

class GoofsSettingsSet(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    @app_commands.command(name="goofs-settings-set",description="Set goofs and gaffs settings")
    @app_commands.describe(flaghorse="1 is on 0 is off")
    @app_commands.describe(horsechance="0-1 decimal")
    @app_commands.describe(flagcat="1 is on 0 is off. requires catbot to work")
    @app_commands.describe(catchance="0-1 decimal")
    @app_commands.describe(flagping="1 is on 0 is off.")
    @app_commands.describe(flagmarathon="1 is on 0 is off.")
    @app_commands.describe(marathonchance="0-1 decimal")
    @app_commands.describe(flagtwitteralt="1 is on 0 is off.")
    @app_commands.describe(twitteraltchance="0-1 decimal")
    async def goofs_settings_command_set(self, interaction: discord.Interaction, flaghorse: int = None, horsechance: float = None, flagcat: int = None, catchance: float = None, flagping: int = None, flagmarathon: int = None, marathonchance: float = None, flagtwitteralt: int = None, twitteraltchance: float = None):
        games_conn=sqlite3.connect("games.db",timeout=10)
        games_curs=games_conn.cursor()
        games_curs.execute('''INSERT INTO CommandLog (GuildID, UserID, CommandName, CommandParameters) VALUES (?, ?, ?, ?)''', (interaction.guild.id, interaction.user.id, "goofs-settings-set", f"'flaghorse': {flaghorse}, 'horsechance': {horsechance}, 'flagcat': {flagcat}, 'catchance': {catchance}, 'flagping': {flagping}, 'flagmarathon': {flagmarathon}, 'marathonchance': {marathonchance}, 'flagtwitteralt': {flagtwitteralt}, 'twitteraltchance': {twitteraltchance}"))
        games_conn.commit()
        games_curs.close()
        games_conn.close()
        if not await isAuthorized(str(interaction.user.id), str(interaction.guild.id), self.client):
            await interaction.response.send_message("You are not authorized to use this command.")
            return

        games_conn=sqlite3.connect("games.db",timeout=10)
        games_curs=games_conn.cursor()
        changedSettings=""
        errorString=""
        if flaghorse is not None:
            if flaghorse not in [0, 1]:
                errorString+=f"Flag horse must be 0 or 1 to represent off or on.\n"
            else:
                games_curs.execute("UPDATE GoofsGaffs SET FlagHorse = ? WHERE GuildID = ?", (flaghorse, interaction.guild.id))
                changedSettings+=f"Horse flag updated to {flaghorse}\n"
        if horsechance is not None:
            if horsechance <= 0:
                errorString+=f"Horse chance must be above 0.\n"
            else:
                games_curs.execute("UPDATE GoofsGaffs SET HorseChance = ? WHERE GuildID = ?", (horsechance, interaction.guild.id))
                changedSettings+=f"Horse chance updated to {horsechance}\n"
        if flagcat is not None:
            if flagcat not in [0, 1]:
                errorString+=f"Flag cat must be 0 or 1 to represent off or on.\n"
            else:
                games_curs.execute("UPDATE GoofsGaffs SET FlagCat = ? WHERE GuildID = ?", (flagcat, interaction.guild.id))
                changedSettings+=f"Cat flag updated to {flagcat}\n"
        if catchance is not None:
            if catchance <= 0:
                errorString+=f"Cat chance must be above 0.\n"
            else:
                games_curs.execute("UPDATE GoofsGaffs SET CatChance = ? WHERE GuildID = ?", (catchance, interaction.guild.id))
                changedSettings+=f"Cat chance updated to {catchance}\n"
        if flagping is not None:
            if flagping not in [0, 1]:
                errorString+=f"Flag ping must be 0 or 1 to represent off or on.\n"
            else:
                games_curs.execute("UPDATE GoofsGaffs SET FlagPing = ? WHERE GuildID = ?", (flagping, interaction.guild.id))
                changedSettings+=f"Ping flag updated to {flagping}\n"
        if flagmarathon is not None:
            if flagmarathon not in [0, 1]:
                errorString+=f"Flag marathon must be 0 or 1 to represent off or on.\n"
            else:
                games_curs.execute("UPDATE GoofsGaffs SET FlagMarathon = ? WHERE GuildID = ?", (flagmarathon, interaction.guild.id))
                changedSettings+=f"Marathon flag updated to {flagmarathon}\n"
        if marathonchance is not None:
            if marathonchance <= 0:
                errorString+=f"Marathon chance must be above 0.\n"
            else:
                games_curs.execute("UPDATE GoofsGaffs SET MarathonChance = ? WHERE GuildID = ?", (marathonchance, interaction.guild.id))
                changedSettings+=f"Marathon chance updated to {marathonchance}\n"
        if flagtwitteralt is not None:
            if flagtwitteralt not in [0, 1]:
                errorString+=f"Flag twitter alt must be 0 or 1 to represent off or on.\n"
            else:
                games_curs.execute("UPDATE GoofsGaffs SET FlagTwitterAlt = ? WHERE GuildID = ?", (flagtwitteralt, interaction.guild.id))
                changedSettings+=f"Twitter alt flag updated to {flagtwitteralt}\n"
        if twitteraltchance is not None:
            if twitteraltchance <= 0:
                errorString+=f"Twitter alt chance must be above 0.\n"
            else:
                games_curs.execute("UPDATE GoofsGaffs SET TwitterAltChance = ? WHERE GuildID = ?", (twitteraltchance, interaction.guild.id))
                changedSettings+=f"Twitter alt chance updated to {twitteraltchance}\n"
        games_conn.commit()
        games_curs.close()
        games_conn.close()
        outstr=""
        if changedSettings!="":
            outstr+=f"Changes:\n{changedSettings}\n"
        if errorString!="":
            outstr+=f"Errors:\n{errorString}"
        if outstr=="":
            outstr="No changes made."
        await interaction.response.send_message(outstr)

#~~~~~~~~~~~~~~~~~~~~~AUCTION SETUP FUNCTION~~~~~~~~~~~~~~~~~~~~~#

class AuctionHouse(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    @app_commands.command(name="auction-house", description="PVP gambling")
    async def auction_house(self, interaction: discord.Interaction):
        await auction_house_command(interaction)


class RankedLobby(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    @app_commands.command(name="ranked-lobby", description="PVP gambling")
    @app_commands.choices(duration=[
        app_commands.Choice(name="long", value=60),
        app_commands.Choice(name="normal", value=30)
    ])
    async def ranked_lobby(self, interaction: discord.Interaction, duration: app_commands.Choice[int]=None):
        games_conn=sqlite3.connect("games.db",timeout=10)
        games_conn.row_factory = sqlite3.Row
        games_curs = games_conn.cursor()
        games_curs.execute('''SELECT RankedDiceTokens FROM GamblingUserStats WHERE GuildID = ? AND UserID = ?''', (interaction.guild.id, interaction.user.id))
        row = games_curs.fetchone()
        if row is None or row['RankedDiceTokens'] < 1:
            await interaction.response.send_message("You do not have enough Ranked Dice Tokens to start a ranked lobby. You can earn Ranked Dice Tokens once a day automatically, or by answering a trivia question correctly.", ephemeral=True)
            games_curs.close()
            games_conn.close()
            return
        await interaction.response.send_message("Initializing Lobby...")
        msg = await interaction.original_response()
        games_curs.execute('''INSERT INTO CommandLog (GuildID, UserID, CommandName) VALUES (?, ?, ?)''', (interaction.guild.id, interaction.user.id, "ranked-lobby"))
        games_conn.commit()
        games_curs.execute('''select GameState, ChannelID, MessageID from LiveRankedDiceMatches where GuildID = ? and (GameState = 0 or GameState = 1 or GameState = 2)''', (interaction.guild.id,))
        row = games_curs.fetchone()
        if row is not None:
            #edit msg to say a ranked match lobby is already active and where it is instead of sending a followup
            message_link = f"https://discord.com/channels/{interaction.guild.id}/{row['ChannelID']}/{row['MessageID']}"
            await msg.edit(content=f"A ranked match lobby is already active in this server located at {message_link}")
            await delete_later(message=msg,time=10)
            games_curs.close()
            games_conn.close()
            return
        games_curs.execute('''SELECT Season FROM RankedDiceGlobals WHERE Name = "Global"''')
        season= games_curs.fetchone()
        games_curs.execute('''INSERT INTO LiveRankedDiceMatches (GuildID, ChannelID, MessageID, Season) VALUES (?, ?, ?, ?)''', (interaction.guild.id, msg.channel.id, msg.id, season['Season']))
        games_conn.commit()
        games_curs.execute('''SELECT * FROM LiveRankedDiceMatches WHERE GuildID = ? AND ChannelID = ? AND MessageID = ?''', (interaction.guild.id, msg.channel.id, msg.id))
        myMatch= games_curs.fetchone()
        await asyncio.sleep(1)
        games_curs.execute('''SELECT * FROM LiveRankedDiceMatches WHERE GuildID = ? and (GameState = 0 or GameState = 1 or GameState = 2) order by TimeInitiated asc limit 1''', (interaction.guild.id,))
        topMatch= games_curs.fetchone()
        if myMatch['ID'] != topMatch['ID']:
            message_link = f"https://discord.com/channels/{interaction.guild.id}/{topMatch['ChannelID']}/{topMatch['MessageID']}"
            await msg.edit(content=f"A ranked match lobby is already active in this server located at {message_link}")
            await delete_later(message=msg,time=10)
            #delete the row i just created since another match is already active
            games_curs.execute('''DELETE FROM LiveRankedDiceMatches WHERE ID = ?''', (myMatch['ID'],))
            games_conn.commit()
            games_curs.close()
            games_conn.close()
            return
        view = discord.ui.View()
        view.add_item(JoinLobbyButton(match_id=myMatch['ID']))
        end_ts = int(time.time()) + 30   # 30 seconds from now
        countdown_tag = f"<t:{end_ts}:R>"
        await msg.edit(content=f"Lobby initialized.", view=view)
        await asyncio.sleep(.5)
        games_curs.execute('''UPDATE LiveRankedDiceMatches SET GameState = 1 WHERE ID = ?''', (myMatch['ID'],))
        games_conn.commit()
        #await asyncio.sleep(30)
        # RIGHT BEFORE "return"
        if duration is None:
            duration = 30
        else:
            duration = duration.value
        self.client.loop.create_task(lobby_countdown_task(
        interaction=interaction,
        match_id=myMatch["ID"],
        message=msg,
        guild_id=interaction.guild.id,
        duration=duration
        ))

        return

class JoinLobbyButton(discord.ui.Button):
    def __init__(self, match_id: int):
        super().__init__(label="Join Ranked Lobby", style=discord.ButtonStyle.primary)
        self.match_id = match_id

    async def callback(self, interaction: discord.Interaction):
        if await ButtonLockout(interaction):
            view = discord.ui.View()
            games_conn=sqlite3.connect("games.db",timeout=10)
            games_conn.row_factory = sqlite3.Row
            games_curs = games_conn.cursor()
            games_curs.execute('''SELECT Season from RankedDiceGlobals WHERE Name = "Global"''')
            season = games_curs.fetchone()
            if season['Season'] == 0:
                view.add_item(ModifierSelectMenu(match_id=self.match_id))
            else:
                view.add_item(ModifierSelectMenuS1(match_id=self.match_id))
            await interaction.response.send_message("Select your lobby modifier!", ephemeral=True, view=view)
            return

class ModifierSelectMenu(discord.ui.Select):
    def __init__(self,  match_id: int):
        self.match_id = match_id
        options = [
            discord.SelectOption(label="♠️Call a spade a spade♠️", description="Roll 1 D20 and add 5 to the final value", value="spade"),
            discord.SelectOption(label="♦️Diamond in the rough♦️", description="Roll 2 D20 and take the higher result", value="diamond"),
            discord.SelectOption(label="♣️Math club♣️", description="Roll 2 D20, average them out, and add 5 to the total", value="club"),
            discord.SelectOption(label="♥️Heart of the cards♥️", description="Roll 1 D20. (Grants enhanced results when calculating MMR and rank changes)", value="heart"),
            #discord.SelectOption(label="🃏Jokers wild🃏", description="Roll 3 D20, average 2 lowest, add between 3-8. Has dramatically increased mmr gains and losses", value="joker"),
            
        ]
        super().__init__(placeholder="Choose a modifier...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        for child in self.view.children:
            child.disabled = True
        games_conn=sqlite3.connect("games.db",timeout=10)
        games_conn.row_factory = sqlite3.Row
        games_curs = games_conn.cursor()
        games_curs.execute('''SELECT GameState from LiveRankedDiceMatches WHERE ID = ?''', (self.match_id,))
        game_state = games_curs.fetchone()
        if game_state:
            if game_state['GameState'] != 1:
                await interaction.response.edit_message(content=f"Cannot join lobby. ",view=None)
                #await interaction.response.send_message(f"Lobby is already closed.", ephemeral=True)
                games_curs.close()
                games_conn.close()
                return
        else:
            await interaction.response.send_message("No game found with that ID.", ephemeral=True)
        games_curs.execute('''SELECT * FROM PlayerSkill WHERE UserID = ? and GuildID = ?''', (interaction.user.id, interaction.guild.id))
        player_skills = games_curs.fetchone()
        if not player_skills:
            games_curs.execute('''INSERT INTO PlayerSkill (UserID, GuildID) VALUES (?, ?)''', (interaction.user.id, interaction.guild.id))
            games_conn.commit()
            games_curs.execute('''SELECT * FROM PlayerSkill WHERE UserID = ? and GuildID = ?''', (interaction.user.id, interaction.guild.id))
            player_skills = games_curs.fetchone()
        games_curs.execute('''INSERT INTO LiveRankedDicePlayers (MatchID, UserID, Modifier, StartingSkillMu, StartingSkillSigma, StartingRank) VALUES (?, ?, ?, ?, ?, ?)''', (self.match_id, interaction.user.id, self.values[0], player_skills['Mu'], player_skills['Sigma'], player_skills['Rank']))
        games_conn.commit()
        games_curs.close()
        games_conn.close()
        await interaction.response.edit_message(content=f"You have joined the lobby and selected {self.values[0]}!",view=self.view)

class jokeButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Rig match (Admin only)", style=discord.ButtonStyle.red)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("Not for you.", ephemeral=True)
        return

async def lobby_countdown_task(interaction, match_id, message, guild_id, duration=30):
    start_time = time.time()
    timeout = duration  # seconds

    while True:
        elapsed = time.time() - start_time
        if elapsed >= timeout:
            break  # stop updating

        # Pull player list
        games_conn = sqlite3.connect("games.db")
        games_conn.row_factory = sqlite3.Row
        games_curs = games_conn.cursor()

        games_curs.execute('''SELECT UserID, Modifier FROM LiveRankedDicePlayers WHERE MatchID = ?''',(match_id,))
        players = games_curs.fetchall()

        

        try:
        # Format lobby text
            names = []
            isOwnerInLobby = False
            for p in players:
                user = message.guild.get_member(int(p["UserID"]))
                if user:
                    if int(p['UserID']) == 100344687029665792:
                        isOwnerInLobby = True
                    games_curs.execute('''SELECT Rank, ProvisionalGames FROM PlayerSkill WHERE GuildID = ? AND UserID = ?''',(guild_id, p['UserID']))
                    player_skill = games_curs.fetchone()
                    if player_skill['ProvisionalGames'] > 0:
                        names.append(f"• {user.display_name}")# — `{p['Modifier']}`
                    else:
                        rankStr= await rank_number_to_rank_name(player_skill['Rank'])
                        names.append(f"• {user.display_name} (Rank: {rankStr})")# — `{p['Modifier']}`

            player_block = "\n".join(names) if names else "*No players yet*"
            view = discord.ui.View()
            view.add_item(JoinLobbyButton(match_id=match_id))
            games_curs.execute('''SELECT RiggedJoke from RankedDiceGlobals WHERE Name = "Global"''')
            riggedJokeRow = games_curs.fetchone()
            riggedJoke = riggedJokeRow['RiggedJoke']
            if isOwnerInLobby and riggedJoke==1:
                view.add_item(jokeButton())
            remaining = int(timeout - elapsed)
            timestamp = f"<t:{int(time.time()) + remaining}:R>"
            await message.edit(content=f"**Ranked Lobby**\nPlayers:\n{player_block}\n\nLobby closes {timestamp}", view=view)

            await asyncio.sleep(2)  # update every 2 seconds
        except Exception as e:
            print(f"Error updating lobby message: {e}")
            #set gamestate to -1
            games_curs.execute('''UPDATE LiveRankedDiceMatches SET GameState = -1 WHERE ID = ?''',(match_id,))
            games_conn.commit()
            games_curs.close()
            games_conn.close()
            return


    games_curs.execute('''UPDATE LiveRankedDiceMatches SET GameState = 2 WHERE ID = ?''',(match_id,))
    games_conn.commit()
    

    await message.edit(content="⏳ Lobby closed! Rolling soon…", view=None)
    await asyncio.sleep(2)

#~~~~~~~~~~~~~~~~~~~~~~LOBBY CLOSED START ROLLING~~~~~~~~~~~~~~~~~~~~~#

#~~~~~~~~~~~~~~~~~~~~~~NAME SETUP~~~~~~~~~~~~~~~~~~~~~#

    games_curs.execute('''SELECT UserID, Modifier FROM LiveRankedDicePlayers WHERE MatchID = ? order by random()''', (match_id,))
    players = games_curs.fetchall()
    entries = []
    rolls = {}
    for p in players:
        roll = await user_rolls(p['Modifier'])
        rolls[p['UserID']] = roll
        games_curs.execute('''UPDATE LiveRankedDicePlayers SET RollResult = ? WHERE MatchID = ? AND UserID = ?''', (roll, match_id, p['UserID']))
        games_conn.commit()
    for p in players:
        user = message.guild.get_member(int(p["UserID"]))
        if user:
            entries.append(f"• {user.display_name} —")#— `{p['Modifier']}` 

    player_block = "\n".join(entries) if entries else "*No players yet*"
    await message.edit(content=f"**Ranked Match Players**\n{player_block}\n\nRolling now…",)
    await asyncio.sleep(1)
    print("a")
    #check to see if the lobby is empty
    games_curs.execute('''SELECT COUNT(*) as PlayerCount FROM LiveRankedDicePlayers WHERE MatchID = ?''', (match_id,))
    row = games_curs.fetchone()
    if row['PlayerCount'] == 0 or row['PlayerCount'] == 1:
        await message.edit(content="Not enough entrants in lobby. Cancelling match...")
        await delete_later(message=message,time=10)
        games_curs.execute('''DELETE FROM LiveRankedDiceMatches WHERE ID = ?''', (match_id,))
        games_conn.commit()
        games_curs.execute('''DELETE FROM LiveRankedDicePlayers WHERE MatchID = ?''', (match_id,))
        games_conn.commit()
        games_curs.close()
        games_conn.close()
        return
#~~~~~~~~~~~~~~~~~~~~~~~~~~~REVEAL ROLLS ONE AT A TIME~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    for i, p in enumerate(players):
        await asyncio.sleep(1)
        user = message.guild.get_member(int(p["UserID"]))
        if not user:
            continue
        roll = rolls.get(p['UserID'])
        entries[i] = f"• {user.display_name} — **{roll}**"#— `{p['Modifier']}` 
        updated_player_block = "\n".join(entries)
        await message.edit(content=f"**Ranked Match Players**\n{updated_player_block}\n\nRolling now…")
    await asyncio.sleep(3)
    print("b")
    
    #Take the token
    print("c")
    games_curs.execute('''UPDATE GamblingUserStats SET RankedDiceTokens = RankedDiceTokens - 1 WHERE UserID = ? AND GuildID = ?''', (interaction.user.id, guild_id))
    games_conn.commit()
    #order the players by their roll result descending
    games_curs.execute('''SELECT UserID, Modifier, RollResult FROM LiveRankedDicePlayers WHERE MatchID = ? ORDER BY RollResult DESC''', (match_id,))
    ordered_players = games_curs.fetchall()
    print("d")
    currentPlacement=1
    lastRoll=None
    placementDict={}
    for p in ordered_players:
        if lastRoll is None:
            placementDict[p['UserID']] = currentPlacement
            lastRoll = p['RollResult']
        else:
            if p['RollResult'] == lastRoll:
                placementDict[p['UserID']] = currentPlacement
            else:
                currentPlacement += 1
                placementDict[p['UserID']] = currentPlacement
                lastRoll = p['RollResult']
        games_curs.execute('''UPDATE LiveRankedDicePlayers SET FinalPosition = ? WHERE MatchID = ? AND UserID = ?''', (placementDict[p['UserID']], match_id, p['UserID']))
        games_conn.commit()
    games_curs.execute('''SELECT ID, UserID, Modifier, FinalPosition, StartingSkillMu as Mu, StartingSkillSigma as Sigma, StartingRank as Rank FROM LiveRankedDicePlayers WHERE MatchID = ? ORDER BY FinalPosition ASC''', (match_id,))
    final_players = games_curs.fetchall()
    print("e")
    #~~~~~~~~~~~~~~~~~~~~~~TRUESKILL CALCULATION~~~~~~~~~~~~~~~~~~~~~#
    games_curs.execute('''SELECT * FROM RankedDiceGlobals''')
    ranked_globals = games_curs.fetchone()
    result_entries = [dict(row) for row in final_players]
    ts_env = trueskill.TrueSkill(mu=ranked_globals['Mu'], sigma=ranked_globals['Sigma'], beta=ranked_globals['Beta'], tau=ranked_globals['Tau'])
    ratings = [ts_env.Rating(mu=player['Mu'], sigma=player['Sigma']) for player in result_entries]
    teams = [[rating] for rating in ratings]
    ranks = [player['FinalPosition']-1 for player in result_entries]
    print("f")
    try:
        new_ratings = trueskill.rate(rating_groups=teams, ranks=ranks)
    except Exception as e:
        print(f"Error initializing TrueSkill environment: {e}")
        await message.edit(content="An error occurred while calculating rankings. Please try again later.")
        #change the gamestate to -1
        games_curs.execute('''UPDATE LiveRankedDiceMatches SET GameState = -1 WHERE ID = ?''', (match_id,))
        games_conn.commit()
        games_curs.close()
        games_conn.close()
        return
    print("g")
    for i, player in enumerate(result_entries):
        player['EndSkillMu'] = new_ratings[i][0].mu
        player['EndSkillSigma'] = new_ratings[i][0].sigma
    for player in result_entries:
        games_curs.execute('''SELECT ProvisionalGames FROM PlayerSkill WHERE UserID = ? AND GuildID = ?''', (player['UserID'], guild_id))
        row = games_curs.fetchone()
        provisional_games_left = row['ProvisionalGames'] if row else 0
        targetRank= mu_to_target_rank(player['EndSkillMu'])
        if provisional_games_left > 0:
            # If there are provisional games left, use the target rank
            targetRank = targetRank if targetRank < 25 else 25
            #player['EndSkillMu'] = player['EndSkillMu'] if player['EndSkillMu'] < 30 else 30
            newRank= targetRank
        else:
            # If no provisional games left, use the end rank
            newRank= update_visible_rank(player['Rank'], targetRank)
        winCount=0
        lossCount=0
        print("h")
        muDiff= player['EndSkillMu'] - player['Mu']
        if player['Modifier'] == 'heart':
            if muDiff > 0:
                muDiff *= 1+float(ranked_globals['HeartBoostWin'])  # Increase MMR gain by 25%
            else:
                muDiff *= 1-float(ranked_globals['HeartBoostLose'])  # Decrease MMR loss by 25%
            player['EndSkillMu'] = player['Mu'] + muDiff
        elif player['Modifier'] == 'joker':
            if muDiff > 0:
                muDiff *= 1+float(ranked_globals['JokerBoostWin'])  # Increase MMR gain by 50%
            else:
                muDiff *= 1-float(ranked_globals['JokerBoostLose'])  # Decrease MMR loss by 50%
            player['EndSkillMu'] = player['Mu'] + muDiff
        print("i")
        if player['Rank'] < 20:
            if muDiff > 0:
                muDiff *= 1+float(ranked_globals['SubDiamondBoostWin'])  # Increase MMR gain by 5%
            else:
                muDiff *= 1-float(ranked_globals['SubDiamondBoostLose'])  # Decrease MMR loss by 5%
            player['EndSkillMu'] = player['Mu'] + muDiff
        print("j")
        if muDiff > 0:
            winCount=1
            rankDiff= newRank - player['Rank']
            if rankDiff < 0:
                newRank= player['Rank']
        else:
            lossCount=1
            rankDiff= newRank - player['Rank']
            if rankDiff > 0:
                newRank= player['Rank']
        if player['EndSkillMu'] > 41:
            player['EndSkillMu'] = 41
        try:
            games_curs.execute('''UPDATE PlayerSkill SET Mu = ?, Sigma = max(?, 4), Rank = ?, ProvisionalGames = max(0, ProvisionalGames - 1), GamesPlayed = GamesPlayed + 1, WinCount = WinCount + ?, LossCount = LossCount + ?, SeasonalGamesPlayed = SeasonalGamesPlayed + 1, SeasonalWinCount = SeasonalWinCount + ?, SeasonalLossCount = SeasonalLossCount + ?, LastPlayed = ? WHERE UserID = ? AND GuildID = ?''', (player['EndSkillMu'], player['EndSkillSigma'], newRank, winCount, lossCount, winCount, lossCount, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), player['UserID'], guild_id))
            games_conn.commit()
            games_curs.execute('''SELECT Modifier, RollResult, StartingRank FROM LiveRankedDicePlayers WHERE MatchID = ? AND UserID = ?''', (match_id, player['UserID']))
            player_data = games_curs.fetchone()
            await achievementTrigger(guildID=guild_id, userID=player['UserID'], eventType="GamesPlayed")
            await achievementTrigger(guildID=guild_id, userID=player['UserID'], eventType="SeasonalGamesPlayed")
            if winCount == 1:
                await achievementTrigger(guildID=guild_id, userID=player['UserID'], eventType="WinCount")
                await achievementTrigger(guildID=guild_id, userID=player['UserID'], eventType="SeasonalWinCount")
                await achievementTrigger(guildID=guild_id, userID=player['UserID'], eventType="FirstPlaceFinishes1v1")
                await achievementTrigger(guildID=guild_id, userID=player['UserID'], eventType="FirstPlaceFinishesLargeLobby")
                if player_data['Modifier'] == 'heart':
                    await achievementTrigger(guildID=guild_id, userID=player['UserID'], eventType="WinsHeart")
                    if player_data['RollResult'] == 20:
                        await achievementTrigger(guildID=guild_id, userID=player['UserID'], eventType="PerfectRollHeart")
                    elif player_data['RollResult'] == 1:
                        await achievementTrigger(guildID=guild_id, userID=player['UserID'], eventType="MinRollHeart")
                elif player_data['Modifier'] == 'spade':
                    await achievementTrigger(guildID=guild_id, userID=player['UserID'], eventType="WinsSpade")
                    if player_data['RollResult'] == 25:
                        await achievementTrigger(guildID=guild_id, userID=player['UserID'], eventType="PerfectRollSpade")
                    elif player_data['RollResult'] == 6:
                        await achievementTrigger(guildID=guild_id, userID=player['UserID'], eventType="MinRollSpade")
                elif player_data['Modifier'] == 'diamond':
                    await achievementTrigger(guildID=guild_id, userID=player['UserID'], eventType="WinsDiamond")
                    if player_data['RollResult'] == 20:
                        await achievementTrigger(guildID=guild_id, userID=player['UserID'], eventType="PerfectRollDiamond")
                    elif player_data['RollResult'] == 1:
                        await achievementTrigger(guildID=guild_id, userID=player['UserID'], eventType="MinRollDiamond")
                elif player_data['Modifier'] == 'club':
                    await achievementTrigger(guildID=guild_id, userID=player['UserID'], eventType="WinsClub")
                    if player_data['RollResult'] == 25:
                        await achievementTrigger(guildID=guild_id, userID=player['UserID'], eventType="PerfectRollClub")
                    elif player_data['RollResult'] == 6:
                        await achievementTrigger(guildID=guild_id, userID=player['UserID'], eventType="MinRollClub")
                if player_data['StartingRank'] > 40:
                    await achievementTrigger(guildID=guild_id, userID=player['UserID'], eventType="D20Wins")
                    if player_data['Modifier'] == 'heart':
                        await achievementTrigger(guildID=guild_id, userID=player['UserID'], eventType="D20HeartWins")
                    elif player_data['Modifier'] == 'spade':
                        await achievementTrigger(guildID=guild_id, userID=player['UserID'], eventType="D20SpadeWins")
                    elif player_data['Modifier'] == 'diamond':
                        await achievementTrigger(guildID=guild_id, userID=player['UserID'], eventType="D20DiamondWins")
                    elif player_data['Modifier'] == 'club':
                        await achievementTrigger(guildID=guild_id, userID=player['UserID'], eventType="D20ClubWins")
            if lossCount == 1:
                await achievementTrigger(guildID=guild_id, userID=player['UserID'], eventType="LossCount")
                await achievementTrigger(guildID=guild_id, userID=player['UserID'], eventType="SeasonalLossCount")
        except Exception as e:
            print(f"Error updating PlayerSkill for UserID {player['UserID']}: {e}")
            await message.edit(content="An error occurred while updating player skills. Please try again later.")
            #change the gamestate to -1
            games_curs.execute('''UPDATE LiveRankedDiceMatches SET GameState = -1 WHERE ID = ?''', (match_id,))
            games_conn.commit()
            games_curs.close()
            games_conn.close()
            return
        print("k")
        games_curs.execute('''UPDATE LiveRankedDicePlayers SET EndSkillMu = ?, EndSkillSigma = max(?, 3), EndRank = ? WHERE MatchID = ? AND UserID = ?''', (player['EndSkillMu'], player['EndSkillSigma'], newRank, match_id, player['UserID']))
        games_conn.commit()
        #edit the message to show the final results with MMR and rank changes
    print("Final Results:")
    try:
        games_curs.execute('''SELECT UserID, FinalPosition, StartingSkillMu, EndSkillMu, StartingRank, EndRank, RollResult FROM LiveRankedDicePlayers WHERE MatchID = ? ORDER BY FinalPosition ASC''', (match_id,))
        final_players_2 = games_curs.fetchall()
        result_entries_2 = [dict(row) for row in final_players_2]
        result_lines = []
        print(f"result_entries: {result_entries_2}")
    
        for player in result_entries_2:
            user = message.guild.get_member(int(player["UserID"]))
            if user:
                mmr_change = player['EndSkillMu'] - player['StartingSkillMu']
                rank_change = player['EndRank'] - player['StartingRank']
                mmr_change_str = f"{mmr_change:+.2f}"
                rank_change_str = f"{rank_change:+.2f}"
                oldRankName = await rank_number_to_rank_name(player['StartingRank'])
                newRankName = await rank_number_to_rank_name(player['EndRank'])
                games_curs.execute('''SELECT ProvisionalGames FROM PlayerSkill WHERE UserID = ? AND GuildID = ?''', (player['UserID'], guild_id))
                row = games_curs.fetchone()
                provisional_games_left = row['ProvisionalGames'] if row else 0
                if provisional_games_left > 0:
                    rank_change_str = f"Provisional Games {10-provisional_games_left}/10 completed"
                    result_lines.append(f"• {user.display_name} — Roll: {player['RollResult']} Position: **{player['FinalPosition']}** — Rank: ({rank_change_str})")
                else:
                    result_lines.append(f"• {user.display_name} — Roll: {player['RollResult']} — Position: **{player['FinalPosition']}** — Rank: {oldRankName} → {newRankName} ({rank_change_str})")
    except Exception as e:
        print(f"Error generating final results: {e}")
        await message.edit(content="An error occurred while generating final results. Please try again later.")
        #change the gamestate to -1
        games_curs.execute('''UPDATE LiveRankedDiceMatches SET GameState = -1 WHERE ID = ?''', (match_id,))
        games_conn.commit()
        games_curs.close()
        games_conn.close()
        return
    print("sas")
    final_result_block = "\n".join(result_lines)
    await message.edit(content=f"**Ranked Match Results**\n{final_result_block}",)
    print("done")
    games_curs.execute('''UPDATE LiveRankedDiceMatches SET GameState = 3 WHERE ID = ?''', (match_id,))
    games_conn.commit()
    await delete_later(message=message,time=30)
    games_curs.close()
    games_conn.close()



def mu_to_target_rank(mu):
    # Example: scale MMR into your 1–60 rank system (20 bronze→plat + 40 diamond)
    # Adjust min/max as needed
    min_mu = 15
    max_mu = 41  # pick appropriate scaling
    max_rank = 41
    min_rank = 1
    # linear scaling
    rank = (mu - min_mu) / (max_mu - min_mu) * (max_rank - min_rank) + min_rank
    return max(min(rank, max_rank), min_rank)

def update_visible_rank(current_rank, target_rank, smoothing=0.3):
    """
    Move the shown rank fractionally toward the target.
    smoothing=0.3 → moves 30% of the gap each update
    """
    return current_rank + (target_rank - current_rank) * smoothing



async def user_rolls(modifier:str):
    games_conn=sqlite3.connect("games.db",timeout=10)
    games_conn.row_factory = sqlite3.Row
    games_curs = games_conn.cursor()
    games_curs.execute('''SELECT Season from RankedDiceGlobals where Name = "Global"''')
    season = games_curs.fetchone()
    roll = random.randint(1, 20)
    if modifier == "spade":
        if season['Season'] == 0:
            roll += 5
        else:
            roll += 4
    elif modifier == "diamond":
        roll2 = random.randint(1, 20)
        roll = max(roll, roll2)
    elif modifier == "club":
        roll2 = random.randint(1, 20)
        if season['Season'] == 0:
            roll = int(((roll + roll2) / 2) + 5)
        else:
            roll = ((roll + roll2) / 2) + 4
    elif modifier == "heart":
        pass  # no change to roll, but may affect MMR later
    elif modifier == "joker":
        roll2 = random.randint(1, 20)
        roll3 = random.randint(1, 20)
        low_rolls = sorted([roll, roll2, roll3])[:2]
        roll = int((low_rolls[0] + low_rolls[1]) / 2)
        roll += random.randint(3, 8)
    return roll


class ModifierSelectMenuS1(discord.ui.Select):
    def __init__(self,  match_id: int):
        self.match_id = match_id
        options = [
            discord.SelectOption(label="♠️Call a spade a spade♠️", description="Roll 1 D20 and add 5 to the final value", value="spade"),
            discord.SelectOption(label="♦️Diamond in the rough♦️", description="Roll 2 D20 and take the higher result", value="diamond"),
            discord.SelectOption(label="♣️Math club♣️", description="Roll 2 D20, average them out, and add 5 to the total", value="club"),
            discord.SelectOption(label="♥️Heart of the cards♥️", description="Roll 1 D20. (Grants enhanced results when calculating MMR and rank changes)", value="heart"),
            discord.SelectOption(label="🃏Jokers wild🃏", description="Roll 3 D20, average 2 lowest, add between 3-8. Has dramatically increased mmr gains and losses", value="joker"),
            
        ]
        super().__init__(placeholder="Choose a modifier...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        for child in self.view.children:
            child.disabled = True
        games_conn=sqlite3.connect("games.db",timeout=10)
        games_conn.row_factory = sqlite3.Row
        games_curs = games_conn.cursor()
        games_curs.execute('''SELECT GameState from LiveRankedDiceMatches WHERE ID = ?''', (self.match_id,))
        game_state = games_curs.fetchone()
        if game_state:
            if game_state['GameState'] != 1:
                await interaction.response.edit_message(content=f"Cannot join lobby. ",view=None)
                #await interaction.response.send_message(f"Lobby is already closed.", ephemeral=True)
                games_curs.close()
                games_conn.close()
                return
        else:
            await interaction.response.send_message("No game found with that ID.", ephemeral=True)
        games_curs.execute('''SELECT * FROM PlayerSkill WHERE UserID = ? and GuildID = ?''', (interaction.user.id, interaction.guild.id))
        player_skills = games_curs.fetchone()
        if not player_skills:
            games_curs.execute('''INSERT INTO PlayerSkill (UserID, GuildID) VALUES (?, ?)''', (interaction.user.id, interaction.guild.id))
            games_conn.commit()
            games_curs.execute('''SELECT * FROM PlayerSkill WHERE UserID = ? and GuildID = ?''', (interaction.user.id, interaction.guild.id))
            player_skills = games_curs.fetchone()
        games_curs.execute('''INSERT INTO LiveRankedDicePlayers (MatchID, UserID, Modifier, StartingSkillMu, StartingSkillSigma, StartingRank) VALUES (?, ?, ?, ?, ?, ?)''', (self.match_id, interaction.user.id, self.values[0], player_skills['Mu'], player_skills['Sigma'], player_skills['Rank']))
        games_conn.commit()
        games_curs.close()
        games_conn.close()
        await interaction.response.edit_message(content=f"You have joined the lobby and selected {self.values[0]}!",view=self.view)


async def setup(client: commands.Bot):
    await client.add_cog(GradeReport(client))
    await client.add_cog(Leaderboard(client))
    await client.add_cog(FlipGame(client))
    await client.add_cog(GameSettingsGet(client))
    await client.add_cog(GameSettingsSet(client))
    await client.add_cog(GoofsSettingsGet(client))
    await client.add_cog(GoofsSettingsSet(client))
    await client.add_cog(AuctionHouse(client))
    await client.add_cog(RankedLobby(client))