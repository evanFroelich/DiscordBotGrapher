"""Reaction handler for the Discord bot."""
import sqlite3
from utils.database import award_points


async def handle_reaction_add(client, reaction, user):
    """Handle reaction add events."""
    if user.bot:
        return
    gameDB = "games.db"
    game_conn = sqlite3.connect(gameDB)
    game_curs = game_conn.cursor()
    game_curs.execute('''SELECT LastBonusPipMessage FROM FeatureTimers WHERE GuildID=?''', 
                     (reaction.message.guild.id,))
    lastBonusPipMessage = game_curs.fetchone()
    if reaction.emoji == '✅' and lastBonusPipMessage is not None and lastBonusPipMessage[0] == reaction.message.id:
        game_curs.execute('''INSERT INTO Scores ( GuildID, UserID, Category, Difficulty, Num_Correct, Num_Incorrect) VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(GuildID, UserID, Category, Difficulty) DO UPDATE SET Num_Correct = Num_Correct + 1;''', 
                         (reaction.message.guild.id, user.id, 'bonus', 1, 1, 0))
        game_conn.commit()
        await reaction.message.clear_reaction(reaction.emoji)
        game_curs.execute('''UPDATE FeatureTimers SET LastBonusPipMessage=? WHERE GuildID=?''', 
                         (None, reaction.message.guild.id))
        game_conn.commit()
        await award_points(1, reaction.message.guild.id, user.id)
    game_curs.close()
    game_conn.close()

