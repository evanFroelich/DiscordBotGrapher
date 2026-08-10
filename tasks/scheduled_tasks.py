"""Scheduled tasks for the Discord bot."""
import sqlite3
import discord
from discord.ext import tasks
from datetime import datetime, timedelta, time
import zoneinfo
import random
from utils.database import award_points


@tasks.loop(time=time(hour=23, minute=55, second=0, tzinfo=zoneinfo.ZoneInfo("America/Los_Angeles")))
async def daily_question_leaderboard():
    """Daily question leaderboard task."""
    if not _client:
        return
    games_conn = sqlite3.connect("games.db")
    games_curs = games_conn.cursor()
    games_curs.execute('''SELECT GuildID, FlagShameChannel, ShameChannel from ServerSettings''')
    guilds = games_curs.fetchall()
    for guildID in guilds:
        if guildID[1] == 1 and guildID[2]:
            games_curs.execute('''SELECT UserID, QuestionsAnsweredTodayCorrect FROM GamblingUserStats WHERE GuildID = ? and (date(LastDailyQuestionTime) = date('now', 'localtime') OR date(LastRandomQuestionTime) = date('now', 'localtime')) order by QuestionsAnsweredTodayCorrect desc''', (guildID[0],))
            leaderboardResults = games_curs.fetchall()
            todaysDate = datetime.now().date()
            embed = discord.Embed(title=f"Daily Question Leaderboard for {todaysDate}", description="", color=0x00ff00)
            printstr = f"**Daily Question Leaderboard for {todaysDate}**\n\n"
            if leaderboardResults:
                for userID, questionsAnswered in leaderboardResults:
                    embed.description += f"<@{userID}>: {questionsAnswered} correct answers today.\n"
                    printstr += f"<@{userID}>: {questionsAnswered} correct answers today.\n"
            channel = _client.get_channel(guildID[2])
            if channel:
                await channel.send(content=printstr)
    games_curs.close()
    games_conn.close()


@tasks.loop(time=time(hour=0, minute=2, second=0, tzinfo=zoneinfo.ZoneInfo("America/Los_Angeles")))
async def package_daily_gambling():
    """Package daily gambling totals for auction house."""
    if not _client:
        return
    print("Packaging daily gambling totals for auction house...")
    games_conn = sqlite3.connect("games.db")
    games_conn.row_factory = sqlite3.Row
    games_curs = games_conn.cursor()
    today = datetime.now().date()
    rollOverFlag = 0
    rollOverAmount = 0
    games_curs.execute('''select * from AuctionHousePrize where Date=?''', (today - timedelta(days=1),))
    yesterday_auction_data = games_curs.fetchall()
    if yesterday_auction_data:
        for row in yesterday_auction_data:
            games_curs.execute('''select CurrentBalance from GamblingUserStats where GuildID=? and UserID=?''', (row['CurrentBidderGuildID'], row['CurrentBidderUserID']))
            bidder_balance = games_curs.fetchone()
            if bidder_balance and bidder_balance[0] >= row['CurrentPrice']:
                if int(row['AmountAuctioned'])-int(row['CurrentPrice']) > 0:
                    games_curs.execute('''Update GamblingUserStats SET AuctionHouseWinnings = AuctionHouseWinnings + ? WHERE GuildID=? AND UserID=?''', (int(row['AmountAuctioned'])-int(row['CurrentPrice']), row['CurrentBidderGuildID'], row['CurrentBidderUserID']))
                else:
                    games_curs.execute('''Update GamblingUserStats SET AuctionHouseLosses = AuctionHouseLosses + ? WHERE GuildID=? AND UserID=?''', (int(row['CurrentPrice'])-int(row['AmountAuctioned']), row['CurrentBidderGuildID'], row['CurrentBidderUserID']))
                games_conn.commit()
                await award_points(-row['CurrentPrice'], row['CurrentBidderGuildID'], row['CurrentBidderUserID'])
                await award_points(int(row['AmountAuctioned']), row['CurrentBidderGuildID'], row['CurrentBidderUserID'])
                games_curs.execute('''UPDATE AuctionHousePrize SET HasBeenCleared=1, FinalBidderGuildId = ?, FinalBidderUserId = ? WHERE Date=? AND Zone=?''', (row['CurrentBidderGuildID'], row['CurrentBidderUserID'], today - timedelta(days=1), row['Zone']))
                games_conn.commit()
                guild = _client.get_guild(row['CurrentBidderGuildID'])
                if guild:
                    user = guild.get_member(row['CurrentBidderUserID'])
                    if user:
                        try:
                            await user.send(f"Congratulations! You won the auction for {row['Zone']} with a bid of {row['CurrentPrice']} points. You have been awarded {int(row['AmountAuctioned'])} points, resulting in a net gain of {int(row['AmountAuctioned']) - row['CurrentPrice']} points.")
                        except Exception as e:
                            print(f"Failed to send DM to user {row['FinalBidderUserID']}: {e}")
            else:
                rollOverFlag = 1
                rollOverAmount += row['AmountAuctioned']
    games_curs.execute('''SELECT Category, sum(Funds) from DailyGamblingTotals where Date=date('now', '-1 day', 'localtime') group by Category''')
    yesterday_totals = games_curs.fetchall()
    
    for row in yesterday_totals:
        random_multiplier = random.random()
        random_multiplier = (random_multiplier*.1)+.05
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


@tasks.loop(minutes=5)
async def cleanup_abandoned_trivia_loop():
    """Cleanup abandoned trivia sessions."""
    from handlers.message_handler import abandoned_trivia_cleanup
    games_conn = sqlite3.connect("games.db")
    games_curs = games_conn.cursor()
    games_curs.execute('''SELECT * FROM ActiveTrivia WHERE Timestamp < ?''', (datetime.now() - timedelta(minutes=5),))
    abandoned_sessions = games_curs.fetchall()
    games_conn.commit()
    games_curs.close()
    games_conn.close()
    for session in abandoned_sessions:
        guildID, userID, messageID, questionID, questionType, questionDifficulty, questionText = session[0], session[1], session[2], session[3], session[4], session[5], session[6]
        await abandoned_trivia_cleanup(guildID, userID, messageID, questionID, questionType, questionDifficulty, questionText)
    return

