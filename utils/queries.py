"""Graph and query utilities."""
import sqlite3
from datetime import datetime
from collections import deque


#mode: 1=in server by user, 2= out of server by user, 3=in server by raw count, 4=out of server by raw count
def emojiQuery(guildID, mode, curs):
    """Query emoji usage data."""
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
        query = """
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
        query = """
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

    sqlResponse = curs.execute(query, (guildID,))
    return sqlResponse.fetchall()


# Global variables for topChat function
lastDate = ""
dateQueue = deque(maxlen=4)


def topChat(graphType, graphXaxis, numMessages, guildID, numLines, drillDownTarget, curs):
    """Query top chat data."""
    lineLabel = 3
    utcnow = datetime.utcnow()
    curtime = utcnow.strftime('%Y-%m-%d %H:%M:%S.%f')
    global lastDate
    global dateQueue
    
    if not len(dateQueue):
        param = (guildID, numMessages)
        print('first run')
        qc = '''SELECT * FROM (SELECT * FROM Master x where x.GuildID == ? order by UTCTime DESC LIMIT ?) sub ORDER by UTCTime ASC'''
    else:
        print('second run')
        param = (guildID, dateQueue[0], curtime)
        qc = '''SELECT * FROM (SELECT * FROM Master x where x.GuildID == ? and strftime('%s', UTCTime) BETWEEN strftime('%s', ?) and strftime('%s', ?) order by UTCTime DESC) sub ORDER by UTCTime ASC'''
    
    outSTR = ''
    outDict = {}
    dataDict = {}
    nameDict = {}
    curDay = ''
    dayList = []
    
    for row in curs.execute(qc, param):
        tstr = row[6]
        dt = datetime.strptime(tstr, "%Y-%m-%d %H:%M:%S.%f")

        nameDict[str(row[lineLabel])] = str(row[lineLabel-1])
        if not dataDict:
            dataDict[row[lineLabel]] = []
            dataDict[row[lineLabel]].append(0)
        if not (row[lineLabel] in dataDict):
            dataDict[row[lineLabel]] = []
            for key in dataDict:
                for item in dataDict[key]:
                    dataDict[row[lineLabel]].append(0)
                break
        
        if graphXaxis == 'hour':
            if curDay == '':
                curDay = dt.strftime("%m / %d / %Y, %H")
                dayList.append(curDay)
            if curDay == dt.strftime("%m / %d / %Y, %H"):
                dataDict[row[lineLabel]][len(dataDict[row[lineLabel]])-1] += 1
            else:
                curDay = dt.strftime("%m / %d / %Y, %H")
                dayList.append(curDay)
                for key in dataDict:
                    dataDict[key].append(0)
                dataDict[row[lineLabel]][len(dataDict[row[lineLabel]])-1] += 1
        elif graphXaxis == 'day':
            if curDay == '':
                curDay = dt.strftime("%m / %d / %Y")
                dayList.append(curDay)
            if curDay == dt.strftime("%m / %d / %Y"):
                dataDict[row[lineLabel]][len(dataDict[row[lineLabel]])-1] += 1
            else:
                curDay = dt.strftime("%m / %d / %Y")
                dayList.append(curDay)
                for key in dataDict:
                    dataDict[key].append(0)
                dataDict[row[lineLabel]][len(dataDict[row[lineLabel]])-1] += 1
        elif graphXaxis == 'day-hour':
            if curDay == '':
                curDay = dt.strftime("%m / %d / %Y, %H")
                dayList.append(curDay)
            if curDay == dt.strftime("%m / %d / %Y, %H"):
                dataDict[row[lineLabel]][len(dataDict[row[lineLabel]])-1] += 1
            else:
                curDay = dt.strftime("%m / %d / %Y, %H")
                dayList.append(curDay)
                for key in dataDict:
                    dataDict[key].append(0)
                dataDict[row[lineLabel]][len(dataDict[row[lineLabel]])-1] += 1
    
    lastDate = curtime
    dateQueue.append(curtime)
    dataDict = {k: dataDict[k] for k in sorted(dataDict, key=lambda k:sum(dataDict[k]), reverse=True)}
    nameDict = {k: nameDict[k] for k in sorted(dataDict, key=lambda k:sum(dataDict[k]), reverse=True)}
    
    tempData = {}
    tempName = {}
    itr = 0
    try:
        for item in list(dataDict.keys()):
            if numLines > 0:
                numLines -= 1
            else:
                del dataDict[item]
                del nameDict[item]
            itr += 1
    except:
        print('required?')
    
    for nameid in nameDict:
        print(nameDict[nameid] + ": " + str(sum(dataDict[nameid])))
    
    return nameDict, dataDict


def Graph(graphType, graphXaxis, numMessages, guildID, numLines, drillDownTarget, curs):
    """Generate graph data."""
    import time as time_module
    import logging
    import pandas as pd
    import matplotlib.pyplot as plt
    
    st1 = time_module.perf_counter()
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
    
    et1 = time_module.perf_counter()
    logging.info("pre sql call time: " + str(et1 - st1))
    ret1 = et1 - st1
    st1 = time_module.perf_counter()
    
    curs.execute(qc, param)
    et2 = time_module.perf_counter()
    rows = curs.fetchall()
    et1 = time_module.perf_counter()
    ret2 = et1 - st1
    ret2a = et2 - st1
    ret2b = et1 - et2
    
    st1 = time_module.perf_counter()
    for row in rows:
        tstr = row[6]
        try:
            dt = datetime.strptime(tstr, "%Y-%m-%d %H:%M:%S.%f")
        except:
            dt = datetime.strptime(tstr, "%Y-%m-%d %H:%M:%S")
        
        nameDict[str(row[lineLabel])] = str(row[lineLabel - 1])
        
        if not dataDict:
            dataDict[row[lineLabel]] = []
            dataDict[row[lineLabel]].append(0)
        if not (row[lineLabel] in dataDict):
            dataDict[row[lineLabel]] = []
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
        dataDict[row[lineLabel]][-1] += 1
    
    et1 = time_module.perf_counter()
    logging.info("sql loop time:" + str(et1 - st1))
    ret3 = et1 - st1
    st1 = time_module.perf_counter()
    
    dataDict = dict(sorted(dataDict.items(), key=lambda item: sum(item[1]), reverse=True)[:numLines])
    nameDict = {k: nameDict[k] for k in dataDict}
    
    et1 = time_module.perf_counter()
    logging.info("data trimming time: " + str(et1 - st1))
    ret4 = et1 - st1
    st1 = time_module.perf_counter()
    
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
    
    et1 = time_module.perf_counter()
    logging.info("data frame construction time: " + str(et1 - st1))
    ret5 = et1 - st1
    
    return ret1, ret2, ret3, ret4, ret5, ret2a, ret2b

