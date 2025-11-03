"""Message handler for the Discord bot."""
import sqlite3
import discord
import asyncio
import random
import re
from datetime import datetime
from discord.utils import get
from utils.database import checkIgnoredChannels, createTimers
from utils.helpers import sigmoid
from utils.queries import topChat


async def smrtGame(message):
    """Handle smart game (bonus pip) feature."""
    await createTimers(message.guild.id)
    gamesDB = "games.db"
    games_conn = sqlite3.connect(gamesDB)
    games_curs = games_conn.cursor()
    curTime = datetime.now()
    delta = 0
    games_curs.execute('''SELECT LastBonusPipTime FROM FeatureTimers WHERE GuildID=?''', (message.guild.id,))
    lastPipTime = games_curs.fetchone()
    if lastPipTime:
        LQT = datetime.strptime(lastPipTime[0], "%Y-%m-%d %H:%M:%S")
        curTime = curTime.replace(microsecond=0)
        delta = LQT - curTime
        delta = delta.total_seconds()
        delta = abs(delta)
    x = .05*(delta-120)
    multiplier = sigmoid(x)
    r = random.random()
    games_curs.execute('''SELECT PipChance FROM ServerSettings WHERE GuildID=?''', (message.guild.id,))
    row = games_curs.fetchone()
    if row:
        pipChance = row[0]
    if r < pipChance * multiplier:
        await message.add_reaction('✅')
        games_curs.execute('''UPDATE FeatureTimers SET LastBonusPipTime=?, LastBonusPipMessage=? WHERE GuildID=?''', 
                         (curTime, message.id, message.guild.id))
        games_conn.commit()
    games_curs.close()
    games_conn.close()


async def questionSpawner(message):
    """Handle random question spawning."""
    from commands.trivia import createQuestion
    await createTimers(message.guild.id)
    gamesDB = "games.db"
    games_conn = sqlite3.connect(gamesDB)
    games_curs = games_conn.cursor()
    games_curs.execute('''SELECT QuestionChance from ServerSettings WHERE GuildID=?''', (message.guild.id,))
    questionChance = games_curs.fetchone()[0]
    curTime = datetime.now()
    delta = 0
    games_curs.execute('''SELECT LastRandomQuestionTime FROM FeatureTimers WHERE GuildID=?''', (message.guild.id,))
    lastQuestionTime = games_curs.fetchone()
    if lastQuestionTime:
        LQT = datetime.strptime(lastQuestionTime[0], "%Y-%m-%d %H:%M:%S")
        curTime = curTime.replace(microsecond=0)
        delta = LQT - curTime
        delta = delta.total_seconds()
        delta = abs(delta)
    x = .05*(delta-120)
    multiplier = sigmoid(x)
    r = random.random()
    if r < questionChance * multiplier:
        await createQuestion(channel=message.channel, isForced=False)
        games_curs.execute('''UPDATE FeatureTimers SET LastRandomQuestionTime=? WHERE GuildID=?''', 
                         (curTime, message.guild.id))
        games_conn.commit()
    games_curs.close()
    games_conn.close()


async def abandoned_trivia_cleanup(guildID: int, userID: int, messageID: int, questionID: int, questionType: str, questionDifficulty: str, questionText: str):
    """Clean up abandoned trivia sessions."""
    from bot import MyClient
    games_conn = sqlite3.connect('games.db')
    games_curs = games_conn.cursor()
    games_curs.execute('''INSERT INTO Scores (GuildID, UserID, Category, Difficulty, Num_Correct, Num_Incorrect) VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(GuildID, UserID, Category, Difficulty) DO UPDATE SET Num_Incorrect = Num_Incorrect + 1;''', 
                      (guildID, userID, questionType, questionDifficulty, 0, 1))
    games_curs.execute('''UPDATE QuestionList SET GlobalIncorrect = GlobalIncorrect + 1 WHERE ID=?''', (questionID,))
    games_conn.commit()
    games_curs.execute('''SELECT FlagShameChannel, ShameChannel FROM ServerSettings WHERE GuildID=?''', (guildID,))
    shameSettings = games_curs.fetchone()
    if shameSettings and shameSettings[0] == 1:
        # Note: client reference will be passed from the bot instance
        pass  # Will be handled in the actual implementation
    games_curs.execute('''DELETE FROM ActiveTrivia WHERE GuildID=? AND UserID=? AND MessageID=?''', (guildID, userID, messageID))
    games_conn.commit()
    games_curs.close()
    games_conn.close()


