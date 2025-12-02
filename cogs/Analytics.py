import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import time
import pandas as pd
import matplotlib.pyplot as plt
import logging as Errorlogging
from datetime import datetime

from Helpers.Helpers import isAuthorized


# Errorlogging.basicConfig(level=Errorlogging.INFO)
# logger = Errorlogging.getLogger(__name__)


class ServerGraph(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    @app_commands.command(name="server-graph", description="Replies with a graph of activity")
    @app_commands.choices(subtype=[
        app_commands.Choice(name="channel", value="channels"),
        app_commands.Choice(name="user", value="users"),
        app_commands.Choice(name="singleChannel", value="singleChannel"),
        app_commands.Choice(name="singleUser", value="singleUser")
    ])
    @app_commands.choices(xaxislabel=[
        app_commands.Choice(name="day", value="day"),
        app_commands.Choice(name="hour", value="hour")
    ])
    @app_commands.choices(logging=[
        app_commands.Choice(name="true", value="true"),
        app_commands.Choice(name="false", value="false")
    ])
    @app_commands.describe(numberofmessages="number of messages to include in graph <default: 1000>")
    @app_commands.describe(drilldowntarget="target of drill down if using single channel or single user [optional] (channelID or userID) <default: none>")
    @app_commands.describe(numberoflines="number of lines to display <default: 15>")

    async def servergraph(self, interaction: discord.Interaction, subtype: app_commands.Choice[str], xaxislabel: app_commands.Choice[str], logging: app_commands.Choice[str], numberofmessages: int = 1000, drilldowntarget: str = '', numberoflines: int = 15):
        gamesDB="games.db"
        games_conn = sqlite3.connect(gamesDB)
        games_curs = games_conn.cursor()
        games_curs.execute('''INSERT INTO CommandLog (GuildID, UserID, CommandName, CommandParameters) VALUES (?, ?, ?, ?)''', (interaction.guild.id, interaction.user.id, "server-graph", f"'subtype': {subtype.value}, 'xaxislabel': {xaxislabel.value}, 'logging': {logging.value}, 'numberofmessages': {numberofmessages}, 'drilldowntarget': {drilldowntarget}, 'numberoflines': {numberoflines}"))
        games_conn.commit()
        games_curs.close()
        games_conn.close()
        if not await isAuthorized(interaction.user.id, str(interaction.guild.id), self.client):
            await interaction.response.send_message("You are not authorized to use this command.")
            return
        if numberofmessages < 1:
            await interaction.response.send_message("Invalid number of messages.")
            return
        if numberoflines < 1:
            await interaction.response.send_message("Invalid number of lines.")
            return
        if subtype.value in ["singleChannel", "singleUser"]:
            if subtype.value == "singleUser":
                if not (drilldowntarget.isdigit() and int(drilldowntarget) in [user.id for user in interaction.guild.members]):
                    await interaction.response.send_message("Invalid drill down target.")
                    return
            if subtype.value == "singleChannel":
                if not (drilldowntarget.isdigit() and int(drilldowntarget) in [channel.id for channel in interaction.guild.text_channels]):
                    await interaction.response.send_message("Invalid drill down target.")
                    return

        time1 = time.perf_counter()
        await interaction.response.defer(thinking=True)
        DB_NAME = "My_DB"
        conn = sqlite3.connect(DB_NAME)
        curs = conn.cursor()
        try:
            guildID=str(interaction.guild.id)
            guildName=interaction.guild.name
            time2=time.perf_counter()
            t1=time2-time1
            t2,t3,t4,t5,t6,t3a,t3b=Graph(subtype.value, xaxislabel.value, numberofmessages, guildID, numberoflines, drilldowntarget, curs)
            time3=time.perf_counter()
            t7=time3-time2
        except Exception as e:
            await interaction.followup.send(f"An error occurred while generating the graph: {e}")
            Errorlogging.error(f"Error generating graph for guild {interaction.guild.id}: {e}")
            curs.close()
            conn.close()
            return
        graphFile=discord.File("images/"+str(guildID)+".png", filename="graph.png")
        embed=discord.Embed(title="Activity Graph",color=0x228a65)
        embed.set_image(url="attachment://graph.png")
        #TODO: crashes out if guild has no icon
        embed.set_author(name=guildName, icon_url=interaction.guild.icon.url)
        time4=time.perf_counter()
        t8=time4-time1
        await interaction.followup.send(file=graphFile, embed=embed)
        if logging.value=='true':
            log_file_path = 'logs/' + guildID + '.txt'
            with open(log_file_path, 'w') as log_file:
                log_file.write(f"t1: {round(t1,2)} seconds to complete pre flight code\n")
                log_file.write(f"t2: {round(t2,2)} seconds to complete pre sql code\n")
                log_file.write(f"t3: {round(t3,2)} seconds to complete the sql call\n")
                log_file.write(f"--t3a: {round(t3a,2)} seconds to execute sql\n")
                log_file.write(f"--t3b: {round(t3b,2)} seconds to fetchall\n")
                log_file.write(f"t4: {round(t4,2)} seconds to complete dataframe assembly\n")
                log_file.write(f"t5: {round(t5,2)} seconds to complete sorting data points\n")
                log_file.write(f"t6: {round(t6,2)} seconds to complete graph image creation\n")
                log_file.write(f"-----------------------------------------------------\n")
                log_file.write(f"t7: {round(t7,2)} seconds to complete whole graph process\n")
                log_file.write(f"t8: {round(t8,2)} seconds to complete entire command\n")
            logFile=discord.File(log_file_path, filename=guildID+'.txt')
            await interaction.channel.send(file=logFile)
        conn.commit()
        #Close DB
        curs.close()
        conn.close()
        return


def Graph(graphType, graphXaxis, numMessages, guildID, numLines, drillDownTarget, curs):
    st1 = time.perf_counter()
    lineLabel = 3
    param = (guildID, numMessages)
    
    if graphType == 'channels':
        lineLabel = 5
    
    if graphType == 'singleChannel' or graphType == 'singleUser':
        print(graphType)
        param = (guildID, drillDownTarget, numMessages)
        if graphType == 'singleUser':
            lineLabel = 5
    
    qc = '''SELECT * FROM (SELECT * FROM Master x where x.GuildID == ? order by UTCTime DESC LIMIT ?) sub ORDER by UTCTime ASC'''
    
    if graphType == 'singleChannel':
        qc = '''SELECT * FROM (SELECT * FROM Master x where x.GuildID == ? and x.ChannelID == ? order by UTCTime DESC LIMIT ?) sub ORDER by UTCTime ASC'''
    
    if graphType == 'singleUser':
        qc = '''SELECT * FROM (SELECT * FROM Master x where x.GuildID == ? and x.UserID == ? order by UTCTime DESC LIMIT ?) sub ORDER by UTCTime ASC'''
    
    outSTR = ''
    outDict = {}
    dataDict = {}
    nameDict = {}
    curDay = ''
    dayList = []
    
    et1 = time.perf_counter()
    #Errorlogging.info("pre sql call time: " + str(et1 - st1))
    ret1=et1-st1
    st1 = time.perf_counter()
    
    curs.execute(qc, param)
    et2 = time.perf_counter()
    rows = curs.fetchall()
    et1 = time.perf_counter()
    ret2=et1-st1
    ret2a=et2-st1
    ret2b=et1-et2
    
    st1 = time.perf_counter()
    for row in rows:
        tstr = row[6]
        try:
            dt = datetime.strptime(tstr, "%Y-%m-%d %H:%M:%S.%f")
        except:
            dt = datetime.strptime(tstr, "%Y-%m-%d %H:%M:%S")
        
        nameDict[str(row[lineLabel])] = str(row[lineLabel - 1])
        
        #if row[lineLabel] not in dataDict:
        #    print("new entry: "+str(len(dayList)))
        #    dataDict[row[lineLabel]] = [0] * len(dayList)

        if not dataDict:
            #print('dict empty')
            dataDict[row[lineLabel]]=[]
            dataDict[row[lineLabel]].append(0)
        if not (row[lineLabel] in dataDict):
            #print("not here")
            dataDict[row[lineLabel]]=[]
            for key in dataDict:
                for item in dataDict[key]:
                    dataDict[row[lineLabel]].append(0)
                break
        
        if graphXaxis in {'hour', 'day'}:
            if curDay == '':
                curDay = dt.strftime("%m / %d / %Y") if graphXaxis == 'day' else dt.strftime("%m / %d / %Y, %H")
                dayList.append(curDay)
            
            if curDay != (dt.strftime("%m / %d / %Y") if graphXaxis == 'day' else dt.strftime("%m / %d / %Y, %H")):
                curDay = dt.strftime("%m / %d / %Y") if graphXaxis == 'day' else dt.strftime("%m / %d / %Y, %H")
                dayList.append(curDay)
                
                for key in dataDict:
                    dataDict[key].append(0)
        #print(dataDict)
        #print(dataDict[row[lineLabel]]+" : "+row[lineLabel])
        dataDict[row[lineLabel]][-1] += 1
    
    et1 = time.perf_counter()
    #Errorlogging.info("sql loop time:" + str(et1 - st1))
    ret3=et1-st1
    st1 = time.perf_counter()
    
    dataDict = dict(sorted(dataDict.items(), key=lambda item: sum(item[1]), reverse=True)[:numLines])
    nameDict = {k: nameDict[k] for k in dataDict}
    
    et1 = time.perf_counter()
    #Errorlogging.info("data trimming time: " + str(et1 - st1))
    ret4=et1-st1
    st1 = time.perf_counter()
    
    date_formats = {
        'hour': "%m / %d / %Y, %H",
        'day': "%m / %d / %Y"
    }
    
    df = pd.DataFrame(dataDict, index=pd.to_datetime(dayList))
    df.columns = df.columns.to_series().map(nameDict)
    
    fig, ax = plt.subplots(figsize=(35, 20.5))
    df.plot(ax=ax)
    ax.set_xticks(df.index.to_numpy())
    ax.set_xticklabels(dayList, rotation=90, fontsize=22)
    ax.tick_params(axis='y', labelsize=30)
    ax.legend(prop={'size': 20})
    
    plt.savefig("images/" + guildID + ".png")
    
    et1 = time.perf_counter()
    #Errorlogging.info("data frame construction time: " + str(et1 - st1))
    ret5=et1-st1
    
    return ret1, ret2, ret3, ret4, ret5, ret2a, ret2b


class MostUsedEmojis(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    @app_commands.command(name="most-used-emojis",description="Queries emoji data for this server.")
    @app_commands.choices(inorout=[
        app_commands.Choice(name="inServerEmoji", value="in"),
        app_commands.Choice(name="outOfServerEmoji", value="out")
    ])
    @app_commands.choices(subtype=[
        app_commands.Choice(name="server", value="server"),
        app_commands.Choice(name="users", value="user")
    ])
    async def mostUsedEmojis(self, interaction: discord.Interaction, inorout: app_commands.Choice[str], subtype: app_commands.Choice[str]):
        gamesDB="games.db"
        games_conn = sqlite3.connect(gamesDB)
        games_curs = games_conn.cursor()
        games_curs.execute('''INSERT INTO CommandLog (GuildID, UserID, CommandName, CommandParameters) VALUES (?, ?, ?, ?)''', (interaction.guild.id, interaction.user.id, "most-used-emojis", f"inOrOut: {inorout.value}, subtype: {subtype.value}"))
        games_conn.commit()
        games_curs.close()
        games_conn.close()
        if not await isAuthorized(interaction.user.id, str(interaction.guild.id), self.client):
            await interaction.response.send_message("You are not authorized to use this command.")
            return
        DB_NAME = "My_DB"
        conn = sqlite3.connect(DB_NAME)
        curs = conn.cursor()

        output=""
        if inorout.value == 'in':
            if subtype.value == 'user':
                list=emojiQuery(str(interaction.guild.id), 1, curs)
                for entry in list:
                    if entry[5]=="a":
                        output+=str(entry[1])+" : <a:"+str(entry[3])+":"+ str(entry[2])+"> : "+str(entry[4])+" uses\n"
                    else:
                        output+=str(entry[1])+" : <:"+str(entry[3])+":"+ str(entry[2])+"> : "+str(entry[4])+" uses\n"
            elif subtype.value == 'server':
                list=emojiQuery(str(interaction.guild.id), 3, curs)
                for entry in list:
                    if entry[2]=="a":
                        output+"<a:"+str(entry[0])+":"+ str(entry[1])+"> : "+str(entry[3])+" uses\n"
                    else:
                        output+="<:"+str(entry[0])+":"+ str(entry[1])+"> : "+str(entry[3])+" uses\n"

        if inorout.value == 'out':
            if subtype.value == 'user':
                list=emojiQuery(str(interaction.guild.id), 2, curs)
                for entry in list:
                    if entry[5]=="a":
                        output+=str(entry[1])+" : <a:"+str(entry[3])+":"+ str(entry[2])+"> : "+str(entry[4])+" uses\n"
                    else:
                        output+=str(entry[1])+" : <:"+str(entry[3])+":"+ str(entry[2])+"> : "+str(entry[4])+" uses\n"
            elif subtype.value == 'server':
                list=emojiQuery(str(interaction.guild.id), 4, curs)
                for entry in list:
                    if entry[2]=="a":
                        output+"<a:"+str(entry[0])+":"+ str(entry[1])+"> : "+str(entry[3])+" uses\n"
                    else:
                        output+="<:"+str(entry[0])+":"+ str(entry[1])+"> : "+str(entry[3])+" uses\n"
        if output=="":
            output="no data found"
        await interaction.response.send_message(output)

        conn.commit()
        #Close DB
        curs.close()
        conn.close()
        return




#mode: 1=in server by user, 2= out of server by user, 3=in server by raw count, 4=out of server by raw count
def emojiQuery(guildID, mode, curs):
    query = ""
    if mode == 1:
        query = """
        WITH EmojiUsage AS (
            SELECT 
                UserID,
                UserName,
                EmojiID,
                EmojiName,
                COUNT(EmojiID) AS EmojiCount,
                AnimatedFlag,
                MAX(UTCTime) AS LastUsedTime
            FROM InServerEmoji
            WHERE GuildID = ?  
            GROUP BY UserID, EmojiID
        ),
        RankedEmojis AS (
            SELECT 
                UserID,
                UserName,
                EmojiID,
                EmojiName,
                EmojiCount,
                AnimatedFlag,
                LastUsedTime,
                RANK() OVER (PARTITION BY UserID ORDER BY EmojiCount DESC, LastUsedTime DESC) AS Rank
            FROM EmojiUsage
        )
        SELECT 
            UserID,
            UserName,
            EmojiID,
            EmojiName,
            EmojiCount,
            AnimatedFlag,
            LastUsedTime
        FROM RankedEmojis
        WHERE Rank = 1
        ORDER BY EmojiCount DESC, LastUsedTime DESC LIMIT 50;
        """
    elif mode == 2:
        query = """
        WITH EmojiUsage AS (
            SELECT 
                UserID,
                UserName,
                EmojiID,
                EmojiName,
                COUNT(EmojiID) AS EmojiCount,
                AnimatedFlag,
                MAX(UTCTime) AS LastUsedTime
            FROM OutOfServerEmoji
            WHERE GuildID = ?  
            GROUP BY UserID, EmojiID
        ),
        RankedEmojis AS (
            SELECT 
                UserID,
                UserName,
                EmojiID,
                EmojiName,
                EmojiCount,
                AnimatedFlag,
                LastUsedTime,
                RANK() OVER (PARTITION BY UserID ORDER BY EmojiCount DESC, LastUsedTime DESC) AS Rank
            FROM EmojiUsage
        )
        SELECT 
            UserID,
            UserName,
            EmojiID,
            EmojiName,
            EmojiCount,
            AnimatedFlag,
            LastUsedTime
        FROM RankedEmojis
        WHERE Rank = 1
        ORDER BY EmojiCount DESC, LastUsedTime DESC LIMIT 50;
        """
    elif mode == 3:
        query="""
        SELECT   
            EmojiName, 
            EmojiID,
            AnimatedFlag, 
            COUNT(*) AS EmojiUsageCount
        FROM InServerEmoji
        WHERE GuildID = ?
        GROUP BY EmojiName, EmojiID
        ORDER BY EmojiUsageCount DESC LIMIT 50;
        """
    elif mode == 4:
        query="""
        SELECT   
            EmojiName, 
            EmojiID, 
            AnimatedFlag,
            COUNT(*) AS EmojiUsageCount
        FROM OutOfServerEmoji
        WHERE GuildID = ?
        GROUP BY EmojiName, EmojiID
        ORDER BY EmojiUsageCount DESC LIMIT 50;
        """

    sqlResponse=curs.execute(query, (guildID,))
    return sqlResponse.fetchall()


async def setup(client: commands.Bot):
    await client.add_cog(ServerGraph(client))
    await client.add_cog(MostUsedEmojis(client))