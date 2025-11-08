CREATE TABLE if not exists Scores (
	"GuildID"	INTEGER,
	"UserID"	INTEGER,
	"Category"	TEXT,
	"Difficulty"	INTEGER,
	"Num_Correct"	INTEGER,
	"Num_Incorrect"	INTEGER,
	PRIMARY KEY("UserID","Category","Difficulty","GuildID")
);

CREATE TABLE if not exists QuestionList (
	"ID"	INTEGER,
	"Type"	TEXT,
	"Difficulty"	INTEGER,
	"Question"	TEXT,
	"Answers"	TEXT,
	PRIMARY KEY("ID" AUTOINCREMENT)
);

CREATE TABLE if not exists ActiveQuestions (
	"MessageID"	INTEGER,
	"RespondedUserID"	INTEGER,
	PRIMARY KEY("MessageID","RespondedUserID")
);

CREATE TABLE if not exists FeatureTimers (
	"GuildID"	INTEGER NOT NULL UNIQUE,
	"LastBonusPipTime"	TEXT NOT NULL DEFAULT (datetime('now')),
	"LastBonusPipMessage"	INTEGER,
	"LastRandomQuestionTime"	TEXT NOT NULL DEFAULT (datetime('now')),
	"LastRandomQuestionMessage"	INTEGER,
	PRIMARY KEY("GuildID")
);

CREATE TABLE if not exists GamblingUserStats (
	"GuildID"	INTEGER NOT NULL,
	"UserID"	INTEGER NOT NULL,
	"LifetimeEarnings"	INTEGER NOT NULL DEFAULT 0,
	"CurrentBalance"	INTEGER NOT NULL DEFAULT 0,
	"TipsGiven"	INTEGER NOT NULL DEFAULT 0,
	"CoinFlipWins"	INTEGER NOT NULL DEFAULT 0,
	"CoinFlipEarnings"	INTEGER NOT NULL DEFAULT 0,
	"CoinFlipDoubleWins"	INTEGER NOT NULL DEFAULT 0,
	"LastDailyQuestionTime"	TEXT,
	"QuestionsAnsweredToday"	INTEGER NOT NULL DEFAULT 0,
	"QuestionsAnsweredTodayCorrect"	INTEGER NOT NULL DEFAULT 0,
	"LastRandomQuestionTime"	TEXT,
	"AuctionHouseWinnings"	INTEGER NOT NULL DEFAULT 0,
	"AuctionHouseLosses"	INTEGER NOT NULL DEFAULT 0,
	PRIMARY KEY("GuildID","UserID")
);

CREATE TABLE if not exists GamblingUnlockConditions (
	"GuildID"	INTEGER,
	"Game1Condition1"	INTEGER NOT NULL DEFAULT 500,
	"Game1Condition2"	INTEGER NOT NULL DEFAULT 15,
	"Game1Condition3"	INTEGER NOT NULL DEFAULT 3,
	"Game2Condition1"	INTEGER NOT NULL DEFAULT 2000,
	"Game2Condition2"	INTEGER NOT NULL DEFAULT 500,
	"Game2Condition3"	INTEGER NOT NULL DEFAULT 3,
	PRIMARY KEY("GuildID")
);

CREATE TABLE if not exists GoofsGaffs (
	"GuildID"	INTEGER NOT NULL,
	"FlagHorse"	INTEGER NOT NULL DEFAULT 1,
	"HorseChance"	REAL NOT NULL DEFAULT .25,
	"FlagPing"	INTEGER NOT NULL DEFAULT 1,
	"FlagMarathon"	INTEGER NOT NULL DEFAULT 1,
	"MarathonChance"	REAL NOT NULL DEFAULT .001,
	"FlagCat"	INTEGER NOT NULL DEFAULT 1,
	"CatChance"	REAL NOT NULL DEFAULT .05,
	"FlagTwitterAlt"	INTEGER NOT NULL DEFAULT 1,
	"TwitterAltChance"	REAL NOT NULL DEFAULT .1,
	PRIMARY KEY("GuildID")
);

