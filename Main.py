import discord
import sqlite3
import os
#import time
from discord.ext import tasks, commands
from discord.utils import get
import random
from datetime import datetime, timedelta, time
import asyncio
import logging
import re
import asyncio
import zoneinfo

from Helpers.Helpers import award_points, checkIgnoredChannels, smrtGame, achievementTrigger, achievement_leaderboard_generator, delete_later, rank_number_to_rank_name
import context
from cogs.Trivia import questionSpawner, QuestionStealButton



@tasks.loop(time=time(hour=23, minute=55, second=0, tzinfo=zoneinfo.ZoneInfo("America/Los_Angeles")))
async def daily_question_leaderboard():
    games_conn=sqlite3.connect("games.db",timeout=10)
    games_curs=games_conn.cursor()
    games_curs.execute('''SELECT GuildID, FlagShameChannel, ShameChannel from ServerSettings''')
    guilds=games_curs.fetchall()
    for guildID in guilds:
        if guildID[1]==1 and guildID[2]:
            games_curs.execute('''SELECT UserID, QuestionsAnsweredTodayCorrect FROM GamblingUserStats WHERE GuildID = ? and (date(LastDailyQuestionTime) = date('now', 'localtime') OR date(LastRandomQuestionTime) = date('now', 'localtime')) order by QuestionsAnsweredTodayCorrect desc''', (guildID[0],))
            leaderboardResults = games_curs.fetchall()
            todaysDate = datetime.now().date()
            embed=discord.Embed(title=f"Daily Question Leaderboard for {todaysDate}", description="", color=0x00ff00)
            printstr=f"**Daily Question Leaderboard for {todaysDate}**\n\n"
            if leaderboardResults:
                # Process leaderboard results
                for userID, questionsAnswered in leaderboardResults:
                    embed.description += f"<@{userID}>: {questionsAnswered} correct answers today.\n"
                    #printstr += f"<@{userID}>: {questionsAnswered} correct answers today.\n"
            #get the channel from the ShameChannel channelID
            channel = client.get_channel(guildID[2])
            await channel.send(content=printstr, embed=embed, allowed_mentions=discord.AllowedMentions.none())

@tasks.loop(time=time(hour=0, minute=0, second=0, tzinfo=zoneinfo.ZoneInfo("America/Los_Angeles")))
async def grant_ranked_token():
    games_conn=sqlite3.connect("games.db",timeout=10)
    games_curs=games_conn.cursor()
    games_curs.execute('''UPDATE GamblingUserStats SET RankedDiceTokens = min(RankedDiceTokens + 1, 3)''')
    games_conn.commit()
    #games_curs.execute('''SELECT Season FROM RankedDiceGlobals''')
    #current_season = games_curs.fetchone()
    #games_curs.execute('''SELECT ''')
    #games_curs.execute('''UPDATE PlayerSkill SET Rank = Rank - 0.1 WHERE LastPlayed < ? and ProvisionalGames = 0''', (datetime.now() - timedelta(days=2),))
    games_curs.execute(
    '''
    UPDATE PlayerSkill
    SET Rank = Rank - 0.1
    WHERE LastPlayed < ?
      AND ProvisionalGames = 0
      AND EXISTS (
            SELECT 1
            FROM LiveRankedDicePlayers p
            JOIN LiveRankedDiceMatches m
              ON m.ID = p.MatchID
            WHERE p.UserID = PlayerSkill.UserID
              AND m.GuildID = PlayerSkill.GuildID
              AND m.Season = (
                    SELECT Season
                    FROM RankedDiceGlobals
              )
      )
    ''',
    (datetime.now() - timedelta(days=2),)
)
    games_conn.commit()
    games_curs.close()
    games_conn.close()

