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
import matplotlib.pyplot as plt
from apscheduler.schedulers.asyncio import AsyncIOScheduler



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
def Graph(graphType, graphXaxis, numMessages, guildID, numLines, drillDownTarget, curs):
    lineLabel=3
    param=(guildID, numMessages)
    #print('drillTarget: '+drillDownTarget)
    
    if graphType == 'channels':
        lineLabel=5
    #if graphType == 'user'
    qc='''SELECT * FROM (SELECT * FROM Master x where x.GuildID == ? order by UTCTime DESC LIMIT ?) sub ORDER by UTCTime ASC'''
    if graphType=='singleChannel':
        print('single channel')
        param=(guildID, drillDownTarget, numMessages)
        qc='''SELECT * FROM (SELECT * FROM Master x where x.GuildID == ? and x.ChannelID == ? order by UTCTime DESC LIMIT ?) sub ORDER by UTCTime ASC'''
    if graphType=='singleUser':
        print('single user')
        param=(guildID, drillDownTarget, numMessages)
        qc='''SELECT * FROM (SELECT * FROM Master x where x.GuildID == ? and x.UserID == ? order by UTCTime DESC LIMIT ?) sub ORDER by UTCTime ASC'''
        lineLabel=5
    outSTR=''
    outDict={}
    dataDict={}
    nameDict={}
    curDay=''
    dayList=[]
    
    #print(param)
    for row in curs.execute(qc,param):
        tstr=row[6]
        tstr=tstr.split()
        s1=tstr[0].split('-')
        s2=tstr[1].split(':')
        s3=s2[2].split('.')
        dt=datetime(int(s1[0]),int(s1[1]),int(s1[2]),int(s2[0]),int(s2[1]),int(s3[0]))#,int(s3[1])
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
    dataDict={k: dataDict[k] for k in sorted(dataDict, key=lambda k:sum(dataDict[k]), reverse=True)}
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
    print(dataDict)
    #await message.channel.send(dataDict)
    #await message.channel.send(nameDict)
    df=pd.DataFrame(dataDict,index=dayList)
    df.columns = df.columns.to_series().map(nameDict)
    df.index=pd.to_datetime(dayList)
    #df.set_size_inches(35,20.5)
    ax=df.plot()
    ax.set_xticks(pd.to_datetime(dayList).to_numpy())
    ax.set_xticklabels(dayList)
    #lines=df.plot.line()
    plt.xticks(rotation=90)
    plt.gcf().set_size_inches(35,20.5)
    plt.xticks(fontsize = 22)
    plt.yticks(fontsize = 30)
    plt.legend(prop={'size':20})
    print(dayList)
    #ax.xaxis.set_ticks(dayList)
    #plt.locator_params(axis="x",len(dayList))
    #plt.xticks(dayList)
    #plt.axes.Axes.set_xticklabels(dayList,fontdict=None)
    #plt.axis.xaxis.set_ticks(dayList)
    plt.savefig("images/"+guildID+".png")
    #return dayList
    
    #plt.show()
    return

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
        tstr=row[6]
        tstr=tstr.split()
        s1=tstr[0].split('-')
        s2=tstr[1].split(':')
        s3=s2[2].split('.')
        dt=datetime(int(s1[0]),int(s1[1]),int(s1[2]),int(s2[0]),int(s2[1]),int(s3[0]))#,int(s3[1])
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
        #assignRoles.start()
        await assignRoles()
        sched=AsyncIOScheduler()
        sched.add_job(assignRoles,'interval',seconds=900)
        sched.start()
        
        
    async def on_thread_create(self,thread):
        await thread.join()
    

    async def on_message(self, message):
        if message.author==client.user:
            return
        if message.author.bot:
            #print('bot!')
            return
        
        DB_NAME = "My_DB"
        conn = sqlite3.connect(DB_NAME)
        curs = conn.cursor()
        
        #print('Message from {0.author}: {0.content}'.format(message))
        print(message.guild.name)
        splitstr=message.content.split()
        if len(message.content)>0:
            if splitstr[0]=='..graph':
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
                Graph(graphType, graphXaxis, numMessages, guildID, int(numLines), drillDownTarget, curs)
                await message.channel.send(file=discord.File("images/"+str(message.guild.id)+".png"))
                
                    
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
                
            if message.content=='Who is Lune?' and message.author.id==100344687029665792:
                await message.channel.send("Who is Lune?")
                time.sleep(1.5)
                m1=await message.channel.send("*Deep breath*")
                time.sleep(1.5)
                await m1.delete()
                time.sleep(2)
                await message.channel.send("For the blind, :see_no_evil:")
                time.sleep(1.5)
                await message.channel.send("She is the light. :bulb:")
                time.sleep(3)
                await message.channel.send("For the famished, :persevere:")
                time.sleep(1.5)
                await message.channel.send("She is sustinance. :bread:")
                time.sleep(3.2)
                await message.channel.send("For the sick, :mask:")
                time.sleep(1.6)
                await message.channel.send("She is the cure. :syringe:")
                time.sleep(3.3)
                await message.channel.send("For the sad, :sob:")
                time.sleep(1.6)
                await message.channel.send("She is joy. :blush:")
                time.sleep(3.3)
                await message.channel.send("For the poor, :no_entry_sign: :coin:")
                time.sleep(1.5)
                await message.channel.send("She is the treasure. :moneybag:")
                time.sleep(3.3)
                await message.channel.send("For the debtor, :pensive:")
                time.sleep(1.4)
                await message.channel.send("She is forgivness. :pray:")
                time.sleep(2.3)
                m1=await message.channel.send("(pause for effect)")
                time.sleep(1.2)
                await m1.delete()
                time.sleep(2)
                await message.channel.send("And on my chessboard,")
                time.sleep(2)
                await message.channel.send("...")
                time.sleep(2)
                await message.channel.send("She is my queen.")
                time.sleep(.75)
                await message.channel.send(":face_holding_back_tears:")
            
                #await message.channel.send(tmp)
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
        conn.commit()
        #Close DB
        curs.close()
        conn.close()

intents=discord.Intents.all()
client = MyClient(intents=intents)












FOToken=open('Token/Token',"r")
token=FOToken.readline()
client.run(token)