CREATE TABLE if not exists ServerSettings (
	"GuildID"	INTEGER NOT NULL,
	"NumQuestionsPerDay"	INTEGER NOT NULL DEFAULT 2,
	"QuestionTimeout"	INTEGER NOT NULL DEFAULT 15,
	"PipChance"	REAL NOT NULL DEFAULT 0.2,
	"QuestionChance"	REAL NOT NULL DEFAULT 0.1,
	"FlagShameChannel"	INTEGER NOT NULL DEFAULT 0,
	"ShameChannel"	INTEGER,
	"FlagIgnoredChannels"	INTEGER NOT NULL DEFAULT 0,
	"IgnoredChannels"	TEXT,
	"FlagGoofsGaffs"	INTEGER NOT NULL DEFAULT 1,
	PRIMARY KEY("GuildID")
);

CREATE TABLE if not exists CoinFlipLeaderboard (
	"UserID"	INTEGER NOT NULL,
	"CurrentStreak"	INTEGER NOT NULL DEFAULT 0,
	"LastFlip"	TEXT NOT NULL DEFAULT (datetime('now')),
	PRIMARY KEY("UserID")
);

CREATE TABLE if not exists GamblingGamesUnlocked (
	"GuildID"	INTEGER NOT NULL,
	"UserID"	INTEGER NOT NULL,
	"Game1"	INTEGER NOT NULL DEFAULT 0,
	"Game2"	INTEGER NOT NULL DEFAULT 0,
	"Game3"	INTEGER NOT NULL DEFAULT 0,
	"Game4"	INTEGER NOT NULL DEFAULT 0,
	"Game5"	INTEGER NOT NULL DEFAULT 0,
	PRIMARY KEY("GuildID","UserID")
);

CREATE TABLE if not exists StoryProgression (
	"GuildID"	INTEGER NOT NULL,
	"UserID"	INTEGER NOT NULL,
	"Story1"	INTEGER NOT NULL DEFAULT 0,
	"Story2"	INTEGER NOT NULL DEFAULT 0,
	"Story3"	INTEGER NOT NULL DEFAULT 0,
	PRIMARY KEY("GuildID","UserID")
);

CREATE TABLE if not exists LLMEvaluations (
	"ID"	INTEGER NOT NULL UNIQUE,
	"Question"	TEXT NOT NULL,
	"GivenAnswer"	TEXT NOT NULL,
	"UserAnswer"	TEXT NOT NULL,
	"LLMResponse"	TEXT NOT NULL,
	"ClassicResponse"	TEXT NOT NULL,
	PRIMARY KEY("ID" AUTOINCREMENT)
);

CREATE TABLE if not exists TriviaEventLog (
	"GuildID"	TEXT,
	"UserID"	TEXT,
	"TimeStamp"	TEXT NOT NULL DEFAULT (datetime('now')),
	"DailyOrRandom"	TEXT,
	"QuestionType"	TEXT,
	"QuestionDifficulty"	INTEGER,
	"QuestionText"	TEXT,
	"QuestionAnswers"	TEXT,
	"UserAnswer"	TEXT,
	"ClassicDecision"	INTEGER,
	"LLMDecision"	INTEGER,
	"LLMText"	TEXT,
	"CurrentQuestionsAnsweredToday"	INTEGER,
	"CurrentQuestionsAnsweredTodayCorrect"	INTEGER
);

CREATE TABLE if not exists DailyGamblingTotals (
	"Date"	TEXT NOT NULL,
	"GuildID"	INTEGER NOT NULL,
	"Category"	TEXT NOT NULL,
	"Funds"	INTEGER NOT NULL DEFAULT 0,
	PRIMARY KEY("Date","Category","GuildID")
);

