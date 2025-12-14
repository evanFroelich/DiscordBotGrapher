import discord
import sqlite3
import asyncio
import numpy as np
import random
from datetime import datetime, timedelta
import json
import context
import logging

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
    await achievementTrigger(guild_id, user_id, "LifetimeEarnings")
    await achievementTrigger(guild_id, user_id, "CurrentBalance")

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
    #run a select to see if the row exists already
    games_curs.execute('''SELECT * FROM FeatureTimers WHERE GuildID=?''', (GuildID,))
    if not games_curs.fetchone():
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
    games_curs.execute('''SELECT LastBonusPipTime, LastBonusPipMessage, LastBonusPipChannel FROM FeatureTimers WHERE GuildID=?''', (message.guild.id,))
    lastPipTime = games_curs.fetchone()
    if lastPipTime:
        if lastPipTime[1] is not None:
            #remove the reaction from the last bonus pip message
            try:
                lastChannel = message.guild.get_channel(lastPipTime[2])
                lastMessage = await lastChannel.fetch_message(lastPipTime[1])
                await lastMessage.clear_reaction('✅')
            except Exception:
                pass
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
        games_curs.execute('''UPDATE FeatureTimers SET LastBonusPipTime=?, LastBonusPipMessage=?, LastBonusPipChannel = ? WHERE GuildID=?''', (curTime, message.id, message.channel.id, message.guild.id))
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
        games_curs.execute('''INSERT INTO GamblingUserStats (GuildID, UserID, CoinFlipLosses, BlackjackLosses) VALUES (?, ?, ?, ?)''', (guildID, userID, 0, 0))
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
    print(f"Checking authorization for userID: {userID} in guildID: {guildID}")
    if int(userID) == 100344687029665792:
        print("User is the bot owner, authorized.")
        return True
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