@tasks.loop(time=time(hour=0, minute=2, second=0, tzinfo=zoneinfo.ZoneInfo("America/Los_Angeles")))
async def package_daily_gambling():
    print("Packaging daily gambling totals for auction house...")
    games_conn=sqlite3.connect("games.db",timeout=10)
    games_conn.row_factory = sqlite3.Row
    games_curs=games_conn.cursor()
    today = datetime.now().date()
    #conclude yesterdays game
    rollOverFlag=0
    rollOverAmount=0
    games_curs.execute('''select * from AuctionHousePrize where Date=?''', (today - timedelta(days=1),))
    yesterday_auction_data = games_curs.fetchall()
    #check if there were any rows
    if yesterday_auction_data:
        for row in yesterday_auction_data:
            games_curs.execute('''select CurrentBalance from GamblingUserStats where GuildID=? and UserID=?''', (row['CurrentBidderGuildID'], row['CurrentBidderUserID']))
            bidder_balance = games_curs.fetchone()
            if bidder_balance and bidder_balance[0] >= row['CurrentPrice'] and row['CurrentPrice']>0:
                # Deduct the bid amount from the bidder's balance
                #new_balance = bidder_balance[0] - row['CurrentPrice']
                #new_balance = new_balance + int(row['AmountAuctioned'])
        
                #games_curs.execute('''UPDATE GamblingUserStats SET CurrentBalance=? WHERE GuildID=? AND UserID=?''', (new_balance, row['CurrentBidderGuildID'], row['CurrentBidderUserID']))
                if int(row['AmountAuctioned'])-int(row['CurrentPrice'])>0:
                    games_curs.execute('''Update GamblingUserStats SET AuctionHouseWinnings = AuctionHouseWinnings + ? WHERE GuildID=? AND UserID=?''', (int(row['AmountAuctioned'])-int(row['CurrentPrice']), row['CurrentBidderGuildID'], row['CurrentBidderUserID']))
                else:
                    games_curs.execute('''Update GamblingUserStats SET AuctionHouseLosses = AuctionHouseLosses + ? WHERE GuildID=? AND UserID=?''', (int(row['CurrentPrice'])-int(row['AmountAuctioned']), row['CurrentBidderGuildID'], row['CurrentBidderUserID']))
                games_conn.commit()
                await award_points(-row['CurrentPrice'], row['CurrentBidderGuildID'], row['CurrentBidderUserID'])
                await award_points(int(row['AmountAuctioned']), row['CurrentBidderGuildID'], row['CurrentBidderUserID'])
                await achievementTrigger(row['CurrentBidderGuildID'], row['CurrentBidderUserID'], 'AuctionHouseWinnings')
                await achievementTrigger(row['CurrentBidderGuildID'], row['CurrentBidderUserID'], 'AuctionHouseLosses')
                games_curs.execute('''UPDATE AuctionHousePrize SET HasBeenCleared=1, FinalBidderGuildId = ?, FinalBidderUserId = ? WHERE Date=? AND Zone=?''', (row['CurrentBidderGuildID'], row['CurrentBidderUserID'], today - timedelta(days=1), row['Zone']))
                games_conn.commit()
                #send the winner a dm about their win with the amount spent and the amount earned
                user = client.get_guild(row['CurrentBidderGuildID']).get_member(row['CurrentBidderUserID'])
                if user:
                    try:
                        await user.send(f"Congratulations! You won the auction for {row['Zone']} with a bid of {row['CurrentPrice']} points. You have been awarded {int(row['AmountAuctioned'])} points, resulting in a net gain of {int(row['AmountAuctioned']) - row['CurrentPrice']} points.")
                    except Exception as e:
                        print(f"Failed to send DM to user {row['FinalBidderUserID']}: {e}")
            else:
                rollOverFlag=1
                #rollOverAmount+=row['AmountAuctioned']
                games_curs.execute('''INSERT INTO DailyGamblingTotals (Date, GuildID, Category, Funds) VALUES (?, ?, ?, ?)''', (today - timedelta(days=1), 9999999999, row['Zone'], row['AmountAuctioned']))
    #set up todays game
    games_curs.execute('''SELECT Category, sum(Funds) from DailyGamblingTotals where Date=date('now', '-1 day', 'localtime') group by Category''')
    yesterday_totals = games_curs.fetchall()
    
    for row in yesterday_totals:
        random_multiplier = random.random()
        random_multiplier=(random_multiplier*.07)+.03
        random_multiplier = round(random_multiplier, 2)
        category = row[0]
        yesterday_total = row[1]
        amount_auctioned = yesterday_total * random_multiplier
        amount_auctioned = round(amount_auctioned)
        games_curs.execute('''INSERT INTO AuctionHousePrize (Date, Zone, TotalAmount, PercentAuctioned, AmountAuctioned, HasRollOver) VALUES (?, ?, ?, ?, ?, ?)''', (today, category, yesterday_total, random_multiplier, amount_auctioned+rollOverAmount, rollOverFlag))
    games_conn.commit()
    games_curs.close()
    games_conn.close()
    return

@tasks.loop(time=time(hour=0, minute=2, second=15, tzinfo=zoneinfo.ZoneInfo("America/Los_Angeles")))
async def daily_achievement_leaderboard_post():
    print("Posting daily achievement leaderboard...")
    games_conn=sqlite3.connect("games.db",timeout=10)
    games_curs=games_conn.cursor()
    games_curs.execute('''SELECT GuildID, FlagShameChannel, ShameChannel from ServerSettings''')
    guilds=games_curs.fetchall()
    for guild in guilds:
        guildID, flagShameChannel, shameChannel = guild
        if flagShameChannel==1 and shameChannel:
            embed = await achievement_leaderboard_generator(guildID=guildID)
            channel = client.get_channel(shameChannel)
            if channel:
                await channel.send(embed=embed)

@tasks.loop(minutes=5, seconds=0)
async def cleanup_abandoned_trivia_loop():
    games_conn = sqlite3.connect("games.db")
    games_curs = games_conn.cursor()
    # Perform cleanup operations on abandoned trivia sessions
    games_curs.execute('''SELECT * FROM ActiveTrivia WHERE Timestamp < ?''', (datetime.now() - timedelta(minutes=5),))
    abandoned_sessions = games_curs.fetchall()
    games_conn.commit()
    games_curs.close()
    games_conn.close()
    for session in abandoned_sessions:
        guildID, userID, messageID, questionID, questionType, questionDifficulty, questionText = session[0], session[1], session[2], session[3], session[4], session[5], session[6]
        await abandoned_trivia_cleanup(guildID, userID, messageID, questionID, questionType, questionDifficulty, questionText)
    return

