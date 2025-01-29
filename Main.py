import discord
import sqlite3
import os
import time
from discord.ext import tasks, commands
from discord.utils import get
from random import random
from datetime import datetime
from collections import deque
import pandas as pd
#import matplotlib
#matplotlib.use('Agg')
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
    



#lineLabel, numItems, guildID, curs, scale, topNum, drillType, drillName
#graphType, graphXaxis, numMessages, guildID, numLines, drillDownType, drillDownTarget, curs
#qc='''SELECT * FROM (SELECT * FROM Master x where x.GuildID == ? order by UTCTime DESC LIMIT ?) sub ORDER by UTCTime ASC'''


def mostUsedEmojis(guildID, curs):
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
    st1 = time.perf_counter()
    
    curs.execute(qc, param)
    rows = curs.fetchall()
    
    for row in rows:
        tstr = row[6]
        try:
            dt = datetime.strptime(tstr, "%Y-%m-%d %H:%M:%S.%f")
        except:
            dt = datetime.strptime(tstr, "%Y-%m-%d %H:%M:%S")
        
        nameDict[str(row[lineLabel])] = str(row[lineLabel - 1])
        
        if row[lineLabel] not in dataDict:
            dataDict[row[lineLabel]] = [0] * len(dayList)
        
        if graphXaxis in {'hour', 'day'}:
            if curDay == '':
                curDay = dt.strftime("%m / %d / %Y") if graphXaxis == 'day' else dt.strftime("%m / %d / %Y, %H")
                dayList.append(curDay)
            
            if curDay != (dt.strftime("%m / %d / %Y") if graphXaxis == 'day' else dt.strftime("%m / %d / %Y, %H")):
                curDay = dt.strftime("%m / %d / %Y") if graphXaxis == 'day' else dt.strftime("%m / %d / %Y, %H")
                dayList.append(curDay)
                
                for key in dataDict:
                    dataDict[key].append(0)
        
        dataDict[row[lineLabel]][-1] += 1
    
    et1 = time.perf_counter()
    logging.info("sql loop time:" + str(et1 - st1))
    st1 = time.perf_counter()
    
    dataDict = dict(sorted(dataDict.items(), key=lambda item: sum(item[1]), reverse=True)[:numLines])
    nameDict = {k: nameDict[k] for k in dataDict}
    
    et1 = time.perf_counter()
    logging.info("data trimming time: " + str(et1 - st1))
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
    
    return nameDict, dataDict

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

def t_make():
    print('')

class MyClient(discord.Client):
    ignoreList=[]
    #lastDate=""
    async def on_ready(self):
        #8 f=open(
        print('Logged on as {0}!'.format(self.user))
        print(random())
        channel=client.get_channel(150421071676309504)
        await channel.send("rebooted")
        DB_NAME = "My_DB"
        conn = sqlite3.connect(DB_NAME)
        curs = conn.cursor()

        with open('Emote_Graph_Schema.sql') as f:
            curs.executescript(f.read())
        
        conn.commit()  
        curs.close()
        conn.close()
        #assignRoles.start()
        #await assignRoles()
        sched=AsyncIOScheduler()
        sched.add_job(assignRoles,'interval',seconds=900)
        #sched.start()
        
        
    async def on_thread_create(self,thread):
        await thread.join()
    

    async def on_message(self, message):
        if message.author==client.user:
            return
        if message.author.bot:
            #print('bot!')
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
            if splitstr[0]=='..graph':
                st1=time.perf_counter()
                graphType='channels'
                graphXaxis='day'
                numMessages=99999
                guildID=str(message.guild.id)
                numLines=15
                drillDownType=''
                drillDownTarget=''
                try:
                    if splitstr[1] == 'channel':
                        graphType='channels'
                    elif splitstr[1] == 'user':
                        graphType='users'
                    elif splitstr[1] == 'singleChannel':
                        graphType='singleChannel'
                    elif splitstr[1] == 'singleUser':
                        graphType='singleUser'
                    print('param1 set: '+graphType)
                    numMessages=splitstr[2]
                    print("param2 set")
                    if splitstr[3] == 'day':
                        graphXaxis='day'
                    elif splitstr[3] == 'hour':
                        graphXaxis='hour'
                    print("param3 set")
                    
                    numLines=splitstr[4]
                    print('param4 set')
                    if graphType == 'singleChannel' or graphType == 'singleUser':
                       # drillDownType=splitstr[5]
                        drillDownTarget=splitstr[5]
                        await message.channel.send(drillDownTarget)
                        
                except IndexError:
                    await message.channel.send('incorrect parameter, using defaults')
                et1=time.perf_counter()
                #await message.channel.send(str(et1-st1))
                startTime=time.perf_counter()
                Graph(graphType, graphXaxis, numMessages, guildID, int(numLines), drillDownTarget, curs)
                endTime=time.perf_counter()
                graphFile=discord.File("images/"+str(message.guild.id)+".png", filename="graph.png")
                #await message.channel.send(str(endTime-startTime))
                guildName=message.guild.name
                embed=discord.Embed(title="Activity Graph",color=0x228a65)
                embed.set_image(url="attachment://graph.png")
                embed.set_author(name=guildName, icon_url=message.guild.icon.url)
                await message.channel.send(file=graphFile, embed=embed)
                #await message.channel.send(file=discord.File("images/"+str(message.guild.id)+".png"))
                
                    
        #try:
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
                resposneImage=discord.File("images/based_on_recent_events.png", filename="response.png")
                await message.reply(file=resposneImage)
                print("hold")

            if splitstr[0]=='mostUsedEmojis':
                emojiList=mostUsedEmojis(str(message.guild.id), curs)
                output=""
                for entry in emojiList:
                    if entry[5]=="a":
                        output+=str(entry[1])+" : <a:"+str(entry[3])+":"+ str(entry[2])+"> : "+str(entry[4])+" uses\n"
                    else:
                        output+=str(entry[1])+" : <:"+str(entry[3])+":"+ str(entry[2])+"> : "+str(entry[4])+" uses\n"
                await message.channel.send(output)



            if (splitstr[0]=='ping' or splitstr[0]=='Ping'):
                if message.author.id==100344687029665792:
                    await message.channel.send("prong")
                    
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
                    print("")
        #except:
            #print('error')
                #await message.channel.send("")
        #Connect or Create DB File
#         DB_NAME = "My_DB"
#         conn = sqlite3.connect(DB_NAME)
#         curs = conn.cursor()
        #curs.execute('''INSERT INTO StdSensorTypes (SensorCode, SensorType) VALUES ("s7", "Door-Windows Sensor")''')
        #curs.execute('''INSERT INTO Master (GuildName, GuildID, UserName, UserID, ChannelName, ChannelID, UTCTime) VALUES (message.author.name)''')
        #curs.execute('''INSERT INTO Master (GuildName) VALUES (?)''')
        tp='''INSERT INTO Master (GuildName,GuildID, UserName, UserID, ChannelName, ChannelID, UTCTime) VALUES (?,?,?,?,?,?,?);'''
        data=(message.guild.name,str(message.guild.id),message.author.name,str(message.author.id),message.channel.name,str(message.channel.id),str(message.created_at.utcnow()))
        curs.execute(tp,data)

        print(message.content)
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

            if match.group('animated')=='a':
                print('animated')
                #await message.channel.send('<a:'+match.group('name')+':'+match.group('id')+'>')
            else:
                print('not animated')
                #await message.channel.send('<:'+match.group('name')+':'+match.group('id')+'>')

        conn.commit()
        #Close DB
        curs.close()
        conn.close()

intents=discord.Intents.all()
client = MyClient(intents=intents)












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