async def handle_message(client, message):
    """Main message handler."""
    if message.author == client.user:
        return
    if message.author.bot:
        if message.author.id == 510016054391734273:
            splitstr = message.content.split()
            if "RUINED" in splitstr:
                await asyncio.sleep(5)
                await message.channel.send("https://tenor.com/view/death-stranding-2-sisyphus-on-the-beach-hideo-kojima-mountain-climb-gif-9060768058445058879")
        return
    
    DB_NAME = "My_DB"
    conn = sqlite3.connect(DB_NAME)
    curs = conn.cursor()

    if not await checkIgnoredChannels(message.channel.id, message.guild.id):
        await smrtGame(message)
        await questionSpawner(message)
    
    print(message.guild.name)
    splitstr = message.content.split()
    if len(message.content) > 0:
        if splitstr[0] == 'top3':
            tmp, extra = topChat('users', 'day', 300, str(message.guild.id), 3, '', curs)
            for key in tmp:
                await message.channel.send(tmp[key])
        
        if splitstr[0] == 'enableRankedRoles':
            print('trying')
            try:
                f = open('RankedRoleConfig/config', "r")
                passing = True
                print("here")
                for line in f:
                    print(line)
                    splitLine = line.split()
                    if splitLine[0] == str(message.guild.id):
                        passing = False
                f.close()
                if passing:
                    cfgFile = open('RankedRoleConfig/config', "a")
                    cfgFile.write('\n'+str(message.guild.id)+' true '+splitstr[1]+' '+splitstr[2]+' '+splitstr[3]+' '+splitstr[4])
                    cfgFile.close()
                    await message.channel.send("added to list")
                else:
                    await message.channel.send("already enabled")
            except AssertionError:
                await message.channel.send("invalid param")
        
        if splitstr[0] == 'disableRankedRoles':
            print('not working yet')
            role = get(message.guild.roles, id=1016131254497845280)
            await message.channel.send(len(role.members))
        
        # Goofs and Gaffs handling
        games_path = "games.db"
        games_conn = sqlite3.connect(games_path)
        games_conn.row_factory = sqlite3.Row
        games_curs = games_conn.cursor()
        
        games_curs.execute("SELECT FlagGoofsGaffs FROM ServerSettings WHERE GuildID = ?", (message.guild.id,))
        row = games_curs.fetchone()
        if not await checkIgnoredChannels(message.channel.id, message.guild.id) and row[0] == 1:
            await handle_goofs_gaffs(message, games_curs, games_conn)
        
        games_curs.close()
        games_conn.close()
    
    # Insert message into Master table
    tp = '''INSERT INTO Master (GuildName,GuildID, UserName, UserID, ChannelName, ChannelID, UTCTime) VALUES (?,?,?,?,?,?,?);'''
    data = (message.guild.name, str(message.guild.id), message.author.name, str(message.author.id), 
            message.channel.name, str(message.channel.id), str(message.created_at.utcnow()))
    curs.execute(tp, data)
    
    # Handle emoji tracking
    pattern = r'<(?P<animated>a?):(?P<name>[a-zA-Z0-9_]{2,32}):(?P<id>[0-9]{18,22})>'
    for match in re.finditer(pattern, message.content):
        isInServer = 0
        for emoji in message.guild.emojis:
            if emoji.id == int(match.group('id')):
                isInServer = 1
        if isInServer == 1:
            insertStr = '''INSERT INTO InServerEmoji (GuildName,GuildID, UserName, UserID, ChannelName, ChannelID, UTCTime, EmojiID, EmojiName, AnimatedFlag) VALUES (?,?,?,?,?,?,?,?,?,?);'''
            Emojidata = (message.guild.name, str(message.guild.id), message.author.name, str(message.author.id), 
                        message.channel.name, str(message.channel.id), str(message.created_at.utcnow()),
                        match.group('id'), match.group('name'), match.group('animated'))
            curs.execute(insertStr, Emojidata)
        else:
            print('emoji not in guild')
            insertStr = '''INSERT INTO OutOfServerEmoji (GuildName,GuildID, UserName, UserID, ChannelName, ChannelID, UTCTime, EmojiID, EmojiName, AnimatedFlag) VALUES (?,?,?,?,?,?,?,?,?,?);'''
            Emojidata = (message.guild.name, str(message.guild.id), message.author.name, str(message.author.id), 
                        message.channel.name, str(message.channel.id), str(message.created_at.utcnow()),
                        match.group('id'), match.group('name'), match.group('animated'))
            curs.execute(insertStr, Emojidata)
    
    conn.commit()
    curs.close()
    conn.close()


