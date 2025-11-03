"""Database utility functions."""
import sqlite3
from datetime import datetime


async def create_user_db_entry(guildID, userID):
    """Create or verify a user entry in the database."""
    gamesDB = "games.db"
    games_conn = sqlite3.connect(gamesDB)
    games_curs = games_conn.cursor()
    games_curs.execute('''SELECT * FROM GamblingUserStats WHERE GuildID=? AND UserID=?''', (guildID, userID))
    user_stats = games_curs.fetchone()
    if not user_stats:
        games_curs.execute('''INSERT INTO GamblingUserStats (GuildID, UserID) VALUES (?, ?)''', (guildID, userID))
        games_conn.commit()
    games_curs.close()
    games_conn.close()


async def create_guild_db_entry(guildID):
    """Create default guild entries in the database."""
    db_name = "My_DB"
    conn = sqlite3.connect(db_name)
    curs = conn.cursor()
    curs.execute('''INSERT OR IGNORE INTO ServerSettings (GuildID) VALUES (?);''', (guildID,))
    conn.commit()
    curs.close()
    conn.close()

    gamesDB = "games.db"
    games_conn = sqlite3.connect(gamesDB)
    games_curs = games_conn.cursor()
    games_curs.execute('''INSERT INTO GamblingUnlockConditions (GuildID, Game1Condition1, Game1Condition2, Game1Condition3, Game2Condition1, Game2Condition2, Game2Condition3) values (?, ?, ?, ?, ?, ?, ?)''', 
                      (guildID, 500, 15, 3, 2000, 500, 3))
    games_curs.execute('''INSERT INTO ServerSettings (GuildID) VALUES (?)''', (guildID,))
    games_conn.commit()
    games_curs.close()
    games_conn.close()


async def award_points(amount, guild_id, user_id):
    """Award points to a user."""
    gamesDB = "games.db"
    games_conn = sqlite3.connect(gamesDB)
    games_curs = games_conn.cursor()
    games_curs.execute('''UPDATE GamblingUserStats SET CurrentBalance = CurrentBalance + ? WHERE GuildID=? AND UserID=?;''', 
                      (amount, guild_id, user_id))
    if amount > 0:
        games_curs.execute('''UPDATE GamblingUserStats SET LifetimeEarnings = LifetimeEarnings + ? WHERE GuildID=? AND UserID=?;''', 
                          (amount, guild_id, user_id))
    games_conn.commit()
    games_curs.close()
    games_conn.close()


async def resetDailyQuestionCorrect(guildID, userID):
    """Reset daily question count for a user if it's a new day."""
    gamesDB = "games.db"
    games_conn = sqlite3.connect(gamesDB)
    games_curs = games_conn.cursor()

    curTime = datetime.now()
    games_curs.execute('''SELECT LastRandomQuestionTime FROM GamblingUserStats WHERE GuildID=? AND UserID=?''', (guildID, userID))
    last_random_question_time = games_curs.fetchone()[0]
    
    games_curs.execute('''SELECT LastDailyQuestionTime FROM GamblingUserStats WHERE GuildID=? AND UserID=?''', (guildID, userID))
    last_daily_question_time = games_curs.fetchone()[0]
    
    if last_random_question_time is not None and last_daily_question_time is not None:
        LRQT = datetime.strptime(last_random_question_time, '%Y-%m-%d %H:%M:%S')
        LDQT = datetime.strptime(last_daily_question_time, '%Y-%m-%d %H:%M:%S') 
        if LRQT.date() != curTime.date() and LDQT.date() != curTime.date():
            games_curs.execute('''UPDATE GamblingUserStats SET QuestionsAnsweredTodayCorrect = 0, QuestionsAnsweredToday = 0 WHERE GuildID=? AND UserID=?''', 
                             (guildID, userID))
    elif last_random_question_time is not None:
        LRQT = datetime.strptime(last_random_question_time, '%Y-%m-%d %H:%M:%S')
        if LRQT.date() != curTime.date():
            games_curs.execute('''UPDATE GamblingUserStats SET QuestionsAnsweredTodayCorrect = 0, QuestionsAnsweredToday = 0 WHERE GuildID=? AND UserID=?''', 
                             (guildID, userID))
    elif last_daily_question_time is not None:
        LDQT = datetime.strptime(last_daily_question_time, '%Y-%m-%d %H:%M:%S')
        if LDQT.date() != curTime.date():
            games_curs.execute('''UPDATE GamblingUserStats SET QuestionsAnsweredTodayCorrect = 0, QuestionsAnsweredToday = 0 WHERE GuildID=? AND UserID=?''', 
                             (guildID, userID))
    games_conn.commit()
    games_curs.close()
    games_conn.close()


async def createTimers(GuildID):
    """Create timer entries for a guild."""
    gameDB = "games.db"
    games_conn = sqlite3.connect(gameDB)
    games_curs = games_conn.cursor()
    games_curs.execute('''INSERT OR IGNORE INTO FeatureTimers(GuildID) VALUES (?)''', (GuildID,))
    games_conn.commit()
    games_curs.close()
    games_conn.close()


async def checkIgnoredChannels(channelID: str, guildID: str) -> bool:
    """Check if a channel is ignored."""
    import json
    channelID_str = str(channelID)
    gameDB = "games.db"
    games_conn = sqlite3.connect(gameDB)
    games_curs = games_conn.cursor()
    games_curs.execute('''SELECT IgnoredChannels FROM ServerSettings WHERE GuildID=?''', (guildID,))
    ignoredchannels = games_curs.fetchone()
    channelList = []
    if ignoredchannels is not None and ignoredchannels[0] is not None:
        channelList = json.loads(ignoredchannels[0])
    games_conn.close()

    if channelID_str in channelList:
        return True
    return False


async def delete_later(message, time):
    """Delete a message after a delay."""
    import asyncio
    import sqlite3
    await asyncio.sleep(time)
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