async def achievementTrigger(guildID: str, userID: str, eventType: str):
    gamesDB = "games.db"
    games_conn = sqlite3.connect(gamesDB)
    games_curs = games_conn.cursor()
    #check this servers achievement flag
    games_curs.execute('''SELECT FlagAchievements FROM ServerSettings WHERE GuildID=?''', (guildID,))
    row = games_curs.fetchone()
    if row is None or row[0] == 0:
        games_curs.close()
        games_conn.close()
        return
    #get all achievements for this event type
    games_curs.execute('''SELECT ID, Value, Name, Description, FlavorText, CompareType from AchievementDefinitions WHERE TriggerType=? AND ID NOT IN (SELECT AchievementID FROM UserAchievements WHERE GuildID=? AND UserID=?)''', (eventType, guildID, userID))
    achievements = games_curs.fetchall()
    embedList=[]
    if eventType == "LifetimeEarnings" or eventType == "CurrentBalance" or eventType == "TipsGiven" or eventType == "CoinFlipWins" or eventType == "CoinFlipEarnings" or eventType == "CoinFlipDoubleWins" or eventType == "AuctionHouseWinnings" or eventType == "AuctionHouseLosses" or eventType == "BlackjackWins" or eventType == "BlackjackEarnings" or eventType == "Blackjack21s" or eventType == "BlackjackLosses" or eventType == "CoinFlipLosses" or eventType == "BlackjackDefeats" or eventType == "BlackjackTies" or eventType == "BlackjackNat21s" or eventType == "BlackjackLongWins" or eventType == "BlackjackLongDefeats" or eventType == "BlackjackLongTies" or eventType == "Blackjack21Ties" or eventType == "CoinFlipDoubleDefeats":
        games_curs.execute(f'''SELECT {eventType} FROM GamblingUserStats WHERE GuildID=? AND UserID=?''', (guildID, userID))
        row = games_curs.fetchone()
    elif eventType == "PingPongCount" or eventType == "PingSongCount" or eventType == "PingDongCount" or eventType == "PingLongCount" or eventType == "PingKongCount" or eventType == "PingGoldStarCount" or eventType == "HorseHitCount" or eventType == "CatHitCount" or eventType == "MarathonHitCount":
        games_curs.execute(f'''SELECT {eventType} FROM UserStats WHERE GuildID=? AND UserID=?''', (guildID, userID))
        row = games_curs.fetchone()
    elif eventType == "CurrentStreak" or eventType == "TimesFlipped":
        games_curs.execute(f'''SELECT {eventType} FROM CoinFlipLeaderboard WHERE UserID=?''', (userID,))
        row = games_curs.fetchone()
    elif eventType == "TriviaCount" or eventType == "TotalCommands" or eventType == "CountAllAs" or eventType == "CountAllFs" or eventType == "CountRainbow":
        games_curs.execute(f'''SELECT {eventType} FROM UserStatsGeneralView WHERE GuildID=? AND UserID=?''', (guildID, userID))
        row = games_curs.fetchone()
    elif eventType == "bonus":
        games_curs.execute(f'''SELECT Num_Correct FROM Scores WHERE GuildID=? AND UserID=? and Category=?''', (guildID, userID, eventType))
        row = games_curs.fetchone()
    elif eventType == "GamesPlayed" or eventType == "WinCount" or eventType == "LossCount" or eventType == "SeasonalGamesPlayed" or eventType == "SeasonalWinCount" or eventType == "SeasonalLossCount":
        games_curs.execute(f'''SELECT {eventType} FROM PlayerSkill WHERE GuildID=? AND UserID=?''', (guildID, userID))
        row = games_curs.fetchone()
    elif eventType == "WinsSpade" or eventType == "WinsHeart" or eventType == "WinsDiamond" or eventType == "WinsClub" or eventType == "PerfectRollSpade" or eventType == "PerfectRollHeart" or eventType == "PerfectRollDiamond" or eventType == "PerfectRollClub" or eventType == "MinRollSpade" or eventType == "MinRollHeart" or eventType == "MinRollDiamond" or eventType == "MinRollClub" or eventType == "D20Wins" or eventType == "FirstPlaceFinishes1v1" or eventType == "FirstPlaceFinishesLargeLobby" or eventType == "D20SpadeWins" or eventType == "D20HeartWins" or eventType == "D20DiamondWins" or eventType == "D20ClubWins":
        games_curs.execute(f'''SELECT {eventType} FROM RankedDiceStatsLifetimeView WHERE GuildID=? AND UserID=?''', (guildID, userID))
        row = games_curs.fetchone()
    if row:
        userValue = int(row[0])
        for achievement in achievements:
            achievementID = achievement[0]
            targetValue = int(achievement[1])
            flavor = achievement[4] if achievement[4] is not None else "-"
            compareType = achievement[5]
            result=False
            if compareType == "Greater":
                if userValue >= targetValue:
                    result=True
            elif compareType == "Exact":
                if userValue == targetValue:
                    result=True
            elif compareType == "Lesser":
                if userValue <= targetValue:
                    result=True
            if result:
                games_curs.execute('''INSERT INTO UserAchievements (GuildID, UserID, AchievementID) VALUES (?, ?, ?)''', (guildID, userID, achievementID))
                games_conn.commit()
                embed=discord.Embed(title=f"Achievement Unlocked: {achievement[2]}", description=f"{achievement[3]}\n*{flavor}*", color=discord.Color.gold())
                #add the guild name to the embed footer
                guildName=context.bot.get_guild(int(guildID)).name if context.bot.get_guild(int(guildID)) else "Unknown Guild"
                embed.set_footer(text=f"Guild: {guildName} | ID: {guildID}")
                embedList.append(embed)

            
    #DM the user the achievement(s)
    if embedList:
        user = await context.bot.fetch_user(int(userID))
        print(f"bot is: {context.bot}")
        print(f"Sending achievement DM to user {user}")
        try:
            await user.send("Congratulations! You've unlocked the following achievement(s):", embeds=embedList)
        except Exception as e:
            print(f"Failed to send DM to user {user}: {e}")
            logging.warning(f"Failed to send DM to user {user}: {e}")
    games_curs.close()
    games_conn.close()

