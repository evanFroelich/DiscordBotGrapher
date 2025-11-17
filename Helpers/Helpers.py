import discord
import sqlite3
import asyncio
import numpy as np
import random
from datetime import datetime
import json

async def ButtonLockout(interaction: discord.Interaction):
    gamesDB = "games.db"
    games_conn = sqlite3.connect(gamesDB)
    games_curs = games_conn.cursor()
    games_curs.execute('''select * from ActiveQuestions where messageID=? and RespondedUserID=?''', (interaction.message.id, interaction.user.id))
    active_question = games_curs.fetchone()
    #print(f"active question: {active_question}")
    if active_question:
        # If the question is already active, do not open a new modal
        await interaction.response.send_message("You already interacted with this message.", ephemeral=True)
        games_curs.close()
        games_conn.close()
        return False
    # When the button is clicked, open a modal for the question
    games_curs.execute('''INSERT INTO ActiveQuestions (messageID, RespondedUserID) VALUES (?, ?)''', (interaction.message.id, interaction.user.id))
    games_conn.commit()
    games_curs.close()
    games_conn.close()
    return True

async def award_points(amount, guild_id, user_id):
    gamesDB = "games.db"
    games_conn = sqlite3.connect(gamesDB)
    games_curs = games_conn.cursor()
    lifeAmount = amount
    if amount < 0:
        lifeAmount = 0
    games_curs.execute('''INSERT INTO GamblingUserStats (GuildID, UserID, CurrentBalance, LifetimeEarnings) VALUES (?, ?, ?, ?) ON CONFLICT (GuildID, UserID) DO UPDATE SET CurrentBalance = CurrentBalance + ?, LifetimeEarnings = LifetimeEarnings + ?;''', (guild_id, user_id, amount, lifeAmount, amount, lifeAmount))
    games_conn.commit()
    games_curs.close()
    games_conn.close()

async def delete_later(message,time):
    await asyncio.sleep(time)  # wait for the specified time
    try:
        await message.delete()
        gamesDB = "games.db"
        games_conn = sqlite3.connect(gamesDB)
        games_curs = games_conn.cursor()
        games_curs.execute('''DELETE FROM ActiveQuestions WHERE messageID=?''', (message.id,))
        games_conn.commit()
        games_curs.close()
        games_conn.close()
    except Exception:
        pass  # message might already be gone

async def createTimers(GuildID):
    gameDB = "games.db"
    games_conn = sqlite3.connect(gameDB)
    games_curs = games_conn.cursor()
    # Create a table to store timers if it doesn't exist
    games_curs.execute('''INSERT OR IGNORE INTO FeatureTimers(GuildID) VALUES (?)''', (GuildID,))
    games_conn.commit()
    games_conn.close()

def sigmoid(x):
    return 1 / (1 + np.exp(-x))

async def smrtGame(message):
    #await createTimers(message.guild.id)
    gamesDB = "games.db"
    games_conn = sqlite3.connect(gamesDB)
    games_curs = games_conn.cursor()
    #get the current time in utc
    curTime = datetime.now()
    delta = 0
    #get the time from the FeatureTimers table
    games_curs.execute('''SELECT LastBonusPipTime FROM FeatureTimers WHERE GuildID=?''', (message.guild.id,))
    lastPipTime = games_curs.fetchone()
    if lastPipTime:
        LQT=datetime.strptime(lastPipTime[0], "%Y-%m-%d %H:%M:%S")
        curTime=curTime.replace(microsecond=0)
        #print("last bonus pip time: "+str(LQT))
        #print("current time: "+str(curTime))
        delta = LQT - curTime
        #convert delta to seconds
        delta = delta.total_seconds()
        delta= abs(delta)
        #print("delta: "+str(delta))
    x=.05*(delta-120)
    multiplier=sigmoid(x)
    r=random.random()
    games_curs.execute('''SELECT PipChance FROM ServerSettings WHERE GuildID=?''', (message.guild.id,))
    row = games_curs.fetchone()
    if row:
        pipChance = row[0]
    if r < pipChance * multiplier:
        await message.add_reaction('✅')
        # Update the last bonus pip time in the database
        games_curs.execute('''UPDATE FeatureTimers SET LastBonusPipTime=?, LastBonusPipMessage=? WHERE GuildID=?''', (curTime, message.id, message.guild.id))
        games_conn.commit()
    games_curs.close()
    games_conn.close()
    return

async def checkIgnoredChannels(channelID: str, guildID: str) -> bool:
    channelID_str = str(channelID)
    gameDB = "games.db"
    games_conn = sqlite3.connect(gameDB)
    games_curs = games_conn.cursor()
    games_curs.execute('''SELECT IgnoredChannels FROM ServerSettings WHERE GuildID=?''', (guildID,))
    ignoredchannels = games_curs.fetchone()
    channelList = []
    if ignoredchannels is not None and ignoredchannels[0] is not None:
        channelList=json.loads(ignoredchannels[0])
    games_conn.close()

    if channelID_str in channelList:
        return True
    return False

async def numToGrade(percentage):
    """Converts a percentage to a letter grade."""
    if percentage >= 90:
        return "A"
    elif percentage >= 80:
        return "B"
    elif percentage >= 70:
        return "C"
    elif percentage >= 60:
        return "D"
    else:
        return "F"
    
async def create_user_db_entry(guildID, userID):
    gamesDB = "games.db"
    games_conn = sqlite3.connect(gamesDB)
    games_curs = games_conn.cursor()
    #check to see if the user has an entry in the GamblingUserStats table
    games_curs.execute('''SELECT * FROM GamblingUserStats WHERE GuildID=? AND UserID=?''', (guildID, userID))
    user_stats = games_curs.fetchone()
    if not user_stats:
        # If no entry exists, create one
        games_curs.execute('''INSERT INTO GamblingUserStats (GuildID, UserID) VALUES (?, ?)''', (guildID, userID))
        games_conn.commit()
    games_curs.close()
    games_conn.close()
    #print(f"User entry created or verified for GuildID: {guildID}, UserID: {userID}")

async def create_guild_db_entry(guildID):
    db_name="My_DB"
    conn = sqlite3.connect(db_name)
    curs = conn.cursor()
    curs.execute('''INSERT OR IGNORE INTO ServerSettings (GuildID) VALUES (?);''',(guildID,))
    conn.commit()
    curs.close()
    conn.close()

    gamesDB = "games.db"
    games_conn = sqlite3.connect(gamesDB)
    games_curs = games_conn.cursor()
    games_curs.execute('''INSERT INTO GamblingUnlockConditions (GuildID, Game1Condition1, Game1Condition2, Game1Condition3, Game2Condition1, Game2Condition2, Game2Condition3) values (?, ?, ?, ?, ?, ?, ?)''', (guildID, 500, 15, 3, 2000, 500, 3))
    games_curs.execute('''INSERT INTO ServerSettings (GuildID) VALUES (?)''', (guildID,))
    games_conn.commit()
    games_curs.close()
    games_conn.close()

async def isAuthorized(userID: str, guildID: str, bot=None) -> bool:
    #check if the user has admin privileges in this guild
    guild = bot.get_guild(int(guildID))
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

