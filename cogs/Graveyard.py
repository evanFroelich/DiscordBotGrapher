async def CoinFlipGame(self, interaction: discord.Interaction, bet_amount: int):
    gamesDB = "games.db"
    games_conn = sqlite3.connect(gamesDB)
    games_curs = games_conn.cursor()
    games_curs.execute('''SELECT CurrentBalance FROM GamblingUserStats WHERE GuildID=? AND UserID=?''', (self.guild_id, self.user_id))
    row = games_curs.fetchone()
    if row is None or row[0] < bet_amount:
        await interaction.response.send_message(f"You do not have enough funds to bet {bet_amount}.", ephemeral=True)
        games_curs.close()
        games_conn.close()
        return

    # Deduct the bet amount from the user's funds
    games_curs.execute('''UPDATE GamblingUserStats SET CurrentBalance=CurrentBalance-? WHERE GuildID=? AND UserID=?''', (bet_amount, self.guild_id, self.user_id))
    
    # Simulate a win or loss
    if random.random() < 0.5:  # 50% chance of winning
        winnings = bet_amount * 2
        await award_points(winnings, self.guild_id, self.user_id)
        #games_curs.execute('''UPDATE GamblingUserStats SET CurrentBalance=CurrentBalance+? WHERE GuildID=? AND UserID=?''', (winnings, self.guild_id, self.user_id))
        await interaction.response.send_message(f"You won {winnings}!", ephemeral=True)
    else:
        await interaction.response.send_message(f"You lost {bet_amount}.", ephemeral=True)

    games_conn.commit()
    games_curs.close()
    games_conn.close()

#set up a modal to set the settings for patch notes
#@client.tree.command(name="change-settings-wip", description="select which feature to change settings")
@app_commands.choices(feature=[
    #app_commands.Choice(name="Top Chatter Tracking", value="topChatterTracking"),
    app_commands.Choice(name="Patch Notes", value="patchNotes")
])
async def changesettings(interaction: discord.Interaction, feature: app_commands.Choice[str]):
    if feature.value == "patchNotes":
        modal = PatchNotesModal()
        await interaction.response.send_modal(modal)

  
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

# Slash command to send the settings menu
#@client.tree.command(name="server-settings-wip", description="Use buttons to set server settings")
async def serversettings(interaction: discord.Interaction):
    if not await isAuthorized(str(interaction.user.id), str(interaction.guild.id)):
        await interaction.response.send_message("You are not authorized to use this command. ask an administrator to authorize you using the /addAuthorizedUser command.",ephemeral=True)
        return
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
    