async def abandoned_trivia_cleanup(guildID: int, userID: int, messageID: int, questionID: int, questionType: str, questionDifficulty: str, questionText: str):
    games_conn=sqlite3.connect('games.db',timeout=10)
    games_curs = games_conn.cursor()
    games_curs.execute('''INSERT INTO Scores (GuildID, UserID, Category, Difficulty, Num_Correct, Num_Incorrect) VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(GuildID, UserID, Category, Difficulty) DO UPDATE SET Num_Incorrect = Num_Incorrect + 1;''', (guildID, userID, questionType, questionDifficulty, 0, 1))
    games_curs.execute('''UPDATE QuestionList SET GlobalIncorrect = GlobalIncorrect + 1 WHERE ID=?''', (questionID,))
    games_conn.commit()
    games_curs.execute('''SELECT FlagShameChannel, ShameChannel FROM ServerSettings WHERE GuildID=?''', (guildID,))
    shameSettings = games_curs.fetchone()
    games_curs.execute('''SELECT ID, Question, Answers, Type, Difficulty, ShadowAnswers FROM QuestionList WHERE ID=?''', (questionID,))
    questionData = games_curs.fetchone()
    stealButton=QuestionStealButton(question=questionData,label ="STEAL", style=discord.ButtonStyle.danger)
    games_curs.execute('''INSERT INTO TriviaEventLog (GuildID, UserID, DailyOrRandom, QuestionType, QuestionDifficulty, QuestionText, QuestionAnswers, UserAnswer, ClassicDecision, LLMDecision, LLMText, CurrentQuestionsAnsweredToday, CurrentQuestionsAnsweredTodayCorrect) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (guildID, userID, 'abandoned', questionType, questionDifficulty, questionData[1], questionData[2], None, 0, 0, None, 0, 0))
    games_conn.commit()
    view=discord.ui.View()
    view.add_item(stealButton)
    if shameSettings and shameSettings[0] == 1:
        #get the shame channel from the guildID instead
        guild=client.get_guild(guildID)
        shameChannel = guild.get_channel(shameSettings[1])
        
        if shameChannel:
            shameMessage = await shameChannel.send(f"Oops! <@{userID}> didn't give an answer to: {questionText}",allowed_mentions=discord.AllowedMentions.none(),view=view)
            shameMessageID = shameMessage.id
            games_curs.execute('''INSERT INTO ActiveSteals (GuildID, ChannelID, MessageID) VALUES (?, ?, ?)''', (guildID, shameChannel.id, shameMessageID))
            games_conn.commit()
        else:
            #try to get the thread
            shameThread = guild.get_thread(shameSettings[1])
            if shameThread:
                shameMessage = await shameThread.send(f"Oops! <@{userID}> didn't give an answer to: {questionText}",allowed_mentions=discord.AllowedMentions.none(),view=view)
                shameMessageID = shameMessage.id
                games_curs.execute('''INSERT INTO ActiveSteals (GuildID, ChannelID, MessageID) VALUES (?, ?, ?)''', (guildID, shameThread.id, shameMessageID))
                games_conn.commit()
    games_curs.execute('''DELETE FROM ActiveTrivia WHERE GuildID=? AND UserID=? AND MessageID=?''', (guildID, userID, messageID))
    games_conn.commit()
    games_curs.close()
    games_conn.close()




@tasks.loop(hours=1)
async def clear_steals_loop():
    print("Clearing old steal messages...")
    games_conn = sqlite3.connect("games.db")
    games_curs = games_conn.cursor()
    # Perform cleanup operations on abandoned trivia sessions
    games_curs.execute('''SELECT GuildID, ChannelID, MessageID, Timestamp FROM ActiveSteals''')
    active_steals = games_curs.fetchall()
    for steal in active_steals:
        await asyncio.sleep(1)  # to avoid rate limits
        guildID, channelID, messageID, timestamp = steal
        print(f"{datetime.now() - datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')}")
        if datetime.now() - datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S') > timedelta(hours=1):
            print(f"Clearing steal message {messageID} in guild {guildID}, channel {channelID}...")
            guild = client.get_guild(guildID)
            if guild:
                channel = guild.get_channel(channelID)
                if channel:
                    try:
                        message = await channel.fetch_message(messageID)
                        #grey out the button on the message
                        view=discord.ui.View()
                        button=discord.ui.Button(label="STEAL", style=discord.ButtonStyle.gray, disabled=True)
                        view.add_item(button)
                        await message.edit(view=view)
                    except Exception as e:
                        print(f"Failed to delete steal message {messageID} in guild {guildID}, channel {channelID}: {e}")
                else:
                    thread = await guild.fetch_channel(channelID)
                    if thread:
                        try:
                            message = await thread.fetch_message(messageID)
                            view=discord.ui.View()
                            button=discord.ui.Button(label="STEAL", style=discord.ButtonStyle.gray, disabled=True)
                            view.add_item(button)
                            await message.edit(view=view)
                        except Exception as e:
                            print(f"Failed to delete steal message {messageID} in guild {guildID}, thread {channelID}: {e}")
            games_curs.execute('''DELETE FROM ActiveSteals WHERE GuildID=? AND ChannelID=? AND MessageID=?''', (guildID, channelID, messageID))
    
    games_conn.commit()
    games_curs.close()
    games_conn.close()
    return
    
@tasks.loop(time=time(hour=0, minute=5, second=10, tzinfo=zoneinfo.ZoneInfo("America/Los_Angeles")))
async def monthly_ranked_dice_reset():
    print("Resetting monthly ranked dice stats...")
    today = datetime.now()
    if today.day != 1:
        return
        #pass
    games_conn=sqlite3.connect("games.db",timeout=10)
    games_curs=games_conn.cursor()
    games_curs.execute('''UPDATE RankedDiceGlobals SET Season = Season + 1''')
    games_conn.commit()
    games_curs.execute('''SELECT UserID, GuildID, Rank, Mu, Sigma, ProvisionalGames FROM PlayerSkill''')
    player_data = games_curs.fetchall()
    for userID, guildID, rank, mu, sigma, provisionalGames in player_data:
        newMu=21#((mu-30)/5)+30
        newSigma=sigma
        if sigma<5:
            newSigma=sigma*2
        if rank > 20:
            pointsPayout=int(40*(rank-20))
            rankedTokenPayout=int((rank-20)//3)
        else:
            pointsPayout=20
            rankedTokenPayout=1
        games_curs.execute('''UPDATE GamblingUserStats SET RankedDiceTokens = RankedDiceTokens + ? WHERE GuildID=? AND UserID=?''', (rankedTokenPayout, guildID, userID))
        games_conn.commit()
        await award_points(pointsPayout, guildID, userID)
        #try to dm the user about their rewards
        user = await client.fetch_user(userID)
        rankName = await rank_number_to_rank_name(rank)
        games_curs.execute('''UPDATE PlayerSkill SET SeasonalWinCount = 0, SeasonalLossCount = 0, SeasonalGamesPlayed = 0, RANK = case when Rank >21 then 21 else Rank end, Mu = ?, Sigma = ? WHERE GuildID = ? AND UserID = ?''', (newMu, newSigma, guildID, userID))
        games_conn.commit()
        if provisionalGames > 0:
            continue  # Skip provisional players for end-of-season rewards
        try:
            guildName = client.get_guild(int(guildID)).name
            embed=discord.Embed(title=f"Ranked Dice Season Ended in {guildName}!", description=f"The current Ranked Dice season has ended! You achieved a final rank of: {rankName}. As a reward, you have received {pointsPayout} points and {rankedTokenPayout} Ranked Dice tokens!\n\nAt the end of each season if you are in diamond rank or higher, your rank will be reset to diamond 1, your MMR will be slightly reduced based on your end of season rank, and your MMR variance score will be increased to help you get moving faster back up.", color=0x52b138)
            await user.send(embed=embed)
        except Exception as e:
            print(f"Failed to send DM to user {userID} in guild {guildID}: {e}")
            logging.warning(f"Failed to send DM to user {userID} in guild {guildID}: {e}")
        
    games_conn.commit()
    games_curs.close()
    games_conn.close()

class MyClient(commands.Bot):
    ignoreList=[]
    async def on_ready(self):
        #8 f=open(
        print('Logged on as {0}!'.format(self.user))
        #print(random.random())
        channel=client.get_channel(150421071676309504)
        await channel.send("rebooted")
        channel=client.get_channel(1337282148054470808)
        await channel.send("rebooted")
        DB_NAME = "My_DB"
        conn = sqlite3.connect(DB_NAME)
        curs = conn.cursor()

        with open('mainDB_Schemas.sql') as f:
            curs.executescript(f.read())
        
        #mostly for creating the tables in prod
        game_conn = sqlite3.connect("games.db")
        game_curs = game_conn.cursor()
        with open('gamesDB_Schemas.sql') as f:
            game_curs.executescript(f.read())
        game_conn.commit()
        

        currentGuilds=[guild.id for guild in client.guilds]
        print(currentGuilds)
        for guild in currentGuilds:
            curs.execute('''INSERT OR IGNORE INTO ServerSettings (GuildID) VALUES (?);''',(guild,))
            game_curs.execute('''INSERT OR IGNORE INTO GoofsGaffs (GuildID) VALUES (?);''',(guild,))
            game_curs.execute('''INSERT OR IGNORE INTO GamblingUnlockConditions (GuildID) VALUES (?);''',(guild,))
            game_curs.execute('''INSERT OR IGNORE INTO FeatureTimers (GuildID) VALUES (?);''',(guild,))
            game_curs.execute('''INSERT OR IGNORE INTO ServerSettings (GuildID) VALUES (?);''',(guild,))
            game_conn.commit()

        conn.commit()  
        curs.execute('''CREATE INDEX IF NOT EXISTS idx_guild_time ON Master (GuildID, UTCTime)''')
        
        curs.execute("PRAGMA temp_store = MEMORY;")  # Use RAM for temp storage
        curs.execute("PRAGMA synchronous = NORMAL;")  # Speeds up writes
        curs.execute("PRAGMA journal_mode = WAL;")  # Allows concurrent reads/writes
        curs.execute("PRAGMA cache_size = 1000000;")  # Increases cache size
        conn.commit()
        game_conn.commit()
        curs.close()
        conn.close()
        game_curs.close()
        game_conn.close()
        #assignRoles.start()
        #await assignRoles()
        #sched=AsyncIOScheduler()
        #sched.add_job(assignRoles,'interval',seconds=900)
        if not cleanup_abandoned_trivia_loop.is_running():
            cleanup_abandoned_trivia_loop.start()
        if not package_daily_gambling.is_running():
            package_daily_gambling.start()
        if not daily_question_leaderboard.is_running():
            daily_question_leaderboard.start()
        if not clear_steals_loop.is_running():
            clear_steals_loop.start()
        if not daily_achievement_leaderboard_post.is_running():
            daily_achievement_leaderboard_post.start()
        if not grant_ranked_token.is_running():
            grant_ranked_token.start()
        if not monthly_ranked_dice_reset.is_running():
            monthly_ranked_dice_reset.start()
        #sched.start()
        #await checkAnswer(question="test",userAnswer="test",correctAnswer="test")
        await client.tree.sync()
        
    def __init__(self, *, intents, **options):
        super().__init__(command_prefix='!', intents=intents, **options)
        #self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.load_extension('cogs.Other')
        await self.load_extension('cogs.Trivia')
        await self.load_extension('cogs.Games')
        await self.load_extension('cogs.Core')
        await self.load_extension('cogs.Analytics')

        #await self.tree.sync()
        print('synced')

    async def on_thread_create(self,thread):
        await thread.join()

    #doesnt run at all if bot is offline at guild invite. be careful
    async def on_guild_join(self, guild):
        DB_NAME = "My_DB"
        conn = sqlite3.connect(DB_NAME)
        curs = conn.cursor()
        curs.execute('''INSERT OR IGNORE INTO ServerSettings (GuildID) VALUES (?);''',(guild.id,))
        
        conn.commit()  
        curs.close()
        conn.close()
        games_conn = sqlite3.connect("games.db")
        games_curs = games_conn.cursor()    
        games_curs.execute('''INSERT INTO GamblingUnlockConditions (GuildID) values (?)''', (guild.id,))
        games_conn.commit()
        games_curs.execute('''INSERT INTO ServerSettings (GuildID) VALUES (?)''', (guild.id,))
        games_conn.commit()
        games_curs.execute('''INSERT OR IGNORE INTO FeatureTimers (GuildID) VALUES (?);''',(guild.id,))
        games_conn.commit()
        games_curs.execute('''INSERT OR IGNORE INTO GoofsGaffs (GuildID) VALUES (?);''',(guild.id,))
        games_conn.commit()
        games_curs.close()
        games_conn.close()

    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return
        gameDB= "games.db"
        game_conn = sqlite3.connect(gameDB)
        game_curs = game_conn.cursor()
        #get the messageID from the featuretimers table pip column
        game_curs.execute('''SELECT LastBonusPipMessage FROM FeatureTimers WHERE GuildID=?''', (reaction.message.guild.id,))
        lastBonusPipMessage = game_curs.fetchone()
        if reaction.emoji=='✅' and lastBonusPipMessage is not None and lastBonusPipMessage[0] == reaction.message.id:
            game_curs.execute('''INSERT INTO Scores ( GuildID, UserID, Category, Difficulty, Num_Correct, Num_Incorrect) VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(GuildID, UserID, Category, Difficulty) DO UPDATE SET Num_Correct = Num_Correct + 1;''', (reaction.message.guild.id,user.id, 'bonus', 1, 1, 0))
            game_conn.commit()
            try:
                await reaction.message.clear_reaction(reaction.emoji)
                game_curs.execute('''UPDATE FeatureTimers SET LastBonusPipMessage=?, LastBonusPipChannel = ? WHERE GuildID=?''', (None, None, reaction.message.guild.id))
                game_conn.commit()
                await award_points(1, reaction.message.guild.id, user.id)  # Award 5 points for bonus pip
                await achievementTrigger(reaction.message.guild.id, user.id, "bonus")
            except Exception as e:
                print(f"Failed to clear reaction or update DB: {e}")
                msg = await reaction.message.channel.send("I do not have permissions to remove reactions in this channel. Please grant me the 'Manage Messages' permission to use this feature, or add this channel to the ignored channels list using /game-settings-set command to disable all interactions in this channel.", allowed_mentions=discord.AllowedMentions.none())
                await delete_later(msg, 10)
                logging.warning(f"Failed to clear reaction or update DB: {e} in guild {reaction.message.guild.id}, channel {reaction.message.channel.id}")
        game_curs.close()
        game_conn.close()

    async def on_message(self, message):
        if message.author==client.user:
            return
        if message.author.bot:
            #print('bot!')
            if message.author.id==510016054391734273:
                splitstr=message.content.split()
                if "RUINED" in splitstr:
                    await asyncio.sleep(5)
                    await message.channel.send("https://tenor.com/view/death-stranding-2-sisyphus-on-the-beach-hideo-kojima-mountain-climb-gif-9060768058445058879")
            return
        
       
        #await message.channel.send('<a:bubble_irl:1039925482998743160>')
        #for emoji in message.guild.emojis:
            #print(emoji.name)
            #print(emoji.id)
        DB_NAME = "My_DB"
        conn = sqlite3.connect(DB_NAME)
        curs = conn.cursor()

        if not await checkIgnoredChannels(message.channel.id, message.guild.id):
            await smrtGame(message)
            await asyncio.sleep(.05)
            await questionSpawner(message)
        #print('Message from {0.author}: {0.content}'.format(message))
        print(message.guild.name)
        splitstr=message.content.split()
        if len(message.content)>0:
            games_path = "games.db"
            games_conn = sqlite3.connect(games_path, timeout=10)
            games_conn.row_factory = sqlite3.Row  # allows dict-like access
            games_curs = games_conn.cursor()

            games_curs.execute("SELECT FlagGoofsGaffs FROM ServerSettings WHERE GuildID = ?", (message.guild.id,))  
            row = games_curs.fetchone()
            if not await checkIgnoredChannels(message.channel.id, message.guild.id) and row[0]==1:
                games_curs.execute("SELECT * FROM GoofsGaffs WHERE GuildID = ?", (message.guild.id,))
                row = games_curs.fetchone()
                games_curs.execute('''SELECT PingTimestamp, HorseTimestamp, CatTimestamp, MarathonTimestamp, TwitterAltTimestamp FROM UserStats WHERE GuildID = ? AND UserID = ?''', (message.guild.id, message.author.id))
                userStatsTimestamps = games_curs.fetchone()
                if not userStatsTimestamps:
                    games_curs.execute('''INSERT INTO UserStats (GuildID, UserID) VALUES (?, ?)''', (message.guild.id, message.author.id))
                    games_conn.commit()
                    games_curs.execute('''SELECT PingTimestamp, HorseTimestamp, CatTimestamp, MarathonTimestamp, TwitterAltTimestamp FROM UserStats WHERE GuildID = ? AND UserID = ?''', (message.guild.id, message.author.id))
                    userStatsTimestamps = games_curs.fetchone()
                currentDate = datetime.now().date()

                if not row:
                    return None  # no record for this guild

                # assign variables dynamically
                FlagHorse = row["FlagHorse"]
                HorseChance = row["HorseChance"]
                FlagPing = row["FlagPing"]
                FlagMarathon = row["FlagMarathon"]
                MarathonChance = row["MarathonChance"]
                FlagCat = row["FlagCat"]
                CatChance = row["CatChance"]
                FlagTwitterAlt = row["FlagTwitterAlt"]
                TwitterAltChance = row["TwitterAltChance"]


                if "girlcockx.com" in message.content and FlagTwitterAlt:
                    UserStatTwitterTimestamp = userStatsTimestamps["TwitterAltTimestamp"]
                    #convert it into an actual timestamp date only
                    UserStatTwitterTimestamp = datetime.strptime(UserStatTwitterTimestamp, '%Y-%m-%d').date()
                    statsFlag=0
                    if currentDate != UserStatTwitterTimestamp:
                        statsFlag=1
                    r=random.random.random()
                    #10% chance of response
                    if r<TwitterAltChance:
                        if statsFlag==1:
                            games_curs.execute('''UPDATE UserStats SET TwitterAltTimestamp = ?, TwitterAltHitCount = TwitterAltHitCount + 1 WHERE GuildID = ? AND UserID = ?''', (currentDate, message.guild.id, message.author.id))
                        resposneImage=discord.File("images/based_on_recent_events.png", filename="response.png")
                        await message.reply(file=resposneImage)
                    else:
                        if statsFlag==1:
                            games_curs.execute('''UPDATE UserStats SET TwitterAltTimestamp = ?, TwitterAltMissCount = TwitterAltMissCount + 1 WHERE GuildID = ? AND UserID = ?''', (currentDate, message.guild.id, message.author.id))
                    games_conn.commit()
                    #print("hold")

                if "horse" in message.content.lower() and FlagHorse:
                    #do the same thing as TwitterAlt
                    UserStatHorseTimestamp = userStatsTimestamps["HorseTimestamp"]
                    #convert it into an actual timestamp date only
                    UserStatHorseTimestamp = datetime.strptime(UserStatHorseTimestamp, '%Y-%m-%d').date()
                    statsFlag=0
                    if currentDate != UserStatHorseTimestamp:
                        statsFlag=1
                    r=random.random()
                    #25% chance of response
                    if r<HorseChance:
                        if statsFlag==1:
                            games_curs.execute('''UPDATE UserStats SET HorseTimestamp = ?, HorseHitCount = HorseHitCount + 1 WHERE GuildID = ? AND UserID = ?''', (currentDate, message.guild.id, message.author.id))
                        resposneImage=discord.File("images/horse.gif", filename="respoonse.gif")
                        await message.reply(file=resposneImage)
                        #print("hold")
                    else:
                        if statsFlag==1:
                            games_curs.execute('''UPDATE UserStats SET HorseTimestamp = ?, HorseMissCount = HorseMissCount + 1 WHERE GuildID = ? AND UserID = ?''', (currentDate, message.guild.id, message.author.id))
                    games_conn.commit()
                    await achievementTrigger(message.guild.id, message.author.id, "HorseHitCount")

                if splitstr[0].lower()=='cat' and FlagCat:
                    UserStatCatTimestamp = userStatsTimestamps["CatTimestamp"]
                    #convert it into an actual timestamp date only
                    UserStatCatTimestamp = datetime.strptime(UserStatCatTimestamp, '%Y-%m-%d').date()
                    statsFlag=0
                    if currentDate != UserStatCatTimestamp:
                        statsFlag=1
                    await asyncio.sleep(1)  # wait a bit for reactions to register
                    r= random.random()
                    if r<CatChance:
                        if statsFlag==1:
                            games_curs.execute('''UPDATE UserStats SET CatTimestamp = ?, CatHitCount = CatHitCount + 1 WHERE GuildID = ? AND UserID = ?''', (currentDate, message.guild.id, message.author.id))
                            games_conn.commit()
                        await asyncio.sleep(.5)  # give it a second to make it more dramatic
                        resposneImage=discord.File("images/cats/cat_laugh.gif", filename="cat_laugh.gif")
                        await message.reply(file=resposneImage)
                    else:
                        if statsFlag==1:
                            games_curs.execute('''UPDATE UserStats SET CatTimestamp = ?, CatMissCount = CatMissCount + 1 WHERE GuildID = ? AND UserID = ?''', (currentDate, message.guild.id, message.author.id))
                            games_conn.commit()

                    # newMessage= await message.channel.fetch_message(message.id)
                    # reactions = newMessage.reactions
                    # for reaction in reactions:
                    #     userList=[user async for user in reaction.users()]
                    #     for user in userList:
                    #         if user.id == 966695034340663367:
                    #             r= random.random()
                    #             if r<CatChance:
                    #                 if statsFlag==1:
                    #                     games_curs.execute('''UPDATE UserStats SET CatTimestamp = ?, CatHitCount = CatHitCount + 1 WHERE GuildID = ? AND UserID = ?''', (currentDate, message.guild.id, message.author.id))
                    #                 await asyncio.sleep(.5)  # give it a second to make it more dramatic
                    #                 resposneImage=discord.File("images/cat_laugh.gif", filename="cat_laugh.gif")
                    #                 await message.reply(file=resposneImage)
                    #             else:
                    #                 if statsFlag==1:
                    #                     games_curs.execute('''UPDATE UserStats SET CatTimestamp = ?, CatMissCount = CatMissCount + 1 WHERE GuildID = ? AND UserID = ?''', (currentDate, message.guild.id, message.author.id))
                    #games_conn.commit()
                    await achievementTrigger(message.guild.id, message.author.id, "CatHitCount")

                if "marathon" in message.content.lower() and FlagMarathon:
                    UserStatMarathonTimestamp = userStatsTimestamps["MarathonTimestamp"]
                    #convert it into an actual timestamp date only
                    UserStatMarathonTimestamp = datetime.strptime(UserStatMarathonTimestamp, '%Y-%m-%d').date()
                    statsFlag=0
                    if currentDate != UserStatMarathonTimestamp:
                        statsFlag=1
                    r=random.random()
                    if r<MarathonChance:
                        if statsFlag==1:
                            games_curs.execute('''UPDATE UserStats SET MarathonTimestamp = ?, MarathonHitCount = MarathonHitCount + 1 WHERE GuildID = ? AND UserID = ?''', (currentDate, message.guild.id, message.author.id))
                        resposneImage=discord.File("images/marathon.gif", filename="respoonse.gif")
                        await message.reply(file=resposneImage)
                        #print("hold")
                    else:
                        if statsFlag==1:
                            games_curs.execute('''UPDATE UserStats SET MarathonTimestamp = ?, MarathonMissCount = MarathonMissCount + 1 WHERE GuildID = ? AND UserID = ?''', (currentDate, message.guild.id, message.author.id))
                    games_conn.commit()
                    await achievementTrigger(message.guild.id, message.author.id, "MarathonHitCount")

                if (splitstr[0].lower()=='ping' and FlagPing):
                    # if message.author.id==100344687029665792:
                    #     await message.channel.send("pong")
                        
                        
                    #else:
                    UserStatPingTimestamp = userStatsTimestamps["PingTimestamp"]
                    #convert it into an actual timestamp date only
                    UserStatPingTimestamp = datetime.strptime(UserStatPingTimestamp, '%Y-%m-%d').date()
                    statsFlag=0
                    if currentDate != UserStatPingTimestamp:
                        statsFlag=1
                    rand=random.random()
                    if rand<.2:
                        await message.channel.send("pong")
                        if statsFlag==1:
                            games_curs.execute('''UPDATE UserStats SET PingTimestamp = ?, PingPongCount = PingPongCount + 1 WHERE GuildID = ? AND UserID = ?''', (currentDate, message.guild.id, message.author.id))
                    elif rand<.4:
                        await message.channel.send("song")
                        if statsFlag==1:
                            games_curs.execute('''UPDATE UserStats SET PingTimestamp = ?, PingSongCount = PingSongCount + 1 WHERE GuildID = ? AND UserID = ?''', (currentDate, message.guild.id, message.author.id))
                    elif rand<.6:
                        await message.channel.send("dong")
                        if statsFlag==1:
                            games_curs.execute('''UPDATE UserStats SET PingTimestamp = ?, PingDongCount = PingDongCount + 1 WHERE GuildID = ? AND UserID = ?''', (currentDate, message.guild.id, message.author.id))
                    elif rand<.8:
                        await message.channel.send("long")
                        if statsFlag==1:
                            games_curs.execute('''UPDATE UserStats SET PingTimestamp = ?, PingLongCount = PingLongCount + 1 WHERE GuildID = ? AND UserID = ?''', (currentDate, message.guild.id, message.author.id))
                    elif rand<.99:
                        await message.channel.send("kong")
                        if statsFlag==1:
                            games_curs.execute('''UPDATE UserStats SET PingTimestamp = ?, PingKongCount = PingKongCount + 1 WHERE GuildID = ? AND UserID = ?''', (currentDate, message.guild.id, message.author.id))
                    else:
                        await message.channel.send("you found the special message. here is your gold star!")
                        if statsFlag==1:
                            games_curs.execute('''UPDATE UserStats SET PingTimestamp = ?, PingGoldStarCount = PingGoldStarCount + 1 WHERE GuildID = ? AND UserID = ?''', (currentDate, message.guild.id, message.author.id))
                    games_conn.commit()
                    await achievementTrigger(message.guild.id, message.author.id, "PingPongCount")
                    await achievementTrigger(message.guild.id, message.author.id, "PingSongCount")
                    await achievementTrigger(message.guild.id, message.author.id, "PingDongCount")
                    await achievementTrigger(message.guild.id, message.author.id, "PingLongCount")
                    await achievementTrigger(message.guild.id, message.author.id, "PingKongCount")
                    await achievementTrigger(message.guild.id, message.author.id, "PingGoldStarCount")
            games_curs.close()
            games_conn.close()



        #inserting row into master db table          
        tp='''INSERT INTO Master (GuildName,GuildID, UserName, UserID, ChannelName, ChannelID, UTCTime) VALUES (?,?,?,?,?,?,?);'''
        data=(message.guild.name,str(message.guild.id),message.author.name,str(message.author.id),message.channel.name,str(message.channel.id),str(message.created_at.utcnow()))
        curs.execute(tp,data)


        #inserting emote data into db table
        pattern=r'<(?P<animated>a?):(?P<name>[a-zA-Z0-9_]{2,32}):(?P<id>[0-9]{18,22})>'
        for match in re.finditer(pattern, message.content):
            #print(match.group('name'))
            #print(match.group('id'))
            #print(match.group('animated'))
            isInServer=0
            for emoji in message.guild.emojis:
                if emoji.id==int(match.group('id')):
                    isInServer=1
            if isInServer==1:
                #await message.channel.send('emoji in guild')
                insertStr='''INSERT INTO InServerEmoji (GuildName,GuildID, UserName, UserID, ChannelName, ChannelID, UTCTime, EmojiID, EmojiName, AnimatedFlag) VALUES (?,?,?,?,?,?,?,?,?,?);'''
                Emojidata=(message.guild.name,str(message.guild.id),message.author.name,str(message.author.id),message.channel.name,str(message.channel.id),str(message.created_at.utcnow()),match.group('id'), match.group('name'),match.group('animated'))
                curs.execute(insertStr,Emojidata)
            else:
                print('emoji not in guild')
                insertStr='''INSERT INTO OutOfServerEmoji (GuildName,GuildID, UserName, UserID, ChannelName, ChannelID, UTCTime, EmojiID, EmojiName, AnimatedFlag) VALUES (?,?,?,?,?,?,?,?,?,?);'''
                Emojidata=(message.guild.name,str(message.guild.id),message.author.name,str(message.author.id),message.channel.name,str(message.channel.id),str(message.created_at.utcnow()),match.group('id'), match.group('name'),match.group('animated'))
                curs.execute(insertStr,Emojidata)
                #await message.channel.send('emoji not in guild')


        conn.commit()
        #Close DB
        curs.close()
        conn.close()


intents=discord.Intents.all()
client = MyClient(intents=intents) 
context.bot=client
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
log_file_path = 'log_file.log'
logging.basicConfig(filename=log_file_path, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
#logging.info('Script started')
FOToken=open('Token/Token',"r")
#logging.info('Post token')
token=FOToken.readline()
client.run(token)
