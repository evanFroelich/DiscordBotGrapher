import discord
import sqlite3
import os
import time
from discord.ext import tasks, commands
from discord.utils import get
from discord import app_commands
from random import random
from datetime import datetime
from collections import deque
import pandas as pd
import matplotlib.pyplot as plt
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging
import re



#role=get(message.guild.roles, id=1016131254497845280)
#await message.channel.send(len(role.members))
#@tasks.loop(seconds=900)
async def assignRoles():
    print('placeholder')
    DB_NAME = "My_DB"
    conn = sqlite3.connect(DB_NAME)
    curs = conn.cursor()

    f=open('RankedRoleConfig/config',"r")
    for line in f:
        splitLine=line.split()
        if splitLine[1]=='true':
            t3,t3d=topChat('users','day',splitLine[5],splitLine[0],3,'',curs)
            #print(splitLine[0])
            guild = client.get_guild(int(splitLine[0]))
            #print(guild.name)
            role1=guild.get_role(int(splitLine[2]))
            for member in role1.members:
                await member.remove_roles(role1,reason="",atomic=True)
            role2=guild.get_role(int(splitLine[3]))
            print(len(role2.members))
            for member in role2.members:
                await member.remove_roles(role2,reason="",atomic=True)
            role3=guild.get_role(int(splitLine[4]))
            for member in role3.members:
                await member.remove_roles(role3,reason="",atomic=True)
            x=0
            for memberid in t3:
                member=guild.get_member(int(memberid))
                if x==0:
                    await member.add_roles(role1,reason="",atomic=True)
                if x==1:
                    await member.add_roles(role2,reason="",atomic=True)
                if x==2:
                    await member.add_roles(role3,reason="",atomic=True)
                x+=1
    #await client.send.message(client.get_channel("992895425688383569"), "updated")
    f.close()
    outstr="Top chatters:\n"
    for nameid in t3:
        outstr+=t3[nameid]+": "+str(sum(t3d[nameid])) + "\n"
    channel=client.get_channel(992895425688383569)
    await channel.send(outstr)
    try:
        print('')
    except:
        erFile=open('errorLog',"a")
        #erFile.write('\n'+"eoor logged at "+str(datetime.datetime.now()))
        print('everythis is bad')
        erFile.close()
    curs.close()
    conn.close()
    




