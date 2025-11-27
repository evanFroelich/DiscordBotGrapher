import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import asyncio
import random
from datetime import datetime, timedelta
from Helpers.Helpers import create_user_db_entry, numToGrade, delete_later, isAuthorized, achievementTrigger, achievement_leaderboard_generator, auction_house_command


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
        app_commands.Choice(name="achievement-score", value="achievement-score")
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
        privMsg=True if visibility.value=="private" else False
        await interaction.response.defer(thinking=True,ephemeral=privMsg)
        embed=embed=discord.Embed(title="Leaderboard", color=0x228a65)
        #print(f"visibility: {visibility.value} privMsg: {privMsg}")
        if subtype.value == "pip":
            guild_id = str(interaction.guild.id)
            games_curs.execute('''SELECT UserID, SUM(Num_Correct) AS TotalPoints
            FROM Scores WHERE GuildID = ?
            GROUP BY UserID
            ORDER BY TotalPoints DESC''', (guild_id,))
            rows= games_curs.fetchall()
            outstr=""
            embed.title="Bonus Points Leaderboard"
            for row in rows:
                user=interaction.guild.get_member(int(row[0]))
                if user:
                    outstr += f"<@{user.id}>: {row[1]} hits\n"
                else:
                    outstr += f"User ID {row[0]}: {row[1]} hits\n"
            if outstr == "":
                outstr = "no points yet"
            embed.description=outstr
            await interaction.followup.send(embed=embed, ephemeral=privMsg)
        if subtype.value == "flip":
            games_curs.execute('''SELECT UserID, CurrentStreak FROM CoinFlipLeaderboard ORDER BY CurrentStreak DESC, LastFlip DESC''')
            rows= games_curs.fetchall()
            embed=discord.Embed(color=0x228a65)
            outstr=""
            quitQ=0
            participation=0
            embed.title="---Coin Flip Leaderboard---"
            for UserID, CurrentStreak in rows:
                #--TODO: see if i can pre capture the user ids so i only have to go out to discord once instead of every loop
                user=interaction.guild.get_member(int(UserID))
                if user:
                    if participation == 0 and CurrentStreak==1:
                        outstr+=f"---Participation Trophy---\n"
                        participation=1
                    if quitQ==0 and CurrentStreak == 0:
                        outstr+=f"---Quitters---\n"
                        quitQ=1
                    outstr += f"<@{user.id}>: {CurrentStreak}\n"
            embed.description=outstr
            msg=await interaction.followup.send(embed=embed,ephemeral=privMsg)
            asyncio.create_task(delete_later(message=msg,time=60))
        if subtype.value == "balance":
            #get the current balances for the server
            games_curs.execute('''SELECT UserID, CurrentBalance FROM GamblingUserStats WHERE GuildID = ? ORDER BY CurrentBalance DESC''', (interaction.guild.id,))
            rows= games_curs.fetchall()
            outstr=""
            embed=discord.Embed(title="Gambling Balance Leaderboard", color=0x228a65)
            for row in rows:
                user=interaction.guild.get_member(int(row[0]))
                if user:
                    outstr += f"<@{user.id}>: {row[1]} points\n"
                else:
                    outstr += f"User ID {row[0]}: {row[1]} points\n"
            embed.description=outstr
            await interaction.followup.send(embed=embed, ephemeral=privMsg)
        if subtype.value == "achievement-score":
            embed = await achievement_leaderboard_generator(interaction.guild.id)
            await interaction.followup.send(embed=embed, ephemeral=privMsg)
        games_curs.close()
        games_conn.close()




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
    async def gamesettingscommandset(self, interaction: discord.Interaction, numberofquestionsperday: int = None, questiontimeout: int = None, pipchance: float = None, questionchance: float = None, flagshamechannel: int = None, shamechannel: str = None, flagignoredchannels: int = None, ignoredchannels: str = None, flaggoofsgaffs: int = None):
        games_conn=sqlite3.connect("games.db",timeout=10)
        games_curs = games_conn.cursor()
        games_curs.execute('''INSERT INTO CommandLog (GuildID, UserID, CommandName, CommandParameters) VALUES (?, ?, ?, ?)''', (interaction.guild.id, interaction.user.id, "game-settings-set", f"'numberofquestionsperday': {numberofquestionsperday}, 'questiontimeout': {questiontimeout}, 'pipchance': {pipchance}, 'questionchance': {questionchance}, 'flagshamechannel': {flagshamechannel}, 'shamechannel': {shamechannel}, 'flagignoredchannels': {flagignoredchannels}, 'ignoredchannels': {ignoredchannels}, 'flaggoofsgaffs': {flaggoofsgaffs}"))
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






async def setup(client: commands.Bot):
    await client.add_cog(GradeReport(client))
    await client.add_cog(Leaderboard(client))
    await client.add_cog(FlipGame(client))
    await client.add_cog(GameSettingsGet(client))
    await client.add_cog(GameSettingsSet(client))
    await client.add_cog(GoofsSettingsGet(client))
    await client.add_cog(GoofsSettingsSet(client))
    await client.add_cog(AuctionHouse(client))