async def achievement_leaderboard_generator(guildID: str):
    gamesDB = "games.db"
    games_conn = sqlite3.connect(gamesDB)
    games_curs = games_conn.cursor()
    games_curs.execute('''SELECT UserID, TotalScore FROM UserAchievementScoresView WHERE GuildID = ? ORDER BY TotalScore DESC''', (guildID,))
    rows= games_curs.fetchall()
    #and get the total acheivement count for each user
    games_curs.execute('''SELECT UserID, COUNT(*) FROM UserAchievements group by UserID, GuildID HAVING GuildID = ?''', (guildID,))
    user_achievement_counts = dict(games_curs.fetchall())
    outstr=""
    embed=discord.Embed(title="Achievement Score Leaderboard", color=0x228a65)
    for row in rows:
        user=context.bot.get_guild(guildID).get_member(int(row[0]))
        if user:
            outstr += f"<@{user.id}>: {int(row[1])} points\t:trophy: {user_achievement_counts.get(user.id, 0)}\n"
        else:
            outstr += f"User ID {row[0]}: {int(row[1])} points\t:trophy: {user_achievement_counts.get(row[0], 0)}\n"
    embed.description=outstr
    games_curs.close()
    games_conn.close()
    return embed

async def auction_house_command(interaction: discord.Interaction):
    games_conn=sqlite3.connect("games.db",timeout=10)
    games_conn.row_factory = sqlite3.Row
    games_curs=games_conn.cursor()
    games_curs.execute('''INSERT INTO CommandLog (GuildID, UserID, CommandName) VALUES (?, ?, ?)''', (interaction.guild.id, interaction.user.id, "auction-house"))
    games_curs.execute('''SELECT Game1 from GamblingGamesUnlocked where GuildID = ? AND UserID = ?''', (interaction.guild.id, interaction.user.id))
    row = games_curs.fetchone()
    if row is None or row['Game1'] == 0:
        await interaction.response.send_message("You have not unlocked the Auction House game yet. Play more to unlock it!", ephemeral=True)
        games_curs.close()
        games_conn.close()
        return
    games_curs.execute('''SELECT Zone, PercentAuctioned, CurrentPrice, CurrentBidderUserID, CurrentBidderGuildID FROM AuctionHousePrize where Date = ?''', (datetime.now().date(),))
    auction_data = games_curs.fetchall()
    games_conn.commit()
    games_curs.close()
    games_conn.close()
    print(f"DEBUG: auction_data fetched: {len(auction_data)} items")
    #if no auction data found
    if not auction_data:
        await interaction.response.send_message("No auction data found for today. Please try again later.", ephemeral=True)
        return
    AUCTIONINFO={"ZoneInfo": {}}
    for item in auction_data:
        AUCTIONINFO["ZoneInfo"][item['Zone']] = {
            'PercentAuctioned': item['PercentAuctioned'],
            'CurrentPrice': item['CurrentPrice'],
            'CurrentBidderUserID': item['CurrentBidderUserID'],
            'CurrentBidderGuildID': item['CurrentBidderGuildID']
        }
    #print(f"DEBUG: AUCTIONINFO constructed: {AUCTIONINFO}")
    AUCTIONINFO["AuctionList"]= list(AUCTIONINFO["ZoneInfo"].keys())
    #print(f"DEBUG: AUCTIONINFO['AuctionList']: {AUCTIONINFO['AuctionList']}")
    AUCTIONINFO["CurrentAuctionSelected"]=auction_data[0]['Zone']
    #print(f"DEBUG: AUCTIONINFO['CurrentAuctionSelected']: {AUCTIONINFO['CurrentAuctionSelected']}")
    embed = await auction_text_generator(interaction=interaction, AUCTIONINFO=AUCTIONINFO)
    if embed == "exit":
        return
    
    view=discord.ui.View(timeout=None)
    bidButton=OpenBidButton(label="Place a Bid", selected_auction=AUCTIONINFO["CurrentAuctionSelected"])
    refreshButton=RefreshAuctionButton(label="🔄", AUCTIONINFO=AUCTIONINFO)
    plus5Button=SimpleBidButton(label="+5", bid_amount=5, selected_auction=AUCTIONINFO["CurrentAuctionSelected"])
    plus1Button=SimpleBidButton(label="+1", bid_amount=1, selected_auction=AUCTIONINFO["CurrentAuctionSelected"])
    switchAuctionButton=SwitchAuctionButton(label="Switch Auction", AUCTIONINFO=AUCTIONINFO)
    view.add_item(switchAuctionButton)
    view.add_item(bidButton)
    view.add_item(refreshButton)
    view.add_item(plus5Button)
    view.add_item(plus1Button)
    await interaction.response.send_message(embed=embed, ephemeral=True, view=view)