class MyClient(discord.Client):
    ignoreList=[]
    #lastDate=""
    async def on_ready(self):
        #8 f=open(
        print('Logged on as {0}!'.format(self.user))
        print(random())
        channel=client.get_channel(150421071676309504)
        await channel.send("rebooted")
        channel=client.get_channel(1337282148054470808)
        await channel.send("rebooted")
        DB_NAME = "My_DB"
        conn = sqlite3.connect(DB_NAME)
        curs = conn.cursor()

        with open('Schemas.sql') as f:
            curs.executescript(f.read())

        currentGuilds=[guild.id for guild in client.guilds]
        print(currentGuilds)
        for guild in currentGuilds:
            curs.execute('''INSERT OR IGNORE INTO ServerSettings (GuildID) VALUES (?);''',(guild,))
        
        conn.commit()  
        curs.execute('''CREATE INDEX IF NOT EXISTS idx_guild_time ON Master (GuildID, UTCTime)''')
        
        curs.execute("PRAGMA temp_store = MEMORY;")  # Use RAM for temp storage
        curs.execute("PRAGMA synchronous = NORMAL;")  # Speeds up writes
        curs.execute("PRAGMA journal_mode = WAL;")  # Allows concurrent reads/writes
        curs.execute("PRAGMA cache_size = 1000000;")  # Increases cache size
        conn.commit()
        curs.close()
        conn.close()
        #assignRoles.start()
        #await assignRoles()
        sched=AsyncIOScheduler()
        sched.add_job(assignRoles,'interval',seconds=900)
        #sched.start()

        await client.tree.sync()
        
    def __init__(self, *, intents, **options):
        super().__init__(intents=intents, **options)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()
        print('synced')

    async def on_thread_create(self,thread):
        await thread.join()

    #untested
    async def on_guild_join(self, guild):
        DB_NAME = "My_DB"
        conn = sqlite3.connect(DB_NAME)
        curs = conn.cursor()
        curs.execute('''INSERT OR IGNORE INTO ServerSettings (GuildID) VALUES (?);''',(guild.id,))
        
        conn.commit()  
        curs.close()
        conn.close()

    async def on_message(self, message):
        if message.author==client.user:
            return
        if message.author.bot:
            #print('bot!')
            if message.author.id==510016054391734273:
                splitstr=message.content.split()
                if "RUINED" in splitstr:
                    time.sleep(5)
                    await message.channel.send("https://tenor.com/view/death-stranding-2-sisyphus-on-the-beach-hideo-kojima-mountain-climb-gif-9060768058445058879")
            return
        
       
        #await message.channel.send('<a:bubble_irl:1039925482998743160>')
        #for emoji in message.guild.emojis:
            #print(emoji.name)
            #print(emoji.id)
        DB_NAME = "My_DB"
        conn = sqlite3.connect(DB_NAME)
        curs = conn.cursor()

    
        
        #print('Message from {0.author}: {0.content}'.format(message))
        print(message.guild.name)
        splitstr=message.content.split()
        if len(message.content)>0:
                    
            if splitstr[0]=='top3':
                tmp,extra=topChat('users','day',300,str(message.guild.id),3,'',curs)
                for key in tmp:
                    await message.channel.send(tmp[key])
                    
            if splitstr[0]=='enableRankedRoles':
                print('trying')
                try:
                    f=open('RankedRoleConfig/config',"r")
                    passing=True
                    print("here")
                    for line in f:
                        print(line)
                        splitLine=line.split()
                        if splitLine[0]==str(message.guild.id):
                            passing=False
                    f.close()
                    if passing:
                        
                        cfgFile=open('RankedRoleConfig/config',"a")
                        cfgFile.write('\n'+str(message.guild.id)+' true '+splitstr[1]+' '+splitstr[2]+' '+splitstr[3]+' '+splitstr[4])
                        cfgFile.close()
                        await message.channel.send("added to list")
                    else:
                        await message.channel.send("already enabled")
                    
                except AssertionError:
                    await message.channel.send("invalid param")
                    
                    
            if splitstr[0]=='disableRankedRoles':
                print('not working yet')
                role=get(message.guild.roles, id=1016131254497845280)
                await message.channel.send(len(role.members))
                

            if "girlcockx.com" in message.content:
                r=random()
                #10% chance of response
                if r<.1:
                    resposneImage=discord.File("images/based_on_recent_events.png", filename="response.png")
                    await message.reply(file=resposneImage)
                    print("hold")

            if "horse" in message.content.lower():
                r=random()
                #25% chance of response
                if r<.25:
                    resposneImage=discord.File("images/horse.gif", filename="respoonse.gif")
                    await message.reply(file=resposneImage)
                    print("hold")

            if splitstr[0]=='cat' or splitstr[0]=='Cat':
                time.sleep(1)  # wait a bit for reactions to register
                newMessage= await message.channel.fetch_message(message.id)
                reactions = newMessage.reactions
                for reaction in reactions:
                    userList=[user async for user in reaction.users()]
                    for user in userList:
                        if user.id == 966695034340663367:
                            r= random()
                            if r<.05:
                                time.sleep(.5)  # give it a second to make it more dramatic
                                resposneImage=discord.File("images/cat_laugh.gif", filename="cat_laugh.gif")
                                await message.reply(file=resposneImage)
                            
            if message.author.id==101755961496076288 or message.channel.id==1360302184297791801 or "marathon" in message.content.lower():
                #make sure the message is not in any channels from the channel block list
                #open the block list file from the global ignore folder
                ignoreList=[]
                try:
                    with open('globalIgnore/channelblocklist.txt', 'r') as f:
                        ignoreList = f.read().splitlines()
                except FileNotFoundError:
                    ignoreList = []
                if str(message.channel.id) not in ignoreList:
                    r=random()
                    if r<.001:
                        resposneImage=discord.File("images/marathon.gif", filename="respoonse.gif")
                        await message.reply(file=resposneImage)
                        print("hold")

            if (splitstr[0]=='ping' or splitstr[0]=='Ping'):
                if message.author.id==100344687029665792:
                    await message.channel.send("pong")
                    
                    #await message.channel.send(outSTR)
                    
                else:
                    rand=random()
                    if rand<.2:
                        await message.channel.send("pong")
                    elif rand<.4:
                        await message.channel.send("song")
                    elif rand<.6:
                        await message.channel.send("dong")
                    elif rand<.8:
                        await message.channel.send("long")
                    elif rand<.99:
                        await message.channel.send("kong")
                    else:
                        await message.channel.send("you found the special message. here is your gold star!")



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