CREATE TABLE if not exists NewsFeed (
	"ID"	INTEGER NOT NULL UNIQUE,
	"Date"	TEXT NOT NULL DEFAULT (date('now', 'localtime')),
	"Headline"	TEXT NOT NULL DEFAULT 'N/A',
	"Notes"	TEXT NOT NULL DEFAULT 'N/A',
	PRIMARY KEY("ID" AUTOINCREMENT)
);

CREATE TABLE if not exists UserStats (
	"GuildID"	INTEGER NOT NULL,
	"UserID"	INTEGER NOT NULL,
	"PingTimestamp"	TEXT NOT NULL DEFAULT (date('now', '-1 day', 'localtime')),
	"PingPongCount"	INTEGER NOT NULL DEFAULT 0,
	"PingKongCount"	INTEGER NOT NULL DEFAULT 0,
	"PingSongCount"	INTEGER NOT NULL DEFAULT 0,
	"PingDongCount"	INTEGER NOT NULL DEFAULT 0,
	"PingLongCount"	INTEGER NOT NULL DEFAULT 0,
	"PingGoldStarCount"	INTEGER NOT NULL DEFAULT 0,
	"HorseTimestamp"	TEXT NOT NULL DEFAULT (date('now', '-1 day', 'localtime')),
	"HorseHitCount"	INTEGER NOT NULL DEFAULT 0,
	"HorseMissCount"	INTEGER NOT NULL DEFAULT 0,
	"CatTimestamp"	TEXT NOT NULL DEFAULT (date('now', '-1 day', 'localtime')),
	"CatHitCount"	INTEGER NOT NULL DEFAULT 0,
	"CatMissCount"	INTEGER NOT NULL DEFAULT 0,
	"MarathonTimestamp"	TEXT NOT NULL DEFAULT (date('now', '-1 day', 'localtime')),
	"MarathonHitCount"	INTEGER NOT NULL DEFAULT 0,
	"MarathonMissCount"	INTEGER NOT NULL DEFAULT 0,
	"TwitterAltTimestamp"	TEXT NOT NULL DEFAULT (date('now', '-1 day', 'localtime')),
	"TwitterAltHitCount"	INTEGER NOT NULL DEFAULT 0,
	"TwitterAltMissCount"	INTEGER NOT NULL DEFAULT 0,
	PRIMARY KEY("GuildID","UserID")
);

CREATE TABLE if not exists QuestionRetries (
	"GuildID"	INTEGER NOT NULL,
	"D1Retry"	INTEGER NOT NULL DEFAULT 0,
	"D2Retry"	INTEGER NOT NULL DEFAULT 0,
	"D3Retry"	INTEGER NOT NULL DEFAULT 1,
	"D4Retry"	INTEGER NOT NULL DEFAULT 1,
	"D5Retry"	INTEGER NOT NULL DEFAULT 2,
	PRIMARY KEY("GuildID")
);

CREATE TABLE if not exists CommandLog (
	"ID"	INTEGER NOT NULL UNIQUE,
	"GuildID"	INTEGER NOT NULL,
	"UserID"	INTEGER NOT NULL,
	"Timestamp"	TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
	"CommandName"	TEXT NOT NULL,
	"CommandParameters"	TEXT,
	PRIMARY KEY("ID" AUTOINCREMENT)
);

CREATE TABLE  if not exists ActiveTrivia (
	"GuildID"	INTEGER NOT NULL,
	"UserID"	INTEGER NOT NULL,
	"MessageID"	INTEGER NOT NULL,
	"QuestionID"	INTEGER NOT NULL,
	"QuestionType"	TEXT NOT NULL,
	"QuestionDifficulty"	INTEGER NOT NULL,
	"QuestionText"	TEXT NOT NULL,
	"Timestamp"	TEXT DEFAULT (datetime('now', 'localtime')),
	PRIMARY KEY("GuildID","UserID","MessageID")
);

