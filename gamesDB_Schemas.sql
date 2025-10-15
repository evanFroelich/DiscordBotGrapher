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

CREATE TABLE if not exists GamblingFunds (
	"GuildID"	INTEGER,
	"UserID"	INTEGER,
	"Funds"	INTEGER,
	PRIMARY KEY("GuildID","UserID")
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

CREATE VIEW if not exists QuestionCounts AS
SELECT 
    Type,
    Difficulty,
    COUNT(*) AS QuestionCount
FROM QuestionList
GROUP BY Type, Difficulty
ORDER BY Type, Difficulty;

CREATE VIEW if not exists QuestionTypesView AS
SELECT DISTINCT
    Type,
    Difficulty
FROM QuestionList
ORDER by Type,Difficulty;