async def handle_goofs_gaffs(message, games_curs, games_conn):
    """Handle goofs and gaffs responses."""
    import random
    games_curs.execute("SELECT * FROM GoofsGaffs WHERE GuildID = ?", (message.guild.id,))
    row = games_curs.fetchone()
    games_curs.execute('''SELECT PingTimestamp, HorseTimestamp, CatTimestamp, MarathonTimestamp, TwitterAltTimestamp FROM UserStats WHERE GuildID = ? AND UserID = ?''', 
                      (message.guild.id, message.author.id))
    userStatsTimestamps = games_curs.fetchone()
    if not userStatsTimestamps:
        games_curs.execute('''INSERT INTO UserStats (GuildID, UserID) VALUES (?, ?)''', (message.guild.id, message.author.id))
        games_conn.commit()
        games_curs.execute('''SELECT PingTimestamp, HorseTimestamp, CatTimestamp, MarathonTimestamp, TwitterAltTimestamp FROM UserStats WHERE GuildID = ? AND UserID = ?''', 
                          (message.guild.id, message.author.id))
        userStatsTimestamps = games_curs.fetchone()
    currentDate = datetime.now().date()
    
    if not row:
        return None
    
    FlagHorse = row["FlagHorse"]
    HorseChance = row["HorseChance"]
    FlagPing = row["FlagPing"]
    FlagMarathon = row["FlagMarathon"]
    MarathonChance = row["MarathonChance"]
    FlagCat = row["FlagCat"]
    CatChance = row["CatChance"]
    FlagTwitterAlt = row["FlagTwitterAlt"]
    TwitterAltChance = row["TwitterAltChance"]
    
    splitstr = message.content.split()
    
    # Handle TwitterAlt
    if "girlcockx.com" in message.content and FlagTwitterAlt:
        UserStatTwitterTimestamp = userStatsTimestamps["TwitterAltTimestamp"]
        UserStatTwitterTimestamp = datetime.strptime(UserStatTwitterTimestamp, '%Y-%m-%d').date()
        statsFlag = 0
        if currentDate != UserStatTwitterTimestamp:
            statsFlag = 1
        r = random.random()
        if r < TwitterAltChance:
            if statsFlag == 1:
                games_curs.execute('''UPDATE UserStats SET TwitterAltTimestamp = ?, TwitterAltHitCount = TwitterAltHitCount + 1 WHERE GuildID = ? AND UserID = ?''', 
                                 (currentDate, message.guild.id, message.author.id))
            responseImage = discord.File("images/based_on_recent_events.png", filename="response.png")
            await message.reply(file=responseImage)
        else:
            if statsFlag == 1:
                games_curs.execute('''UPDATE UserStats SET TwitterAltTimestamp = ?, TwitterAltMissCount = TwitterAltMissCount + 1 WHERE GuildID = ? AND UserID = ?''', 
                                 (currentDate, message.guild.id, message.author.id))
        games_conn.commit()
    
    # Handle Horse
    if "horse" in message.content.lower() and FlagHorse:
        UserStatHorseTimestamp = userStatsTimestamps["HorseTimestamp"]
        UserStatHorseTimestamp = datetime.strptime(UserStatHorseTimestamp, '%Y-%m-%d').date()
        statsFlag = 0
        if currentDate != UserStatHorseTimestamp:
            statsFlag = 1
        r = random.random()
        if r < HorseChance:
            if statsFlag == 1:
                games_curs.execute('''UPDATE UserStats SET HorseTimestamp = ?, HorseHitCount = HorseHitCount + 1 WHERE GuildID = ? AND UserID = ?''', 
                                 (currentDate, message.guild.id, message.author.id))
            responseImage = discord.File("images/horse.gif", filename="response.gif")
            await message.reply(file=responseImage)
        else:
            if statsFlag == 1:
                games_curs.execute('''UPDATE UserStats SET HorseTimestamp = ?, HorseMissCount = HorseMissCount + 1 WHERE GuildID = ? AND UserID = ?''', 
                                 (currentDate, message.guild.id, message.author.id))
        games_conn.commit()
    
    # Handle Cat
    if splitstr[0].lower() == 'cat' and FlagCat:
        UserStatCatTimestamp = userStatsTimestamps["CatTimestamp"]
        UserStatCatTimestamp = datetime.strptime(UserStatCatTimestamp, '%Y-%m-%d').date()
        statsFlag = 0
        if currentDate != UserStatCatTimestamp:
            statsFlag = 1
        await asyncio.sleep(1)
        newMessage = await message.channel.fetch_message(message.id)
        reactions = newMessage.reactions
        for reaction in reactions:
            userList = [user async for user in reaction.users()]
            for user in userList:
                if user.id == 966695034340663367:
                    r = random.random()
                    if r < CatChance:
                        if statsFlag == 1:
                            games_curs.execute('''UPDATE UserStats SET CatTimestamp = ?, CatHitCount = CatHitCount + 1 WHERE GuildID = ? AND UserID = ?''', 
                                             (currentDate, message.guild.id, message.author.id))
                        await asyncio.sleep(.5)
                        responseImage = discord.File("images/cat_laugh.gif", filename="cat_laugh.gif")
                        await message.reply(file=responseImage)
                    else:
                        if statsFlag == 1:
                            games_curs.execute('''UPDATE UserStats SET CatTimestamp = ?, CatMissCount = CatMissCount + 1 WHERE GuildID = ? AND UserID = ?''', 
                                             (currentDate, message.guild.id, message.author.id))
        games_conn.commit()
    
    # Handle Marathon
    if "marathon" in message.content.lower() and FlagMarathon:
        UserStatMarathonTimestamp = userStatsTimestamps["MarathonTimestamp"]
        UserStatMarathonTimestamp = datetime.strptime(UserStatMarathonTimestamp, '%Y-%m-%d').date()
        statsFlag = 0
        if currentDate != UserStatMarathonTimestamp:
            statsFlag = 1
        r = random.random()
        if r < MarathonChance:
            if statsFlag == 1:
                games_curs.execute('''UPDATE UserStats SET MarathonTimestamp = ?, MarathonHitCount = MarathonHitCount + 1 WHERE GuildID = ? AND UserID = ?''', 
                                 (currentDate, message.guild.id, message.author.id))
            responseImage = discord.File("images/marathon.gif", filename="response.gif")
            await message.reply(file=responseImage)
        else:
            if statsFlag == 1:
                games_curs.execute('''UPDATE UserStats SET MarathonTimestamp = ?, MarathonMissCount = MarathonMissCount + 1 WHERE GuildID = ? AND UserID = ?''', 
                                 (currentDate, message.guild.id, message.author.id))
        games_conn.commit()
    
    # Handle Ping
    if (splitstr[0].lower() == 'ping' and FlagPing):
        UserStatPingTimestamp = userStatsTimestamps["PingTimestamp"]
        UserStatPingTimestamp = datetime.strptime(UserStatPingTimestamp, '%Y-%m-%d').date()
        statsFlag = 0
        if currentDate != UserStatPingTimestamp:
            statsFlag = 1
        rand = random.random()
        if rand < .2:
            await message.channel.send("pong")
            if statsFlag == 1:
                games_curs.execute('''UPDATE UserStats SET PingTimestamp = ?, PingPongCount = PingPongCount + 1 WHERE GuildID = ? AND UserID = ?''', 
                                 (currentDate, message.guild.id, message.author.id))
        elif rand < .4:
            await message.channel.send("song")
            if statsFlag == 1:
                games_curs.execute('''UPDATE UserStats SET PingTimestamp = ?, PingSongCount = PingSongCount + 1 WHERE GuildID = ? AND UserID = ?''', 
                                 (currentDate, message.guild.id, message.author.id))
        elif rand < .6:
            await message.channel.send("dong")
            if statsFlag == 1:
                games_curs.execute('''UPDATE UserStats SET PingTimestamp = ?, PingDongCount = PingDongCount + 1 WHERE GuildID = ? AND UserID = ?''', 
                                 (currentDate, message.guild.id, message.author.id))
        elif rand < .8:
            await message.channel.send("long")
            if statsFlag == 1:
                games_curs.execute('''UPDATE UserStats SET PingTimestamp = ?, PingLongCount = PingLongCount + 1 WHERE GuildID = ? AND UserID = ?''', 
                                 (currentDate, message.guild.id, message.author.id))
        elif rand < .99:
            await message.channel.send("kong")
            if statsFlag == 1:
                games_curs.execute('''UPDATE UserStats SET PingTimestamp = ?, PingKongCount = PingKongCount + 1 WHERE GuildID = ? AND UserID = ?''', 
                                 (currentDate, message.guild.id, message.author.id))
        else:
            await message.channel.send("you found the special message. here is your gold star!")
            if statsFlag == 1:
                games_curs.execute('''UPDATE UserStats SET PingTimestamp = ?, PingGoldStarCount = PingGoldStarCount + 1 WHERE GuildID = ? AND UserID = ?''', 
                                 (currentDate, message.guild.id, message.author.id))
        games_conn.commit()