class RefreshAuctionButton(discord.ui.Button):
    def __init__(self, label=None, style=discord.ButtonStyle.primary, AUCTIONINFO=None):
        super().__init__(label=label, style=style)
        self.AUCTIONINFO = AUCTIONINFO

    async def callback(self, interaction: discord.Interaction):
         # 🟩 re-fetch auction data from DB
        games_conn = sqlite3.connect("games.db")
        games_conn.row_factory = sqlite3.Row
        games_curs = games_conn.cursor()
        games_curs.execute('''SELECT Zone, PercentAuctioned, CurrentPrice, CurrentBidderUserID, CurrentBidderGuildID
                              FROM AuctionHousePrize WHERE Date = ?''', (datetime.now().date(),))
        auction_data = games_curs.fetchall()
        print(f"DEBUG: Refreshed auction_data fetched: {len(auction_data)} items")
        games_curs.close()
        games_conn.close()
        AUCTIONINFO={"ZoneInfo": {}}
        for item in auction_data:
            AUCTIONINFO["ZoneInfo"][item['Zone']] = {
                'PercentAuctioned': item['PercentAuctioned'],
                'CurrentPrice': item['CurrentPrice'],
                'CurrentBidderUserID': item['CurrentBidderUserID'],
                'CurrentBidderGuildID': item['CurrentBidderGuildID']
            }
        AUCTIONINFO["AuctionList"]= list(AUCTIONINFO["ZoneInfo"].keys())
        AUCTIONINFO["CurrentAuctionSelected"]=self.AUCTIONINFO["CurrentAuctionSelected"]
        print(f"DEBUG: Refreshed AUCTIONINFO: {AUCTIONINFO}")
        embed = await auction_text_generator(interaction=interaction, AUCTIONINFO=AUCTIONINFO)
        # 🟩 rebuild embed with new data
        # 🟩 update message in place
        view = discord.ui.View(timeout=None)
        view.add_item(SwitchAuctionButton(label="Switch Auction", AUCTIONINFO=AUCTIONINFO))
        view.add_item(OpenBidButton(label="Place a Bid", selected_auction=AUCTIONINFO["CurrentAuctionSelected"]))
        view.add_item(RefreshAuctionButton(label="🔄", AUCTIONINFO=AUCTIONINFO))
        view.add_item(SimpleBidButton(label="+5", bid_amount=5, selected_auction=AUCTIONINFO["CurrentAuctionSelected"]))
        view.add_item(SimpleBidButton(label="+1", bid_amount=1, selected_auction=AUCTIONINFO["CurrentAuctionSelected"]))
        await interaction.response.edit_message(embed=embed, view=view)
        #await interaction.followup.send("✅ Auction info refreshed!", ephemeral=True)  # optional confirmation

class OpenBidButton(discord.ui.Button):
    def __init__(self, label=None, style=discord.ButtonStyle.primary, selected_auction=None):
        super().__init__(label=label, style=style)
        self.selected_auction = selected_auction

    async def callback(self, interaction: discord.Interaction):
        placeABidModal=BidModal(interaction, selected_auction=self.selected_auction)
        await interaction.response.send_modal(placeABidModal)

class BidModal(discord.ui.Modal):
    def __init__(self, interaction: discord.Interaction, selected_auction: str = None):
        super().__init__(title="Place Your Bid")
        self.selected_auction = selected_auction
        games_conn=sqlite3.connect("games.db",timeout=10)
        games_conn.row_factory = sqlite3.Row
        games_curs=games_conn.cursor()
        games_curs.execute('''SELECT CurrentBalance FROM GamblingUserStats WHERE GuildID=? AND UserID=?''', (interaction.guild.id, interaction.user.id))
        currentBalance = games_curs.fetchone()
        self.add_item(discord.ui.TextInput(label=f"Enter bid. Current bal: {currentBalance['CurrentBalance']}", placeholder="Enter your bid amount"))
    async def on_submit(self, interaction: discord.Interaction):
        bid_amount = self.children[0].value
        await placeBid(interaction, bid_amount, selected_auction=self.selected_auction)
        

