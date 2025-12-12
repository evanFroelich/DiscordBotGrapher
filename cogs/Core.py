from anyio import key
import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import json

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
        games_curs.execute('''SELECT Date, Notes, Headline from NewsFeed order by Date desc Limit 3''')
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
        # Implementation for ranked dice stats command
        games_conn=sqlite3.connect("games.db",timeout=10)
        games_conn.row_factory = sqlite3.Row
        games_curs = games_conn.cursor()
        games_curs.execute('''INSERT INTO CommandLog (GuildID, UserID, CommandName) VALUES (?, ?, ?)''', (interaction.guild.id, interaction.user.id, "ranked-dice-stats"))
        games_conn.commit()
        games_curs.execute('''SELECT * FROM RankedDiceStatsLifetimeView WHERE GuildID=? AND UserID=?''', (interaction.guild.id, interaction.user.id))
        row = games_curs.fetchone()
        games_curs.close()
        games_conn.close()
        embed = discord.Embed(title="---WIP---\nJust a table dump for now, will have formatting later", color=discord.Color.purple())
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
            embed.add_field(name="Ranked Dice Stats", value=item, inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

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