@client.tree.command(name="ping", description="Replies with Pong!")
async def ping(interaction: discord.Interaction):
    rand=random()
    payload=""
    if rand<.2:
        payload="pong"
    elif rand<.4:
        payload="song"
    elif rand<.6:
        payload="dong"
    elif rand<.8:
        payload="long"
    elif rand<.99:
        payload="kong"
    else:
        payload="you found the special message. here is your gold star!"
    #await interaction.channel.send(payload)
    await interaction.response.send_message(payload)


@client.tree.command(name="mostusedemojis",description="Queries emoji data for this server.")
@app_commands.choices(inorout=[
    app_commands.Choice(name="inServerEmoji", value="in"),
    app_commands.Choice(name="outOfServerEmoji", value="out")
])
@app_commands.choices(subtype=[
    app_commands.Choice(name="server", value="server"),
    app_commands.Choice(name="users", value="user")
])
async def mostUsedEmojis(interaction: discord.Interaction, inorout: app_commands.Choice[str], subtype: app_commands.Choice[str]):
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

@client.tree.command(name="servergraph", description="Replies with a graph of activity")
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
#@app_commands.describe(subtype="subtype of graph to display (channel, user, singleChannel, singleUser) <default: channel>")
@app_commands.describe(numberofmessages="number of messages to include in graph <default: 1000>")
#@app_commands.describe(xaxislabel="x axis label (day, hour) <default: day>")
@app_commands.describe(drilldowntarget="target of drill down if using single channel or single user [optional] (channelID or userID) <default: none>")
@app_commands.describe(numberoflines="number of lines to display <default: 15>")
#@app_commands.describe(logging="enable logging <default: false>")

async def servergraph(interaction: discord.Interaction, subtype: app_commands.Choice[str], xaxislabel: app_commands.Choice[str], logging: app_commands.Choice[str], numberofmessages: int = 1000, drilldowntarget: str = '', numberoflines: int = 15):
    time1 = time.perf_counter()
    await interaction.response.defer(thinking=True)
    DB_NAME = "My_DB"
    conn = sqlite3.connect(DB_NAME)
    curs = conn.cursor()

    guildID=str(interaction.guild.id)
    guildName=interaction.guild.name
    time2=time.perf_counter()
    t1=time2-time1
    t2,t3,t4,t5,t6,t3a,t3b=Graph(subtype.value, xaxislabel.value, numberofmessages, guildID, numberoflines, drilldowntarget, curs)
    time3=time.perf_counter()
    t7=time3-time2
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