async def placeBid(interaction: discord.Interaction, bid_amount: int, is_simple_bid: bool = False, selected_auction: str = None):
        games_conn=sqlite3.connect("games.db",timeout=10)
        games_conn.row_factory = sqlite3.Row
        games_curs=games_conn.cursor()
        if selected_auction == "Casino":
            games_curs.execute('''SELECT Game2 from GamblingGamesUnlocked where GuildID = ? AND UserID = ?''', (interaction.guild.id, interaction.user.id))
            row = games_curs.fetchone()
            if row is None or row['Game2'] == 0:
                await interaction.response.send_message("You have not unlocked the Casino auction yet. Play more to unlock it!", ephemeral=True)
                games_curs.close()
                games_conn.close()
                return
        games_curs.execute('''SELECT CurrentBalance FROM GamblingUserStats WHERE GuildID=? AND UserID=?''', (interaction.guild.id, interaction.user.id))
        currentBalance = games_curs.fetchone()
        if not currentBalance or int(bid_amount) > currentBalance['CurrentBalance']:
            await interaction.response.send_message("You do not have enough balance to place that bid.", ephemeral=True)
            games_curs.close()
            games_conn.close()
            return
        #check if the user won an auction yesterday and if so, prevent them from bidding today
        games_curs.execute('''SELECT FinalBidderUserID, FinalBidderGuildID FROM AuctionHousePrize WHERE Date = ?''', (datetime.now().date() - timedelta(days=1),))
        won_auctions = games_curs.fetchall()
        for auction in won_auctions:
            if auction['FinalBidderUserID'] == interaction.user.id and auction['FinalBidderGuildID'] == interaction.guild.id:
                await interaction.response.send_message("You won an auction yesterday and cannot bid today. Please wait until tomorrow to bid again.", ephemeral=True)
                games_curs.close()
                games_conn.close()
                return
        #check if the user is the current highest bidder for other auctions today
        games_curs.execute('''SELECT Zone FROM AuctionHousePrize WHERE Date = ? AND CurrentBidderUserID = ? and CurrentBidderGuildID = ?''', (datetime.now().date(), interaction.user.id, interaction.guild.id))
        current_bids = games_curs.fetchall()
        for bid in current_bids:
            if bid['Zone'] != selected_auction:
                await interaction.response.send_message("You are already the highest bidder for another auction today. You cannot bid on multiple auctions in the same day.", ephemeral=True)
                games_curs.close()
                games_conn.close()
                return
        print(f"DEBUG: selected_auction in placeBid: {selected_auction}")
        games_curs.execute('''SELECT CurrentPrice FROM AuctionHousePrize where Date = ? and Zone = ?''', (datetime.now().date(), selected_auction))
        currentPrice= games_curs.fetchone()
        print(f"DEBUG: currentPrice in placeBid: {currentPrice['CurrentPrice'] if currentPrice else 'None'}")
        if is_simple_bid:
            bid_amount = currentPrice['CurrentPrice'] + bid_amount
        if currentPrice and int(bid_amount) > currentPrice['CurrentPrice']:
            games_curs.execute('''UPDATE AuctionHousePrize SET CurrentPrice = ?, CurrentBidderUserID = ?, CurrentBidderGuildID = ? WHERE Date = ? and Zone = ?''', (int(bid_amount), interaction.user.id, interaction.guild.id, datetime.now().date(), selected_auction))
            games_conn.commit()
            await interaction.response.send_message(f"You placed a bid of {bid_amount}!",ephemeral=True)
        else:
            await interaction.response.send_message(f"Your bid must be higher than the current price of {currentPrice['CurrentPrice']}.", ephemeral=True)
        games_curs.close()
        games_conn.close()


class SimpleBidButton(discord.ui.Button):
    def __init__(self, label=None, style=discord.ButtonStyle.primary, bid_amount=0, selected_auction=None):
        super().__init__(label=label, style=style)
        self.bid_amount = bid_amount
        self.selected_auction = selected_auction

    async def callback(self, interaction: discord.Interaction):
        await placeBid(interaction, self.bid_amount, is_simple_bid=True, selected_auction=self.selected_auction)
        

