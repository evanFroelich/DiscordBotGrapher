import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import json
import matplotlib.pyplot as plt

from Helpers.Helpers import isAuthorized, rank_number_to_rank_name

class News(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    @app_commands.command(name="news", description="Displays the recent news")
    async def news(self, interaction: discord.Interaction):
        # Fetch news from a news API or database
        gamesDB="games.db"
        games_conn = sqlite3.connect(gamesDB)
        games_curs = games_conn.cursor()
        games_curs.execute('''INSERT INTO CommandLog (GuildID, UserID, CommandName) VALUES (?, ?, ?)''', (interaction.guild.id, interaction.user.id, "news"))
        games_conn.commit()
        #only pull news that was from today or earlier
        games_curs.execute('''SELECT Date, Notes, Headline from NewsFeed WHERE Date <= date('now') order by Date desc Limit 3''')
        rows = games_curs.fetchall()
        embed = discord.Embed(title="Recent News", color=discord.Color.blue())
        for row in rows:
            embed.add_field(name=f"{row[0]}: {row[2]}", value=row[1], inline=False)
        view = discord.ui.View()
        next_button = NewsPageButton(label="Next", page_number=2)
        view.add_item(next_button)
        await interaction.response.send_message(embed=embed, ephemeral=True, view=view)
        games_curs.close()
        games_conn.close()

class NewsPageButton(discord.ui.Button):
    def __init__(self, label=None, page_number=1):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.page_number = page_number

    async def callback(self, interaction: discord.Interaction):
        gamesDB="games.db"
        games_conn = sqlite3.connect(gamesDB)
        games_curs = games_conn.cursor()
        offset = (self.page_number - 1) * 3
        games_curs.execute('''SELECT Date, Notes, Headline from NewsFeed order by Date desc Limit 3 OFFSET ?''', (offset,))
        rows = games_curs.fetchall()
        embed = discord.Embed(title="Recent News", color=discord.Color.blue())
        for row in rows:
            embed.add_field(name=f"{row[0]}: {row[2]}", value=row[1], inline=False)
        view = discord.ui.View()
        if self.page_number > 1:
            prev_button = NewsPageButton(label="Previous", page_number=self.page_number - 1)
            view.add_item(prev_button)
        # Check if there are more news items for the next page
        games_curs.execute('''SELECT COUNT(*) FROM NewsFeed''')
        total_news = games_curs.fetchone()[0]
        if offset + 3 < total_news:
            next_button = NewsPageButton(label="Next", page_number=self.page_number + 1)
            view.add_item(next_button)
        await interaction.response.edit_message(embed=embed, view=view)
        games_curs.close()
        games_conn.close()

class Inventory(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    @app_commands.command(name="inventory", description="Displays the user's inventory")
    async def inventory(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        guild_id = interaction.guild.id

        # Fetch the user's inventory from the database
        gamesDB="games.db"
        games_conn = sqlite3.connect(gamesDB)   
        games_curs = games_conn.cursor()
        games_curs.execute('''INSERT INTO CommandLog (GuildID, UserID, CommandName) VALUES (?, ?, ?)''', (interaction.guild.id, interaction.user.id, "inventory"))
        games_conn.commit()
        games_curs.execute('''SELECT CurrentBalance, RankedDiceTokens FROM GamblingUserStats WHERE GuildID=? AND UserID=?''', (guild_id, user_id))
        current_balance = games_curs.fetchone()
        games_curs.execute('''SELECT Phrase from UserCasinoPassPhrases WHERE GuildID=? AND UserID=?''', (guild_id, user_id))
        passphrase = games_curs.fetchone()
        embed = discord.Embed(title=f"---WIP---\n{interaction.user.name}'s Inventory", color=discord.Color.green())
        if current_balance:
            embed.add_field(name="Current Balance", value=current_balance[0], inline=False)
            embed.add_field(name="Ranked Dice Tokens", value=current_balance[1], inline=False)
        else:
            embed.add_field(name="Current Balance", value="No balance information available.", inline=False)
        if passphrase:
            embed.add_field(name="Casino Passphrase", value=passphrase[0], inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class Stats(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    @app_commands.command(name="stats", description="Displays your personal stats from this server")
    @app_commands.choices(visibility=[
        app_commands.Choice(name="Private", value="private"),
        app_commands.Choice(name="Public", value="public")
    ])
    async def stats(self, interaction: discord.Interaction, visibility: app_commands.Choice[str]):
        user_id = interaction.user.id
        guild_id = interaction.guild.id

        # Fetch the user's stats from the database
        gamesDB="games.db"
        games_conn = sqlite3.connect(gamesDB)   
        games_conn.row_factory = sqlite3.Row
        games_curs = games_conn.cursor()
        games_curs.execute('''INSERT INTO CommandLog (GuildID, UserID, CommandName, CommandParameters) VALUES (?, ?, ?, ?)''', (interaction.guild.id, interaction.user.id, "stats", f"visibility: {visibility.value}"))
        games_conn.commit()
        games_curs.execute('''SELECT * FROM UserStats WHERE GuildID=? AND UserID=?''', (guild_id, user_id))
        user_stats = games_curs.fetchone()
        games_curs.execute('''SELECT * FROM UserStatsGeneralView WHERE GuildID=? AND UserID=?''', (guild_id, user_id))
        general_stats = games_curs.fetchone()
        games_curs.execute('''SELECT CommandName, CommandCount FROM UserStatsCommandView WHERE GuildID=? AND UserID=? Order by CommandCount desc''', (guild_id, user_id))
        command_stats = games_curs.fetchall()
        games_curs.execute('''SELECT AuctionHouseWinnings, AuctionHouseLosses FROM GamblingUserStats WHERE GuildID=? AND UserID=?''', (guild_id, user_id))
        auction_stats = games_curs.fetchone()
        games_curs.execute('''SELECT CoinFlipWins, CoinFlipEarnings, CoinFlipDoubleWins FROM GamblingUserStats WHERE GuildID=? AND UserID=?''', (guild_id, user_id))
        coin_flip_stats = games_curs.fetchone()
        games_curs.execute('''SELECT BlackJackWins, BlackJackEarnings, Blackjack21s FROM GamblingUserStats WHERE GuildID=? AND UserID=?''', (guild_id, user_id))
        black_jack_stats = games_curs.fetchone()
        games_curs.execute('''SELECT * FROM GamblingGamesUnlocked WHERE GuildID=? AND UserID=?''', (guild_id, user_id))
        unlocked_games = games_curs.fetchone()
        games_curs.execute('''SELECT TotalScore FROM UserAchievementScoresView WHERE GuildID=? AND UserID=?''', (guild_id, user_id))
        achievement_score = games_curs.fetchone()
        games_curs.execute('''with Names as (select ID, Name from AchievementDefinitions), OwnedAchievements as (select AchievementID, GuildID, UserID from UserAchievements), achievement_scores as (select AchievementID, Score, Earners from DynamicAchievementScoresView) select a.Name, c.Earners, c.Score from Names a left join OwnedAchievements b on a.ID = b.AchievementID left join achievement_scores c on c.AchievementID = b.AchievementID where b.UserID = ? and b.GuildID = ? order by c.Score DESC limit 3''', (user_id, guild_id))
        top_achievements = games_curs.fetchall()
        games_curs.execute('''SELECT GamesPlayed, WinCount, LossCount, CAST(WinCount AS FLOAT) / (WinCount + LossCount) * 100 as WinRate, Rank, ProvisionalGames FROM PlayerSkill WHERE GuildID=? AND UserID=?''', (guild_id, user_id))
        player_skill = games_curs.fetchone()
        games_curs.execute('''SELECT
            a.Modifier,
            SUM(CASE WHEN a.EndSkillMu > a.StartingSkillMu THEN 1 ELSE 0 END) AS Wins,
            SUM(CASE WHEN a.EndSkillMu < a.StartingSkillMu THEN 1 ELSE 0 END) AS Losses,
            CAST(SUM(CASE WHEN a.EndSkillMu > a.StartingSkillMu THEN 1 ELSE 0 END) AS FLOAT) / CAST(COUNT(*)  AS FLOAT) * 100 AS WinRate
        FROM LiveRankedDicePlayers a
        INNER JOIN LiveRankedDiceMatches m
            ON a.MatchID = m.ID
        WHERE a.UserID = ?
        AND m.GuildID = ?
        GROUP BY a.Modifier
        ORDER BY WinRate DESC;''', (user_id, guild_id))
        modifier_stats = games_curs.fetchall()
        games_curs.close()
        games_conn.close()
        embed = discord.Embed(title=f"---WIP---\n{interaction.user.name}'s Stats", color=discord.Color.green())
        if top_achievements:
            achievementStr=""
            for achievement in top_achievements:
                achievementStr += f"({achievement['Earners']}) {achievement['Name']}\n"
            embed.add_field(name="Top Achievements", value=achievementStr, inline=True)
        
        if player_skill:
            rankText=""
            if player_skill['ProvisionalGames'] == 0:
                textRank = await rank_number_to_rank_name(player_skill['Rank'])
                rankText = f"{textRank}"
            else:
                rankText = f"{10-player_skill['ProvisionalGames']}/10 placements"
            embed.add_field(name="Ranked Dice Stats", value=f"Rank: {rankText}\nGames Played: {player_skill['GamesPlayed']}\nWins: {player_skill['WinCount']}\nLosses: {player_skill['LossCount']}\nWin Rate: {round(player_skill['WinRate'],2)}%", inline=True)
        if modifier_stats and visibility.value == "private":
            modifierStr=""
            for modifier in modifier_stats:
                modifierStr += f"{modifier['Modifier']}: W: {modifier['Wins']} L: {modifier['Losses']} WR: {int(modifier['WinRate'])}%\n"
            embed.add_field(name="Ranked Dice Modifier Stats", value=modifierStr, inline=True)
        if achievement_score:
            embed.add_field(name="Achievement Score", value=achievement_score['TotalScore'], inline=False)
        if user_stats:
            embed.add_field(name="Ping Responses", value=f"Pong:{user_stats['PingPongCount']}\nSong: {user_stats['PingSongCount']}\nDong: {user_stats['PingDongCount']}\nLong: {user_stats['PingLongCount']}\nKong: {user_stats['PingKongCount']}\nGoldStar: {user_stats['PingGoldStarCount']}", inline=False)
            #divide hits and misses to get a percent rounded to the whole number. if miss is 0 then default to 100%
            hitRate=0
            if user_stats['HorseMissCount'] == 0:
                if user_stats['HorseHitCount'] == 0:
                    hitRate = "N/A"
                else:
                    hitRate = 100
            else:
                hitRate = round(user_stats['HorseHitCount'] / (user_stats['HorseHitCount'] + user_stats['HorseMissCount']) * 100)
            embed.add_field(name="Horse Stats", value=f"Times hit: {user_stats['HorseHitCount']}\tHit Rate: {hitRate}%", inline=True)
            if user_stats['CatMissCount'] == 0:
                if user_stats['CatHitCount'] == 0:
                    hitRate = "N/A"
                else:
                    hitRate = 100
            else:
                hitRate = round(user_stats['CatHitCount'] / (user_stats['CatHitCount'] + user_stats['CatMissCount']) * 100)
            embed.add_field(name="Cat Stats", value=f"Times hit: {user_stats['CatHitCount']}\tHit Rate: {hitRate}%", inline=True)
            if user_stats['MarathonMissCount'] == 0:
                if user_stats['MarathonHitCount'] == 0:
                    hitRate = "N/A"
                else:
                    hitRate = 100
            else:
                hitRate = round(user_stats['MarathonHitCount'] / (user_stats['MarathonHitCount'] + user_stats['MarathonMissCount']) * 100)
            embed.add_field(name="Marathon Stats", value=f"Times hit: {user_stats['MarathonHitCount']}\tHit Rate: {hitRate}%", inline=True)
            if user_stats['TwitterAltMissCount'] == 0:
                if user_stats['TwitterAltHitCount'] == 0:
                    hitRate = "N/A"
                else:
                    hitRate = 100
            else:
                hitRate = round(user_stats['TwitterAltHitCount'] / (user_stats['TwitterAltHitCount'] + user_stats['TwitterAltMissCount']) * 100)
            if user_stats['TwitterAltHitCount'] != 0 or user_stats['TwitterAltMissCount'] != 0:
                embed.add_field(name="Twitter Alt Stats", value=f"Times hit: {user_stats['TwitterAltHitCount']}\tHit Rate: {hitRate}%", inline=False)
            if general_stats:
                embed.add_field(name="Trivia stats", value=f"Questions Answered: {general_stats['TriviaCount']}\nLifetime Earnings: {general_stats['LifetimeEarnings']}\nCurrent Balance: {general_stats['CurrentBalance']}\nTips Given: {general_stats['TipsGiven']}", inline=True)
                if coin_flip_stats and visibility.value == "private":
                    if unlocked_games:
                        if int(unlocked_games['Game1'])==1:
                            embed.add_field(name="Gambling Coin Flip Stats", value=f"Wins: {coin_flip_stats['CoinFlipWins']}\nEarnings: {coin_flip_stats['CoinFlipEarnings']}\nDouble Wins: {coin_flip_stats['CoinFlipDoubleWins']}", inline=True)
                else:
                    embed.add_field(name="\u200b", value="\u200b", inline=True)
                if black_jack_stats and visibility.value == "private":
                    if unlocked_games:
                        if int(unlocked_games['Game2'])==1:
                            embed.add_field(name="Gambling Black Jack Stats", value=f"Wins: {black_jack_stats['BlackJackWins']}\nEarnings: {black_jack_stats['BlackJackEarnings']}\n21's hit: {black_jack_stats['Blackjack21s']}", inline=True)
                else:
                    embed.add_field(name="\u200b", value="\u200b", inline=True)
                commandStr=""
                for command in command_stats:
                    commandStr += f"{command['CommandName']}: {command['CommandCount']}\n"
                embed.add_field(name=f"Total Commands Used: {general_stats['TotalCommands']}",value=f"{commandStr}", inline=True)
                if auction_stats:
                    if unlocked_games:
                        if int(unlocked_games['Game1'])==1:
                            embed.add_field(name="Auction House Stats", value=f"Winnings: {auction_stats['AuctionHouseWinnings']}\nLosses: {auction_stats['AuctionHouseLosses']}", inline=True)
                embed.add_field(name="Coin Flip Stats", value=f"Times Flipped: {general_stats['TimesFlipped']}\nCurrent Streak: {general_stats['CurrentStreak']}\nLast Flipped: {general_stats['LastFlip']}", inline=True)
                

        else:
            embed.add_field(name="Stats", value="No stats information available.", inline=False)
        visibility = "Public" if visibility.value == "public" else "Private"
        await interaction.response.send_message(embed=embed, ephemeral=visibility == "Private")

class RankedDiceStats(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    @app_commands.command(name="ranked-dice-stats", description="Displays your ranked dice stats")
    async def ranked_dice_stats(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        # Implementation for ranked dice stats command
        games_conn=sqlite3.connect("games.db",timeout=10)
        games_conn.row_factory = sqlite3.Row
        games_curs = games_conn.cursor()
        games_curs.execute('''INSERT INTO CommandLog (GuildID, UserID, CommandName) VALUES (?, ?, ?)''', (interaction.guild.id, interaction.user.id, "ranked-dice-stats"))
        games_conn.commit()
        games_curs.close()
        games_conn.close()
        await ranked_dice_stats_helper(interaction, season="lifetime")
        

async def ranked_dice_stats_helper(interaction: discord.Interaction, season: str="lifetime", new: bool=True):
    games_conn=sqlite3.connect("games.db",timeout=10)
    games_conn.row_factory = sqlite3.Row
    games_curs = games_conn.cursor()
    if season == "lifetime":
        games_curs.execute('''SELECT * FROM RankedDiceStatsLifetimeView WHERE GuildID=? AND UserID=?''', (interaction.guild.id, interaction.user.id))
    if season.__contains__("season"):
        season_number = int(season.replace("season","").strip())
        games_curs.execute('''SELECT * FROM RankedDiceStatsSeasonView WHERE GuildID=? AND UserID=? and Season=?''', (interaction.guild.id, interaction.user.id, season_number))
    row = games_curs.fetchone()
    games_curs.close()
    games_conn.close()
    embed = discord.Embed(title=f"Ranked dice stats {season}", color=discord.Color.purple())
    #--General Stats
    Generalstr=f"W: {row['WinsGeneral']} L: {row['LossesGeneral']} WR: {round(row['WRGeneral']) if row['WRGeneral'] is not None else 0}%\n♠️: W: {row['WinsSpade']} L: {row['LossesSpade']} WR: {round(row['WRSpade']) if row['WRSpade'] is not None else 0}%\n♦️: W: {row['WinsDiamond']} L: {row['LossesDiamond']} WR: {round(row['WRDiamond']) if row['WRDiamond'] is not None else 0}%\n♣️: W: {row['WinsClub']} L: {row['LossesClub']} WR: {round(row['WRClub']) if row['WRClub'] is not None else 0}%\n♥️: W: {row['WinsHeart']} L: {row['LossesHeart']} WR: {round(row['WRHeart']) if row['WRHeart'] is not None else 0}%\n🃏: W: {row['WinsJoker']} L: {row['LossesJoker']} WR: {round(row['WRJoker']) if row['WRJoker'] is not None else 0}%\n"
    embed.add_field(name="General Stats", value=Generalstr, inline=True)
    #--D20 stats
    D20str=f"Wins: {row['D20Wins']}\n♠️ Wins: {row['D20SpadeWins']}\n♦️ Wins: {row['D20DiamondWins']}\n♣️ Wins: {row['D20ClubWins']}\n♥️ Wins: {row['D20HeartWins']}\n🃏 Wins: {row['D20JokerWins']}"
    embed.add_field(name="D20 Stats", value=D20str, inline=True)

    #embed.add_field(name="\u200b", value="\u200b", inline=False)

    


    #--1v1 Stats
    #embed.add_field(name="\u200b", value="\u200b", inline=True)
    lobbystr=f"Wins 1v1: {row['Wins1v1']}\nWins small lobby: {row['WinsSmallLobby']}\nWins large lobby: {row['WinsLargeLobby']}\nFirst places 1v1: {row['FirstPlaceFinishes1v1']}\nFirst places small lobby: {row['FirstPlaceFinishesSmallLobby']}\nFirst places large lobby: {row['FirstPlaceFinishesLargeLobby']}\n"
    embed.add_field(name="Lobby size stats", value=lobbystr, inline=True)

    #embed.add_field(name="\u200b", value="\u200b", inline=False)

    #--Spade Stats
    spadestr=f'''First Places: {row['FirstPlaceFinishesSpade']}
    Perfect Rolls: {row['PerfectRollSpade']}
    Min Rolls: {row['MinRollSpade']}
    Avg fin: {round(row['AveragePositionSpade']) if row['AveragePositionSpade'] is not None else "N/A"}
    Avg fin 1v1: {round(row['AveragePosition1v1Spade']) if row['AveragePosition1v1Spade'] is not None else "N/A"}
    Avg fin small lobby: {round(row['AveragePositionSmallLobbySpade']) if row['AveragePositionSmallLobbySpade'] is not None else "N/A"}
    Avg fin large lobby: {round(row['AveragePositionLargeLobbySpade']) if row['AveragePositionLargeLobbySpade'] is not None else "N/A"}
    WR 1v1: {round(row['WR1v1Spade']) if row['WR1v1Spade'] is not None else "N/A"}%
    WR small lobby: {round(row['WRSmallLobbySpade']) if row['WRSmallLobbySpade'] is not None else "N/A"}%
    WR large lobby: {round(row['WRLargeLobbySpade']) if row['WRLargeLobbySpade'] is not None else "N/A"}%'''
    embed.add_field(name="♠️ Spade Stats", value=spadestr, inline=True)



    #--Diamond Stats
    diamondstr=f'''First Places: {row['FirstPlaceFinishesDiamond']}
    Perfect Rolls: {row['PerfectRollDiamond']}
    Min Rolls: {row['MinRollDiamond']}
    Avg fin: {round(row['AveragePositionDiamond']) if row['AveragePositionDiamond'] is not None else "N/A"}
    Avg fin 1v1: {round(row['AveragePosition1v1Diamond']) if row['AveragePosition1v1Diamond'] is not None else "N/A"}
    Avg fin small lobby: {round(row['AveragePositionSmallLobbyDiamond']) if row['AveragePositionSmallLobbyDiamond'] is not None else "N/A"}
    Avg fin large lobby: {round(row['AveragePositionLargeLobbyDiamond']) if row['AveragePositionLargeLobbyDiamond'] is not None else "N/A"}
    WR 1v1: {round(row['WR1v1Diamond']) if row['WR1v1Diamond'] is not None else "N/A"}%
    WR small lobby: {round(row['WRSmallLobbyDiamond']) if row['WRSmallLobbyDiamond'] is not None else "N/A"}%
    WR large lobby: {round(row['WRLargeLobbyDiamond']) if row['WRLargeLobbyDiamond'] is not None else "N/A"}%'''
    embed.add_field(name="♦️ Diamond Stats", value=diamondstr, inline=True)

    #embed.add_field(name="\u200b", value="\u200b", inline=True)
    #embed.add_field(name="\u200b", value="\u200b", inline=False)

    #--Joker Stats
    jokerstr=f'''First Places: {row['FirstPlaceFinishesJoker']}
    Perfect Rolls: {row['PerfectRollJoker']}
    Min Rolls: {row['MinRollJoker']}
    Avg fin: {round(row['AveragePositionJoker']) if row['AveragePositionJoker'] is not None else "N/A"}
    Avg fin 1v1: {round(row['AveragePosition1v1Joker']) if row['AveragePosition1v1Joker'] is not None else "N/A"}
    Avg fin small lobby: {round(row['AveragePositionSmallLobbyJoker']) if row['AveragePositionSmallLobbyJoker'] is not None else "N/A"}
    Avg fin large lobby: {round(row['AveragePositionLargeLobbyJoker']) if row['AveragePositionLargeLobbyJoker'] is not None else "N/A"}
    WR 1v1: {round(row['WR1v1Joker']) if row['WR1v1Joker'] is not None else "N/A"}%
    WR small lobby: {round(row['WRSmallLobbyJoker']) if row['WRSmallLobbyJoker'] is not None else "N/A"}%
    WR large lobby: {round(row['WRLargeLobbyJoker']) if row['WRLargeLobbyJoker'] is not None else "N/A"}%'''
    embed.add_field(name="🃏 Joker Stats", value=jokerstr, inline=True)

    #--Club Stats
    clubstr=f'''First Places: {row['FirstPlaceFinishesClub']}
    Perfect Rolls: {row['PerfectRollClub']}
    Min Rolls: {row['MinRollClub']}
    Avg fin: {round(row['AveragePositionClub']) if row['AveragePositionClub'] is not None else "N/A"}
    Avg fin 1v1: {round(row['AveragePosition1v1Club']) if row['AveragePosition1v1Club'] is not None else "N/A"}
    Avg fin small lobby: {round(row['AveragePositionSmallLobbyClub']) if row['AveragePositionSmallLobbyClub'] is not None else "N/A"}
    Avg fin large lobby: {round(row['AveragePositionLargeLobbyClub']) if row['AveragePositionLargeLobbyClub'] is not None else "N/A"}
    WR 1v1: {round(row['WR1v1Club']) if row['WR1v1Club'] is not None else "N/A"}%
    WR small lobby: {round(row['WRSmallLobbyClub']) if row['WRSmallLobbyClub'] is not None else "N/A"}%
    WR large lobby: {round(row['WRLargeLobbyClub']) if row['WRLargeLobbyClub'] is not None else "N/A"}%'''
    embed.add_field(name="♣️ Club Stats", value=clubstr, inline=True)

    #--Heart Stats
    heartstr=f'''First Places: {row['FirstPlaceFinishesHeart']}
    Perfect Rolls: {row['PerfectRollHeart']}
    Min Rolls: {row['MinRollHeart']}
    Avg fin: {round(row['AveragePositionHeart']) if row['AveragePositionHeart'] is not None else "N/A"}
    Avg fin 1v1: {round(row['AveragePosition1v1Heart']) if row['AveragePosition1v1Heart'] is not None else "N/A"}
    Avg fin small lobby: {round(row['AveragePositionSmallLobbyHeart']) if row['AveragePositionSmallLobbyHeart'] is not None else "N/A"}
    Avg fin large lobby: {round(row['AveragePositionLargeLobbyHeart']) if row['AveragePositionLargeLobbyHeart'] is not None else "N/A"}
    WR 1v1: {round(row['WR1v1Heart']) if row['WR1v1Heart'] is not None else "N/A"}%
    WR small lobby: {round(row['WRSmallLobbyHeart']) if row['WRSmallLobbyHeart'] is not None else "N/A"}%
    WR large lobby: {round(row['WRLargeLobbyHeart']) if row['WRLargeLobbyHeart'] is not None else "N/A"}%'''
    embed.add_field(name="♥️ Heart Stats", value=heartstr, inline=True)

    embed.add_field(name="\u200b", value="\u200b", inline=True)
    outstr = ""
    outList=[]
    count = 0
    if row:
        for column in row.keys():
            count += 1
            if count >20:
                outList.append(outstr)
                outstr = ""
                count = 1
            outstr += f"{column}: {row[column]}\n"
            #embed.add_field(name=column, value=row[column], inline=True)
        outList.append(outstr)
    else:
        embed.add_field(name="Ranked Dice Stats", value="No ranked dice stats available.", inline=False)
    for item in outList:
        #embed.add_field(name="Ranked Dice Stats", value=item, inline=False)
        pass
    games_conn=sqlite3.connect("games.db",timeout=10)
    games_conn.row_factory = sqlite3.Row
    games_curs = games_conn.cursor()
    games_curs.execute('''SELECT DISTINCT Season FROM RankedDiceStatsSeasonView WHERE GuildID=? AND UserID=? ORDER BY Season ASC''', (interaction.guild.id, interaction.user.id))
    seasons = games_curs.fetchall()
    
    options = [discord.SelectOption(label="Lifetime", value="lifetime")]
    for season_row in seasons:
        options.append(discord.SelectOption(label=f"Season {season_row['Season']}", value=f"season {season_row['Season']}"))
    seasonSelectorMenu = discord.ui.Select(placeholder="Select Season", options=options)
    async def season_select_callback(interaction: discord.Interaction):
        await ranked_dice_stats_helper(interaction, season=seasonSelectorMenu.values[0], new=False)
    seasonSelectorMenu.callback = season_select_callback
    view = discord.ui.View()
    view.add_item(seasonSelectorMenu)
    games_curs.execute('''SELECT ProvisionalGames FROM PlayerSkill WHERE GuildID=? AND UserID=?''', (interaction.guild.id, interaction.user.id))
    provisional_games = games_curs.fetchone()
    if provisional_games and provisional_games['ProvisionalGames'] == 0:
        #making a graph of rank over time
        rank_values = []
        if season == "lifetime":
            games_curs.execute('''SELECT StartingRank FROM LiveRankedDicePlayers p JOIN LiveRankedDiceMatches m ON m.ID = p.MatchID WHERE m.GuildID=? AND p.UserID=? AND m.ID NOT IN (SELECT value FROM ProvisionalMatchFilter pmf, json_each('[' || pmf.ProvisionalMatchIDs || ']') WHERE pmf.GuildID = m.GuildID AND pmf.UserID = p.UserID) ORDER BY m.ID ASC''', (interaction.guild.id, interaction.user.id))
            ranks= games_curs.fetchall()
            games_curs.execute('''SELECT Rank from PlayerSkill WHERE GuildID=? AND UserID=?''', (interaction.guild.id, interaction.user.id))
            current_rank = games_curs.fetchone()
            if ranks and current_rank:
                for rank in ranks:
                    rank_values.append(rank['StartingRank'])
                rank_values.append(current_rank['Rank'])  
        elif season.__contains__("season"):
            games_curs.execute('''SELECT StartingRank FROM LiveRankedDicePlayers p JOIN LiveRankedDiceMatches m ON m.ID = p.MatchID WHERE m.GuildID=? AND p.UserID=? AND m.Season=? AND m.ID NOT IN (SELECT value FROM ProvisionalMatchFilter pmf, json_each('[' || pmf.ProvisionalMatchIDs || ']') WHERE pmf.GuildID = m.GuildID AND pmf.UserID = p.UserID) ORDER BY m.ID ASC''', (interaction.guild.id, interaction.user.id, int(season.replace("season","").strip())))
            ranks= games_curs.fetchall()
            for rank in ranks:
                rank_values.append(rank['StartingRank'])
            games_curs.execute('''SELECT Season FROM RankedDiceGlobals''')
            current_season = games_curs.fetchone()
            if current_season and current_season == int(season.replace("season","").strip()):
                games_curs.execute('''SELECT Rank from PlayerSkill WHERE GuildID=? AND UserID=?''', (interaction.guild.id, interaction.user.id))
                current_rank = games_curs.fetchone()
                if current_rank:
                    rank_values.append(current_rank['Rank'])
        embed, file = await send_rank_dice_stats_plot(interaction, season=season, embed=embed, rank_values=rank_values)
        graph_button = GraphButton(label="View Rank Graph", style=discord.ButtonStyle.primary, file=file)
        view.add_item(graph_button)

    games_curs.close()
    games_conn.close()
    if new:
        await interaction.followup.send(embed=embed, ephemeral=True, view=view)
    else:
        await interaction.response.edit_message(embed=embed, view=view)

class GraphButton(discord.ui.Button):
    def __init__(self, label=None, style=discord.ButtonStyle.primary, file=None):
        super().__init__(label=label, style=style)
        self.file = file

    async def callback(self, interaction: discord.Interaction):
        #send the file in an emphemeral message
        await interaction.response.send_message(file=self.file, ephemeral=True)

async def send_rank_dice_stats_plot(interaction: discord.Interaction, season: str="lifetime", embed: discord.Embed= None, rank_values: list=[]):
    plt.figure(figsize=(10, 5))
    plt.plot(range(1, len(rank_values) + 1), rank_values)#, marker='o'
    #plt.gca().invert_yaxis()
    plt.title('Rank Over Time')
    plt.xlabel('Number of Games Played')
    plt.ylabel('Rank')
    plt.grid(True)
    #plt.xticks(range(1, len(rank_values) + 1))
    #plt.yticks(range(1, 41))
    plt.yticks(ticks=[6,11,16,21,25,30,35,40], labels=["Silver1","Gold1","Platinum1","Diamond 1","Diamond 5","Diamond 10","Diamond 15","Diamond 20"])
    # Save the plot to a file
    plot_filename = f'images/ranked_dice_rank_{interaction.guild.id}_{interaction.user.id}_{season}.png'
    plt.savefig(plot_filename)
    plt.close()
    # Send the plot image in the Discord message
    file = discord.File(plot_filename, filename="ranked_dice_rank.png")
    embed.set_image(url="attachment://ranked_dice_rank.png")
    return embed, file

class AddAuthorizedUser(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client


    @app_commands.command(name="add-authorized-user", description="User ID")
    async def add_authorized_user(self, interaction: discord.Interaction, userid: str):
        gamesDB="games.db"
        games_conn = sqlite3.connect(gamesDB)
        games_curs = games_conn.cursor()
        games_curs.execute('''INSERT INTO CommandLog (GuildID, UserID, CommandName, CommandParameters) VALUES (?, ?, ?, ?)''', (interaction.guild.id, interaction.user.id, "add-authorized-user", f"User: {userid}"))
        games_conn.commit()
        games_curs.close()
        games_conn.close()
        if not await isAuthorized(interaction.user.id, str(interaction.guild.id), self.client):
            await interaction.response.send_message("You are not authorized to use this command.")
            return
        #validate that the user id is from a user in this guild
        guild = self.client.get_guild(interaction.guild.id)
        member = guild.get_member(int(userid))
        if not member:
            await interaction.response.send_message("User not found in this guild.")
            return
        main_db = "MY_DB"
        main_conn = sqlite3.connect(main_db)
        main_curs = main_conn.cursor()
        main_curs.execute("SELECT AuthorizedUsers FROM ServerSettings WHERE GuildID = ?", (interaction.guild.id,))
        result = main_curs.fetchone()
        if result and result[0]:
            authorized_users = json.loads(result[0])
            if userid not in authorized_users:
                authorized_users.append(userid)
                main_curs.execute("UPDATE ServerSettings SET AuthorizedUsers = ? WHERE GuildID = ?", (json.dumps(authorized_users), interaction.guild.id))
            else:
                authorized_users.remove(userid)
                main_curs.execute("UPDATE ServerSettings SET AuthorizedUsers = ? WHERE GuildID = ?", (json.dumps(authorized_users), interaction.guild.id))
        else:
            authorized_users=[]
            authorized_users.append(userid)
            main_curs.execute("UPDATE ServerSettings SET AuthorizedUsers = ? WHERE GuildID = ?", (json.dumps(authorized_users), interaction.guild.id))
        main_conn.commit()
        main_curs.close()
        main_conn.close()
        await interaction.response.send_message(f"User {userid  } has been added to the authorized users list.")

class Wiki(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    @app_commands.command(name="wiki", description="A wiki for understanding the bot's features")
    async def wiki(self, interaction: discord.Interaction):
        #log it to the command log
        games_conn=sqlite3.connect("games.db",timeout=10)
        games_curs = games_conn.cursor()
        games_curs.execute('''INSERT INTO CommandLog (GuildID, UserID, CommandName) VALUES (?, ?, ?)''', (interaction.guild.id, interaction.user.id, "wiki"))
        games_conn.commit()
        games_curs.close()
        games_conn.close()
        embed = discord.Embed(title="Bot Wiki", description="A wiki for understanding the bot's features.", color=0x228a65)
        pages = await get_wiki_page()
        for page in pages:
            embed.add_field(name=page['CommandName'], value=page['CommandDescription'], inline=False)
        view = discord.ui.View(timeout=None)
        view.add_item(WikiChangeButton(label="General", group="General"))
        view.add_item(WikiChangeButton(label="Data", group="Data"))
        view.add_item(WikiChangeButton(label="Trivia", group="Trivia"))
        view.add_item(WikiChangeButton(label="Other", group="Other"))
        await interaction.response.send_message(embed=embed, ephemeral=True, view=view)

class WikiChangeButton(discord.ui.Button):
    def __init__(self, label=None, style=discord.ButtonStyle.primary, group="General"):
        super().__init__(label=label, style=style)
        self.group = group

    async def callback(self, interaction: discord.Interaction):
        pages = await get_wiki_page(self.group)
        embed = discord.Embed(title=f"Wiki - {self.group}", color=0x228a65)
        for page in pages:
            embed.add_field(name=page['CommandName'], value=page['CommandDescription'], inline=False)
        view = discord.ui.View(timeout=None)
        view.add_item(WikiChangeButton(label="General", group="General"))
        view.add_item(WikiChangeButton(label="Data", group="Data"))
        view.add_item(WikiChangeButton(label="Trivia", group="Trivia"))
        view.add_item(WikiChangeButton(label="Other", group="Other"))
        await interaction.response.edit_message(embed=embed, view=view)
        return
    
async def get_wiki_page(group: str= "General"):
    games_conn=sqlite3.connect("games.db",timeout=10)
    games_conn.row_factory = sqlite3.Row
    games_curs = games_conn.cursor()
    games_curs.execute("select CommandName, CommandDescription from Wiki where CommandGroup=? order by ListOrder asc", (group,))
    pages = games_curs.fetchall()
    games_curs.close()
    games_conn.close()
    return pages

class Achievements(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    @app_commands.command(name="achievements", description="Displays your achievements")
    async def achievements(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        guild_id = interaction.guild.id

        # Fetch the user's achievements from the database
        gamesDB="games.db"
        games_conn = sqlite3.connect(gamesDB)   
        games_conn.row_factory = sqlite3.Row
        games_curs = games_conn.cursor()
        games_curs.execute('''INSERT INTO CommandLog (GuildID, UserID, CommandName) VALUES (?, ?, ?)''', (interaction.guild.id, interaction.user.id, "achievements"))
        games_conn.commit()
        games_curs.execute("""
            SELECT 
                ad.ID,
                ad.Name,
                ad.Description,
                ad.TriggerType,
                ad.Value,
                ad.FlavorText,
                ua.Timestamp
            FROM AchievementDefinitions AS ad
            INNER JOIN UserAchievements AS ua
                ON ad.ID = ua.AchievementID
            WHERE ua.GuildID = ?
            AND ua.UserID = ?
            ORDER BY ad.ID
        """, (interaction.guild.id, interaction.user.id))

        rows = games_curs.fetchall()

        games_curs.close()
        games_conn.close()

        if not rows:
            await interaction.response.send_message("You haven't unlocked any achievements yet!", ephemeral=True)
            return

        # Build pages
        pages = []
        per_page = 5

        for i in range(0, len(rows), per_page):
            chunk = rows[i:i+per_page]

            embed = discord.Embed(
                title=f"Achievements ({i+1}-{min(i+5, len(rows))} of {len(rows)})",
                color=discord.Color.gold()
            )

            for ach in chunk:
                ach_id, name, desc, trigger, value, flavor, timestamp = ach
                flavor = flavor if flavor is not None else "-"
                embed.add_field(
                    name=f"{ach_id}: {name}",
                    value=f"**Description:** {desc}\n"
                        f"*{flavor}*\n"
                        f"**Unlocked:** {timestamp}\n"
                        f"-----------------------------------",
                    inline=False
                )

            pages.append(embed)

        view = AchievementsPaginator(interaction, pages)

        await interaction.response.send_message(embed=pages[0], view=view, ephemeral=True)

class AchievementsPaginator(discord.ui.View):
    def __init__(self, interaction, pages):
        super().__init__(timeout=120)
        self.interaction = interaction
        self.pages = pages
        self.current_page = 0

        # Disable "Previous" on first page
        self.children[0].disabled = True

    async def update_page(self, interaction):
        embed = self.pages[self.current_page]

        # Update button states
        self.children[0].disabled = (self.current_page == 0)
        self.children[1].disabled = (self.current_page == len(self.pages) - 1)

        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        await self.update_page(interaction)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        await self.update_page(interaction)



async def setup(client: commands.Bot):
    await client.add_cog(News(client))
    await client.add_cog(Inventory(client))
    await client.add_cog(Stats(client))
    await client.add_cog(AddAuthorizedUser(client))
    await client.add_cog(Wiki(client))
    await client.add_cog(Achievements(client))
    await client.add_cog(RankedDiceStats(client))