CREATE TABLE if not exists AuctionHousePrize (
	"Date"	TEXT,
	"Zone"	TEXT,
	"TotalAmount"	INTEGER,
	"PercentAuctioned"	REAL,
	"AmountAuctioned"	INTEGER,
	"CurrentPrice"	INTEGER NOT NULL DEFAULT 0,
	"CurrentBidderGuildID"	INTEGER NOT NULL DEFAULT 122123044582981632,
	"CurrentBidderUserID"	INTEGER NOT NULL DEFAULT 100344687029665792,
	"FinalBidderGuildID"	INTEGER,
	"FinalBidderUserID"	INTEGER,
	"HasBeenClaimed"	INTEGER NOT NULL DEFAULT 0,
	"HasBeenCleared"	INTEGER NOT NULL DEFAULT 0,
	"HasRollOver"	INTEGER NOT NULL DEFAULT 0,
	PRIMARY KEY("Date","Zone")
);

CREATE TABLE if not exists Wiki (
	"CommandName"	TEXT NOT NULL,
	"CommandGroup"	TEXT,
	"CommandDescription"	TEXT,
	"ListOrder"	INTEGER NOT NULL DEFAULT 0,
	PRIMARY KEY("CommandName")
);

CREATE TABLE if not exists ActiveSteals (
	"GuildID"	INTEGER NOT NULL,
	"ChannelID"	INTEGER NOT NULL,
	"MessageID"	INTEGER NOT NULL,
	"Timestamp"	TEXT DEFAULT (datetime('now', 'localtime')),
	PRIMARY KEY("MessageID")
);

CREATE VIEW if not exists GamblingUnlockMetricsView AS
SELECT
    GuildID,
    UserID,
    LifetimeEarnings AS Game1Condition1,
    TipsGiven AS Game1Condition2,
    QuestionsAnsweredTodayCorrect AS Game1Condition3,
    LifetimeEarnings AS Game2Condition1,
    CoinFlipEarnings AS Game2Condition2,
    CoinFlipDoubleWins AS Game2Condition3
FROM GamblingUserStats;

CREATE VIEW if not exists QuestionTypesView AS
SELECT 
    Type,
    Difficulty,
    COUNT(*) AS QuestionCount
FROM QuestionList
GROUP BY Type, Difficulty
ORDER BY Type, Difficulty;

CREATE VIEW if not exists UserStatsGeneralView AS WITH
Trivia AS (
    SELECT GuildID, UserID, SUM(Num_Correct) AS TotalCorrect,
        SUM(Num_Incorrect) AS TotalIncorrect,
        SUM(Num_Correct + Num_Incorrect) AS TriviaCount
    FROM Scores
	WHERE Category != 'bonus'
    GROUP BY GuildID, UserID
),
Gambling AS (
    SELECT GuildID, UserID, LifetimeEarnings, CurrentBalance, TipsGiven,
           CoinFlipWins, CoinFlipEarnings, CoinFlipDoubleWins
    FROM GamblingUserStats
),
CoinFlips AS (
    SELECT UserID, CurrentStreak, LastFlip, TimesFlipped
    FROM CoinFlipLeaderboard
    GROUP BY UserID
),
Commands AS (
    SELECT GuildID, UserID, COUNT(*) AS TotalCommands
    FROM CommandLog
    GROUP BY GuildID, UserID
)
SELECT
    t.GuildID,
    t.UserID,
    t.TriviaCount,
    g.LifetimeEarnings,
    g.CurrentBalance,
    g.TipsGiven,
    g.CoinFlipWins,
    g.CoinFlipEarnings,
    g.CoinFlipDoubleWins,
    c.CurrentStreak,
    c.LastFlip,
    c.TimesFlipped,
    cmd.TotalCommands
FROM Trivia t
LEFT JOIN Gambling g
    ON t.GuildID = g.GuildID AND t.UserID = g.UserID
LEFT JOIN CoinFlips c
    ON t.UserID = c.UserID
LEFT JOIN Commands cmd
    ON t.GuildID = cmd.GuildID AND t.UserID = cmd.UserID;