class SwitchAuctionButton(discord.ui.Button):
    def __init__(self, label=None, style=discord.ButtonStyle.primary, AUCTIONINFO=None):
        super().__init__(label=label, style=style)
        self.AUCTIONINFO = AUCTIONINFO

    async def callback(self, interaction: discord.Interaction):
       #switch the current auction selected to the next one in the list
        current_index = self.AUCTIONINFO["AuctionList"].index(self.AUCTIONINFO["CurrentAuctionSelected"])
        next_index = (current_index + 1) % len(self.AUCTIONINFO["AuctionList"])
        self.AUCTIONINFO["CurrentAuctionSelected"] = self.AUCTIONINFO["AuctionList"][next_index]
        embed = await auction_text_generator(self.AUCTIONINFO, interaction=interaction)
        view=discord.ui.View(timeout=None)
        switchButton=SwitchAuctionButton(label="Switch Auction", AUCTIONINFO=self.AUCTIONINFO)
        bidButton=OpenBidButton(label="Place a Bid", selected_auction=self.AUCTIONINFO["CurrentAuctionSelected"])
        refreshButton=RefreshAuctionButton(label="🔄",AUCTIONINFO=self.AUCTIONINFO)
        plus5Button=SimpleBidButton(label="+5", bid_amount=5, selected_auction=self.AUCTIONINFO["CurrentAuctionSelected"])
        plus1Button=SimpleBidButton(label="+1", bid_amount=1, selected_auction=self.AUCTIONINFO["CurrentAuctionSelected"])
        view.add_item(switchButton)
        view.add_item(bidButton)
        view.add_item(refreshButton)
        view.add_item(plus5Button)
        view.add_item(plus1Button)
        await interaction.response.edit_message(embed=embed, view=view)
        return

async def auction_text_generator(AUCTIONINFO=None, interaction: discord.Interaction=None):
    embed = discord.Embed(title="Auction House", description="Bid on winners!", color=0x228a65)
    if AUCTIONINFO["ZoneInfo"]:
        for zoneName, item in AUCTIONINFO["ZoneInfo"].items():
            userTag=""
            if int(item['CurrentBidderGuildID']) == interaction.guild.id:
                userTag = f"<@{item['CurrentBidderUserID']}>"
            else:
                userTag = f"*a user from another server*"
            if zoneName == AUCTIONINFO["CurrentAuctionSelected"]:
                aucName = f"[{int(item['PercentAuctioned']*100)}% of yesterdays total from {zoneName}]"
                aucValue = f":right_arrow: Current top bid: {item['CurrentPrice']} by {userTag}"
            else:
                aucName = f"{int(item['PercentAuctioned']*100)}% of yesterdays total from {zoneName}"
                aucValue = f"Current top bid: {item['CurrentPrice']} by {userTag}"
            embed.add_field(name=aucName, value=aucValue, inline=False)
    else:
        embed.add_field(name="No auction data available for today.", value="Please check back tomorrow.", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return "exit"
    return embed

class AuctionHouseButton(discord.ui.Button):
    def __init__(self, label=None, style=discord.ButtonStyle.primary):
        super().__init__(label=label, style=style)

    async def callback(self, interaction: discord.Interaction):
        await auction_house_command(interaction)

async def rank_number_to_rank_name(rank_number):
    # Example mapping, adjust as needed
    rank_names = {
        1: "B1",
        2: "B2",
        3: "B3",
        4: "B4",
        5: "B5",
        6: "S1",
        7: "S2",
        8: "S3",
        9: "S4",
        10: "S5",
        11: "G1",
        12: "G2",
        13: "G3",
        14: "G4",
        15: "G5",
        16: "P1",
        17: "P2",
        18: "P3",
        19: "P4",
        20: "P5",
        21: "D1",
        22: "D2",
        23: "D3",
        24: "D4",
        25: "D5",
        26: "D6",
        27: "D7",
        28: "D8",
        29: "D9",
        30: "D10",
        31: "D11",
        32: "D12",
        33: "D13",
        34: "D14",
        35: "D15",
        36: "D16",
        37: "D17",
        38: "D18",
        39: "D19",
        40: "D20",
        # Add more ranks as needed
    }
    return rank_names.get(int(rank_number), "Unranked")