class ServerSettingsView(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=None)  # No timeout
        self.guild_id = guild_id  # Store the Guild ID
        conn= sqlite3.connect("My_DB")
        curs=conn.cursor()
        curs.execute("SELECT * FROM ServerSettings WHERE GuildID = ?", (guild_id,))
        self.featureStatus=curs.fetchall()
        print(self.featureStatus)
        conn.commit()
        curs.close()
        conn.close()

        # Button 1: Toggle Top Chatter Tracking
        if self.featureStatus[0][1]==1:
            l1="Toggle Top Chatter Tracking<not working>: ✅ Enabled"
            s1=discord.ButtonStyle.success
        else:
            l1="Toggle Top Chatter Tracking<not working>: ❌ Disabled"
            s1=discord.ButtonStyle.danger
        self.button1 = discord.ui.Button(label=l1, style=s1)
        self.button1.callback = self.toggle_top_chatter
        self.add_item(self.button1)

        # Button 2: Toggle Patch Notes
        if self.featureStatus[0][2]==1:
            l2="Toggle Patch Notes ✅ Enabled"
            s2=discord.ButtonStyle.success
        else:
            l2="Toggle Patch Notes ❌ Disabled"
            s2=discord.ButtonStyle.danger
        self.button2 = discord.ui.Button(label=l2, style=s2)
        self.button2.callback = self.toggle_patch_notes
        self.add_item(self.button2)

    async def toggle_top_chatter(self, interaction: discord.Interaction):
        """Toggles Top Chatter Tracking in the database."""
        newStatus = toggle_feature(self.guild_id, "TopChatTracking")  # Toggles in DB
        # Update button label and style based on new status
        if newStatus == 1:
            self.button1.label = "Toggle Top Chatter Tracking<working>: ✅ Enabled"
            self.button1.style = discord.ButtonStyle.success
            newText="✅ Top Chatter Tracking is now enabled"
        else:
            self.button1.label = "Toggle Top Chatter Tracking<not working>: ❌ Disabled"
            self.button1.style = discord.ButtonStyle.danger
            newText="❌ Top Chatter Tracking is now disabled"
        await interaction.response.edit_message(content=newText, view=self)

    async def toggle_patch_notes(self, interaction: discord.Interaction):
        """Toggles Patch Notes in the database (placeholder function)."""
        newStatus = toggle_feature(self.guild_id, "PatchNotes")  # Toggles in DB
        if newStatus == 1:
            self.button2.label = "Toggle Patch Notes<not working>: ✅ Enabled"
            self.button2.style = discord.ButtonStyle.success
            newText="✅ Patch notes feature is now enabled"
        else:
            newText="❌ Patch notes feature is now disabled"
            self.button2.label = "Toggle Patch Notes<not working>: ❌ Disabled"
            self.button2.style = discord.ButtonStyle.danger
        await interaction.response.edit_message(content=newText, view=self)

# Utility function to toggle a feature in the database
def toggle_feature(guild_id, feature_name):
    conn = sqlite3.connect("My_DB")
    curs = conn.cursor()

    # Ensure the column exists (optional safety check)
    curs.execute(f"PRAGMA table_info(ServerSettings);")
    existing_columns = {row[1] for row in curs.fetchall()}
    if feature_name not in existing_columns:
        curs.execute(f"ALTER TABLE ServerSettings ADD COLUMN {feature_name} INTEGER DEFAULT 0;")
        conn.commit()

    # Toggle the feature
    curs.execute(f"SELECT {feature_name} FROM ServerSettings WHERE GuildID = ?", (guild_id,))
    row = curs.fetchone()

    
    if (row is None or row[0] == 0):
        newStatus=1
    else:
        newStatus=0
    curs.execute(f"UPDATE ServerSettings SET {feature_name} = ? WHERE GuildID = ?", (newStatus, guild_id))
    conn.commit()
    conn.close()

    return newStatus  # Return new status for UI updates

# Slash command to send the settings menu
@client.tree.command(name="serversettings", description="Use buttons to set server settings")
async def serversettings(interaction: discord.Interaction):
    guild_id = str(interaction.guild.id)
    guild_name = interaction.guild.name

    embed = discord.Embed(title="Server Settings", color=0x228a65)
    embed.set_author(name=guild_name, icon_url=interaction.guild.icon.url)
    embed.add_field(name="Server ID", value=guild_id, inline=False)
    embed.add_field(name="Server Name", value=guild_name, inline=False)
    embed.add_field(name="Server Settings", value="Click the buttons below to set server settings.", inline=False)

    view = ServerSettingsView(guild_id)  # Create an interactive button view
    await interaction.response.send_message(embed=embed, view=view)

class PatchNotesModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="settings")
        self.channel=discord.ui.TextInput(label="Patch Notes Channel ID", placeholder="Enter the channel ID for patch notes",max_length=24,style=discord.TextStyle.short)
        self.add_item(self.channel)

    async def on_submit(self, interaction):
        #grab the channel ID from the input
        channelID = self.children[0].value
        conn= sqlite3.connect("My_DB")
        curs=conn.cursor()
        curs.execute("INSERT OR REPLACE INTO PatchNotesSettings (GuildID, ChannelID) VALUES (?, ?)", (interaction.guild.id, channelID))
        await interaction.response.send_message(f"Patch notes channel ID set to: <#{channelID}>")
        conn.commit()
        conn.close()


#set up a modal to set the settings for patch notes
@client.tree.command(name="changesettings", description="select which feature to change settings")
@app_commands.choices(feature=[
    #app_commands.Choice(name="Top Chatter Tracking", value="topChatterTracking"),
    app_commands.Choice(name="Patch Notes", value="patchNotes")
])
async def changesettings(interaction: discord.Interaction, feature: app_commands.Choice[str]):
    if feature.value == "patchNotes":
        modal = PatchNotesModal()
        await interaction.response.send_modal(modal)





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
        ORDER BY EmojiCount DESC, LastUsedTime DESC;
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
        ORDER BY EmojiCount DESC, LastUsedTime DESC;
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
        ORDER BY EmojiUsageCount DESC;
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
        ORDER BY EmojiUsageCount DESC;
        """

    sqlResponse=curs.execute(query, (guildID,))
    return sqlResponse.fetchall()

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
    logging.info("pre sql call time: " + str(et1 - st1))
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
    logging.info("sql loop time:" + str(et1 - st1))
    ret3=et1-st1
    st1 = time.perf_counter()
    
    dataDict = dict(sorted(dataDict.items(), key=lambda item: sum(item[1]), reverse=True)[:numLines])
    nameDict = {k: nameDict[k] for k in dataDict}
    
    et1 = time.perf_counter()
    logging.info("data trimming time: " + str(et1 - st1))
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
    logging.info("data frame construction time: " + str(et1 - st1))
    ret5=et1-st1
    
    return ret1, ret2, ret3, ret4, ret5, ret2a, ret2b


#TODO: remove these globals, what was I thinking?
lastDate=""
dateQueue=deque(maxlen=4)
def topChat(graphType, graphXaxis, numMessages, guildID, numLines, drillDownTarget, curs):
    lineLabel=3
    
    #print('drillTarget: '+drillDownTarget)
    
    
    #if graphType == 'user'
    utcnow=datetime.utcnow()
    curtime=utcnow.strftime('%Y-%m-%d %H:%M:%S.%f')
    global lastDate
    global dateQueue
    if not len(dateQueue):
        param=(guildID, numMessages)
        print('first run')
        qc='''SELECT * FROM (SELECT * FROM Master x where x.GuildID == ? order by UTCTime DESC LIMIT ?) sub ORDER by UTCTime ASC'''
    else:
        print('second run')
        param=(guildID,dateQueue[0],curtime)
        qc='''SELECT * FROM (SELECT * FROM Master x where x.GuildID == ? and strftime('%s', UTCTime) BETWEEN strftime('%s', ?) and strftime('%s', ?) order by UTCTime DESC) sub ORDER by UTCTime ASC'''
#     if lastDate=="":
#         param=(guildID, numMessages)
#         print('first run')
#         qc='''SELECT * FROM (SELECT * FROM Master x where x.GuildID == ? order by UTCTime DESC LIMIT ?) sub ORDER by UTCTime ASC'''
#     else:
#         print('second run')
#         param=(guildID,lastDate,curtime)
#         qc='''SELECT * FROM (SELECT * FROM Master x where x.GuildID == ? and strftime('%s', UTCTime) BETWEEN strftime('%s', ?) and strftime('%s', ?) order by UTCTime DESC) sub ORDER by UTCTime ASC'''
    outSTR=''
    outDict={}
    dataDict={}
    nameDict={}
    curDay=''
    dayList=[]
    
    #print(param)
    for row in curs.execute(qc,param):
        tstr = row[6]
        dt = datetime.strptime(tstr, "%Y-%m-%d %H:%M:%S.%f")

        nameDict[str(row[lineLabel])]=str(row[lineLabel-1])
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
        #print(dt.date())
        if graphXaxis=='hour':
            if curDay=='':
                curDay=dt.strftime("%m / %d / %Y, %H")
                #curDay=str(dt.date())
                #curDay=curDay+str(dt.hour)
                dayList.append(curDay)
            if curDay==dt.strftime("%m / %d / %Y, %H"):#str(dt.date()):
                dataDict[row[lineLabel]][len(dataDict[row[lineLabel]])-1]+=1
            else:
                curDay=dt.strftime("%m / %d / %Y, %H")
                #curDay=str(dt.date())
                #curDay=curDay+str(dt.hour)
                dayList.append(curDay)
                for key in dataDict:
                    dataDict[key].append(0)
                dataDict[row[lineLabel]][len(dataDict[row[lineLabel]])-1]+=1
                
        elif graphXaxis=='day':
            if curDay=='':
                curDay=dt.strftime("%m / %d / %Y")
                #curDay=str(dt.date())
                #curDay=curDay+str(dt.hour)
                dayList.append(curDay)
            if curDay==dt.strftime("%m / %d / %Y"):#str(dt.date()):
                dataDict[row[lineLabel]][len(dataDict[row[lineLabel]])-1]+=1
            else:
                curDay=dt.strftime("%m / %d / %Y")
                #curDay=str(dt.date())
                #curDay=curDay+str(dt.hour)
                dayList.append(curDay)
                for key in dataDict:
                    dataDict[key].append(0)
                dataDict[row[lineLabel]][len(dataDict[row[lineLabel]])-1]+=1
        #vvvdepricated currentlyvvv
        elif graphXaxis=='day-hour':
            if curDay=='':
                curDay=dt.strftime("%m / %d / %Y, %H")
                #curDay=str(dt.date())
                #curDay=curDay+str(dt.hour)
                dayList.append(curDay)
            if curDay==dt.strftime("%m / %d / %Y, %H"):#str(dt.date()):
                dataDict[row[lineLabel]][len(dataDict[row[lineLabel]])-1]+=1
            else:
                curDay=dt.strftime("%m / %d / %Y, %H")
                #curDay=str(dt.date())
                #curDay=curDay+str(dt.hour)
                dayList.append(curDay)
                for key in dataDict:
                    dataDict[key].append(0)
                dataDict[row[lineLabel]][len(dataDict[row[lineLabel]])-1]+=1
#                     if str(dt.date()) in outDict:
#                         outDict[str(dt.date())]+=1
#                     else:
#                         outDict[str(dt.date())]=1
#                     #outSTR+=tstr[0]+'\n'
#                 
#                 for key in outDict:
#                     outSTR+=key + ':\t' + str(outDict[key]) + '\n'
    #await message.channel.send(outSTR)
    lastDate=curtime
    dateQueue.append(curtime)
    dataDict={k: dataDict[k] for k in sorted(dataDict, key=lambda k:sum(dataDict[k]), reverse=True)}
    nameDict={k: nameDict[k] for k in sorted(dataDict, key=lambda k:sum(dataDict[k]), reverse=True)}
    tempData={}
    tempName={}
    itr=0
    #print(numLines+" lines")
    try:
        for item in list(dataDict.keys()):
            #print('itr')
            if numLines>0:
                numLines-=1
            else:
                #print('deleting')
                del dataDict[item]
                del nameDict[item]
            #print('itr2') 
            itr+=1
    except:
        print('required?')
    #print(itr)
    #print(dataDict)
    for nameid in nameDict:
        print(nameDict[nameid]+": "+str(sum(dataDict[nameid])))
    return nameDict,dataDict

















script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
log_file_path = 'log_file.log'
logging.basicConfig(filename=log_file_path, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info('Script started')
logging.info('root dir changed')
FOToken=open('Token/Token',"r")
logging.info('Post token')
token=FOToken.readline()
client.run(token)
