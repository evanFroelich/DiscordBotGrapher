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

CREATE TABLE if not exists PassPhraseMasterList (
	"ID"	INTEGER NOT NULL UNIQUE,
	"Phrase"	TEXT,
	PRIMARY KEY("ID" AUTOINCREMENT)
);

CREATE TABLE if not exists UserCasinoPassPhrases (
	"UserID"	INTEGER NOT NULL,
	"GuildID"	INTEGER NOT NULL,
	"Phrase"	TEXT,
	PRIMARY KEY("UserID","GuildID")
);

CREATE TABLE  if not exists AchievementDefinitions (
	"ID"	INTEGER NOT NULL UNIQUE,
	"Name"	TEXT,
	"Description"	TEXT,
	"TriggerType"	TEXT,
	"Value"	INTEGER,
	"FlavorText"	TEXT,
	PRIMARY KEY("ID" AUTOINCREMENT)
);

CREATE TABLE if not exists UserAchievements (
	"GuildID"	INTEGER NOT NULL,
	"UserID"	INTEGER NOT NULL,
	"AchievementID"	INTEGER NOT NULL,
	"Timestamp"	INTEGER NOT NULL DEFAULT (datetime('now', 'localtime')),
	PRIMARY KEY("GuildID","UserID","AchievementID")
);

CREATE TABLE if not exists ShadowListQueue (
	"ID"	INTEGER NOT NULL UNIQUE,
	"Question"	TEXT,
	"GivenAnswer"	TEXT,
	"UserAnswer"	TEXT,
	"LLMResponse"	TEXT,
	"ShadowAnswers"	TEXT,
	PRIMARY KEY("ID" AUTOINCREMENT)
);

CREATE TABLE if not exists PlayerSkill (
    "GuildID"              TEXT NOT NULL,
    "UserID"               TEXT NOT NULL,
    "Mu"                   REAL NOT NULL DEFAULT 25.0,
    "Sigma"                REAL NOT NULL DEFAULT 20.0,
    "LastPlayed"           TEXT,
    "GamesPlayed"          INTEGER NOT NULL DEFAULT 0,
    "WinCount"             INTEGER NOT NULL DEFAULT 0,
    "LossCount"            INTEGER NOT NULL DEFAULT 0,
    "ProvisionalGames"     INTEGER NOT NULL DEFAULT 10,
    "Rank"                 REAL NOT NULL DEFAULT 1,
    "SeasonalGamesPlayed"  INTEGER NOT NULL DEFAULT 0,
    "SeasonalWinCount"     INTEGER NOT NULL DEFAULT 0,
    "SeasonalLossCount"    INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY ("GuildID", "UserID")
);

CREATE TABLE if not exists LiveRankedDiceMatches (
    "ID"             INTEGER PRIMARY KEY AUTOINCREMENT,
    "GuildID"        INTEGER NOT NULL,
	"ChannelID"      INTEGER NOT NULL,
    "MessageID"      INTEGER NOT NULL,
    "TimeInitiated"  TEXT DEFAULT (datetime('now', 'localtime')),
    "GameState"      INTEGER DEFAULT 0
);

CREATE TABLE if not exists LiveRankedDicePlayers (
    "ID"        INTEGER PRIMARY KEY AUTOINCREMENT,
    "MatchID"   INTEGER NOT NULL,
    "UserID"    INTEGER NOT NULL,
    "Modifier"  TEXT,
    "JoinedAt"  TEXT DEFAULT (datetime('now', 'localtime')),
	"RollResult" INTEGER,
	"FinalPosition" INTEGER,
	"StartingSkillMu" REAL,
	"StartingSkillSigma" REAL,
	"StartingRank" REAL,
	"EndSkillMu" REAL,
	"EndSkillSigma" REAL,
	"EndRank" REAL,
    FOREIGN KEY ("MatchID") REFERENCES LiveRankedDiceMatches("ID")
);

CREATE TABLE if not exists RankedDiceGlobals (
	"Name"	TEXT NOT NULL,
	"Mu"	REAL NOT NULL,
	"Sigma"	REAL NOT NULL,
	"Beta"	REAL NOT NULL,
	"Tau"	REAL NOT NULL,
	"SubDiamondBoostWin"	REAL NOT NULL,
	"SubDiamondBoostLose"	REAL NOT NULL,
	"HeartBoostWin"	REAL NOT NULL,
	"HeartBoostLose"	REAL NOT NULL,
	PRIMARY KEY("Name")
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
),
Achievements AS (
    SELECT
        GuildID,
        UserID,
        SUM(CASE WHEN NumAs = 5 AND RowsInCategory = 5 THEN 1 ELSE 0 END) AS CountAllAs,
        SUM(CASE WHEN NumFs = 5 AND RowsInCategory = 5 THEN 1 ELSE 0 END) AS CountAllFs,
        SUM(CASE 
                WHEN RowsInCategory = 5
                 AND NumAs = 1
                 AND NumBs = 1
                 AND NumCs = 1
                 AND NumDs = 1
                 AND NumFs = 1 
                THEN 1 
                ELSE 0 
            END) AS CountRainbow
    FROM SubjectGradeSpreadView
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
    cmd.TotalCommands,
	a.CountAllAs,
	a.CountAllFs,
	a.CountRainbow
FROM Trivia t
LEFT JOIN Gambling g
    ON t.GuildID = g.GuildID AND t.UserID = g.UserID
LEFT JOIN CoinFlips c
    ON t.UserID = c.UserID
LEFT JOIN Commands cmd
    ON t.GuildID = cmd.GuildID AND t.UserID = cmd.UserID
LEFT JOIN Achievements a 
	ON t.GuildID = a.GuildID and t.UserID = a.UserID;

CREATE VIEW if not exists DynamicAchievementScoresView AS SELECT
    ad.ID AS AchievementID,
    COUNT(ua.UserID) AS Earners,

    round(-1 * (150.0 / (1 + 2 * exp(-0.1 * COUNT(ua.UserID)))) + 170, 0) AS Score
FROM AchievementDefinitions ad
LEFT JOIN UserAchievements ua ON ad.ID = ua.AchievementID
GROUP BY ad.ID, ua.GuildID;

CREATE VIEW if not exists UserAchievementScoresView AS SELECT
    ua.GuildID,
    ua.UserID,
    SUM(ascore.Score) AS TotalScore
FROM UserAchievements ua
JOIN DynamicAchievementScoresView ascore
    ON ua.AchievementID = ascore.AchievementID
GROUP BY ua.GuildID, ua.UserID;

CREATE VIEW if not exists GradesPerScoreView AS
SELECT 
    GuildID,
    UserID,
    Category,
    Difficulty,
    Num_Correct,
    Num_Incorrect,
    CASE 
        WHEN Num_Correct + Num_Incorrect = 0 THEN 'F'           -- no answers = F
        WHEN 1.0 * Num_Correct / (Num_Correct + Num_Incorrect) >= 0.9 THEN 'A'
        WHEN 1.0 * Num_Correct / (Num_Correct + Num_Incorrect) >= 0.8 THEN 'B'
        WHEN 1.0 * Num_Correct / (Num_Correct + Num_Incorrect) >= 0.7 THEN 'C'
        WHEN 1.0 * Num_Correct / (Num_Correct + Num_Incorrect) >= 0.6 THEN 'D'
        ELSE 'F'
    END AS Grade
FROM Scores WHERE Category!="bonus";

CREATE VIEW if not exists GradeTotalsView AS
SELECT
    GuildID,
    UserID,
    SUM(CASE WHEN Grade = 'A' THEN 1 ELSE 0 END) AS Total_As,
    SUM(CASE WHEN Grade = 'B' THEN 1 ELSE 0 END) AS Total_Bs,
    SUM(CASE WHEN Grade = 'C' THEN 1 ELSE 0 END) AS Total_Cs,
    SUM(CASE WHEN Grade = 'D' THEN 1 ELSE 0 END) AS Total_Ds,
    SUM(CASE WHEN Grade = 'F' THEN 1 ELSE 0 END) AS Total_Fs
FROM GradesPerScoreView
GROUP BY GuildID, UserID;

CREATE VIEW if not exists SubjectGradeSpreadView AS
SELECT
    GuildID,
    UserID,
    Category,
    COUNT(*) AS RowsInCategory,
    SUM(CASE WHEN Grade = 'A' THEN 1 ELSE 0 END) AS NumAs,
	SUM(CASE WHEN Grade = 'B' THEN 1 ELSE 0 END) AS NumBs,
	SUM(CASE WHEN Grade = 'C' THEN 1 ELSE 0 END) AS NumCs,
	SUM(CASE WHEN Grade = 'D' THEN 1 ELSE 0 END) AS NumDs,
	SUM(CASE WHEN Grade = 'F' THEN 1 ELSE 0 END) AS NumFs
FROM GradesPerScoreView
GROUP BY GuildID, UserID, Category;

CREATE VIEW if not exists RankedDiceStatsLifetimeView AS


SELECT
	m.GuildID,
    a.UserID,
    
    -- Hearts
    SUM(CASE WHEN a.Modifier = 'heart' AND a.EndSkillMu > a.StartingSkillMu THEN 1 ELSE 0 END) AS WinsHeart,
    SUM(CASE WHEN a.Modifier = 'heart' AND a.EndSkillMu < a.StartingSkillMu THEN 1 ELSE 0 END) AS LossesHeart,
    CASE 
        WHEN SUM(CASE WHEN a.Modifier = 'heart' THEN 1 END) = 0 THEN NULL
        ELSE (
            CAST(SUM(CASE WHEN a.Modifier = 'heart' AND a.EndSkillMu > a.StartingSkillMu THEN 1 END) AS FLOAT)
            / CAST(SUM(CASE WHEN a.Modifier = 'heart' THEN 1 END) AS FLOAT)
        ) * 100
    END AS WRHeart,

    -- Clubs
    SUM(CASE WHEN a.Modifier = 'club' AND a.EndSkillMu > a.StartingSkillMu THEN 1 ELSE 0 END) AS WinsClub,
    SUM(CASE WHEN a.Modifier = 'club' AND a.EndSkillMu < a.StartingSkillMu THEN 1 ELSE 0 END) AS LossesClub,
    CASE 
        WHEN SUM(CASE WHEN a.Modifier = 'club' THEN 1 END) = 0 THEN NULL
        ELSE (
            CAST(SUM(CASE WHEN a.Modifier = 'club' AND a.EndSkillMu > a.StartingSkillMu THEN 1 END) AS FLOAT)
            / CAST(SUM(CASE WHEN a.Modifier = 'club' THEN 1 END) AS FLOAT)
        ) * 100
    END AS WRClub,

    -- Diamonds
    SUM(CASE WHEN a.Modifier = 'diamond' AND a.EndSkillMu > a.StartingSkillMu THEN 1 ELSE 0 END) AS WinsDiamond,
    SUM(CASE WHEN a.Modifier = 'diamond' AND a.EndSkillMu < a.StartingSkillMu THEN 1 ELSE 0 END) AS LossesDiamond,
    CASE 
        WHEN SUM(CASE WHEN a.Modifier = 'diamond' THEN 1 END) = 0 THEN NULL
        ELSE (
            CAST(SUM(CASE WHEN a.Modifier = 'diamond' AND a.EndSkillMu > a.StartingSkillMu THEN 1 END) AS FLOAT)
            / CAST(SUM(CASE WHEN a.Modifier = 'diamond' THEN 1 END) AS FLOAT)
        ) * 100
    END AS WRDiamond,

    -- Spades
    SUM(CASE WHEN a.Modifier = 'spade' AND a.EndSkillMu > a.StartingSkillMu THEN 1 ELSE 0 END) AS WinsSpade,
    SUM(CASE WHEN a.Modifier = 'spade' AND a.EndSkillMu < a.StartingSkillMu THEN 1 ELSE 0 END) AS LossesSpade,
    CASE 
        WHEN SUM(CASE WHEN a.Modifier = 'spade' THEN 1 END) = 0 THEN NULL
        ELSE (
            CAST(SUM(CASE WHEN a.Modifier = 'spade' AND a.EndSkillMu > a.StartingSkillMu THEN 1 END) AS FLOAT)
            / CAST(SUM(CASE WHEN a.Modifier = 'spade' THEN 1 END) AS FLOAT)
        ) * 100
    END AS WRSpade,
	SUM(Case when a.FinalPosition = 1 and a.Modifier = 'heart' then 1 else 0 end) as FirstPlaceFinishesHeart,
	SUM(Case when a.FinalPosition = 1 and a.Modifier = 'diamond' then 1 else 0 end) as FirstPlaceFinishesDiamond,
	SUM(Case when a.FinalPosition = 1 and a.Modifier = 'spade' then 1 else 0 end) as FirstPlaceFinishesSpade,
	SUM(Case when a.FinalPosition = 1 and a.Modifier = 'club' then 1 else 0 end) as FirstPlaceFinishesClub,
	SUM(CASE WHEN a.EndSkillMu > a.StartingSkillMu and a.StartingRank > 40 THEN 1 ELSE 0 END) AS D20Wins,
	SUM(CASE WHEN a.Modifier = 'spade' AND a.EndSkillMu > a.StartingSkillMu and a.StartingRank > 40 THEN 1 ELSE 0 END) AS D20SpadeWins,
	SUM(CASE WHEN a.Modifier = 'diamond' AND a.EndSkillMu > a.StartingSkillMu and a.StartingRank > 40 THEN 1 ELSE 0 END) AS D20DiamondWins,
	SUM(CASE WHEN a.Modifier = 'heart' AND a.EndSkillMu > a.StartingSkillMu and a.StartingRank > 40 THEN 1 ELSE 0 END) AS D20HeartWins,
	SUM(CASE WHEN a.Modifier = 'club' AND a.EndSkillMu > a.StartingSkillMu and a.StartingRank > 40 THEN 1 ELSE 0 END) AS D20ClubWins,
	SUM(CASE WHEN a.Modifier = 'spade' AND a.RollResult = 25 THEN 1 ELSE 0 END) AS PerfectRollSpade,
	SUM(CASE WHEN a.Modifier = 'diamond' AND a.RollResult = 20 THEN 1 ELSE 0 END) AS PerfectRollDiamond,
	SUM(CASE WHEN a.Modifier = 'heart' AND a.RollResult = 20 THEN 1 ELSE 0 END) AS PerfectRollHeart,
	SUM(CASE WHEN a.Modifier = 'club' AND a.RollResult = 25 THEN 1 ELSE 0 END) AS PerfectRollClub,
	SUM(CASE WHEN a.Modifier = 'spade' AND a.RollResult = 6 THEN 1 ELSE 0 END) AS MinRollSpade,
	SUM(CASE WHEN a.Modifier = 'diamond' AND a.RollResult = 1 THEN 1 ELSE 0 END) AS MinRollDiamond,
	SUM(CASE WHEN a.Modifier = 'heart' AND a.RollResult = 1 THEN 1 ELSE 0 END) AS MinRollHeart,
	SUM(CASE WHEN a.Modifier = 'club' AND a.RollResult = 6 THEN 1 ELSE 0 END) AS MinRollClub,
	
	SUM(
        CASE WHEN pcount.LobbySize = 2 AND a.EndSkillMu > a.StartingSkillMu
        THEN 1 ELSE 0 END
    ) AS Wins1v1,

    -- Small Lobby Wins (3–4 players)
    SUM(
        CASE WHEN pcount.LobbySize BETWEEN 3 AND 4
             AND a.EndSkillMu > a.StartingSkillMu
        THEN 1 ELSE 0 END
    ) AS WinsSmallLobby,

    -- Large Lobby Wins (5+ players)
    SUM(
        CASE WHEN pcount.LobbySize >= 5
             AND a.EndSkillMu > a.StartingSkillMu
        THEN 1 ELSE 0 END
    ) AS WinsLargeLobby,
	SUM(CASE WHEN pcount.LobbySize=2 and a.FinalPosition = 1 THEN 1 ELSE 0 END) AS FirstPlaceFinishes1v1,
	SUM(CASE WHEN pcount.LobbySize<5 and pcount.LobbySize>2 and a.FinalPosition = 1 THEN 1 ELSE 0 END) AS FirstPlaceFinishesSmallLobby,
	SUM(CASE WHEN pcount.LobbySize>=5 and a.FinalPosition = 1 THEN 1 ELSE 0 END) AS FirstPlaceFinishesLargeLobby,
	SUM(CASE WHEN a.Modifier = 'spade' THEN a.FinalPosition ELSE 0 END) / SUM(CASE WHEN a.Modifier = 'spade' THEN 1 ELSE 0 END) AS AveragePositionSpade,
	SUM(CASE WHEN a.Modifier = 'diamond' THEN a.FinalPosition ELSE 0 END) / SUM(CASE WHEN a.Modifier = 'diamond' THEN 1 ELSE 0 END) AS AveragePositionDiamond,
	SUM(CASE WHEN a.Modifier = 'heart' THEN a.FinalPosition ELSE 0 END) / SUM(CASE WHEN a.Modifier = 'heart' THEN 1 ELSE 0 END) AS AveragePositionHeart,
	SUM(CASE WHEN a.Modifier = 'club' THEN a.FinalPosition ELSE 0 END) / SUM(CASE WHEN a.Modifier = 'club' THEN 1 ELSE 0 END) AS AveragePositionClub,
	SUM(CASE WHEN a.Modifier = 'spade' and pcount.LobbySize = 2 THEN a.FinalPosition ELSE 0 END) / SUM(CASE WHEN a.Modifier = 'spade' and pcount.LobbySize = 2 THEN 1 ELSE 0 END) AS AveragePosition1v1Spade,
	SUM(CASE WHEN a.Modifier = 'diamond' and pcount.LobbySize = 2 THEN a.FinalPosition ELSE 0 END) / SUM(CASE WHEN a.Modifier = 'diamond' and pcount.LobbySize = 2 THEN 1 ELSE 0 END) AS AveragePosition1v1Diamond,
	SUM(CASE WHEN a.Modifier = 'heart' and pcount.LobbySize = 2 THEN a.FinalPosition ELSE 0 END) / SUM(CASE WHEN a.Modifier = 'heart' and pcount.LobbySize = 2 THEN 1 ELSE 0 END) AS AveragePosition1v1Heart,
	SUM(CASE WHEN a.Modifier = 'club' and pcount.LobbySize = 2 THEN a.FinalPosition ELSE 0 END) / SUM(CASE WHEN a.Modifier = 'club' and pcount.LobbySize = 2 THEN 1 ELSE 0 END) AS AveragePosition1v1Club,
	SUM(CASE WHEN a.Modifier = 'spade' and pcount.LobbySize > 2 and pcount.LobbySize < 5 THEN a.FinalPosition ELSE 0 END) / SUM(CASE WHEN a.Modifier = 'spade' and pcount.LobbySize > 2 and pcount.LobbySize < 5 THEN 1 ELSE 0 END) AS AveragePositionSmallLobbySpade,
	SUM(CASE WHEN a.Modifier = 'diamond' and pcount.LobbySize > 2 and pcount.LobbySize < 5 THEN a.FinalPosition ELSE 0 END) / SUM(CASE WHEN a.Modifier = 'diamond' and pcount.LobbySize > 2 and pcount.LobbySize < 5 THEN 1 ELSE 0 END) AS AveragePositionSmallLobbyDiamond,
	SUM(CASE WHEN a.Modifier = 'heart' and pcount.LobbySize > 2 and pcount.LobbySize < 5 THEN a.FinalPosition ELSE 0 END) / SUM(CASE WHEN a.Modifier = 'heart' and pcount.LobbySize > 2 and pcount.LobbySize < 5 THEN 1 ELSE 0 END) AS AveragePositionSmallLobbyHeart,
	SUM(CASE WHEN a.Modifier = 'club' and pcount.LobbySize > 2 and pcount.LobbySize < 5 THEN a.FinalPosition ELSE 0 END) / SUM(CASE WHEN a.Modifier = 'club' and pcount.LobbySize > 2 and pcount.LobbySize < 5 THEN 1 ELSE 0 END) AS AveragePositionSmallLobbyClub,
	SUM(CASE WHEN a.Modifier = 'spade' and pcount.LobbySize >= 5 THEN a.FinalPosition ELSE 0 END) / SUM(CASE WHEN a.Modifier = 'spade' and pcount.LobbySize >= 5 THEN 1 ELSE 0 END) AS AveragePositionLargeLobbySpade,
	SUM(CASE WHEN a.Modifier = 'diamond' and pcount.LobbySize >= 5 THEN a.FinalPosition ELSE 0 END) / SUM(CASE WHEN a.Modifier = 'diamond' and pcount.LobbySize >= 5 THEN 1 ELSE 0 END) AS AveragePositionLargeLobbyDiamond,
	SUM(CASE WHEN a.Modifier = 'heart' and pcount.LobbySize >= 5 THEN a.FinalPosition ELSE 0 END) / SUM(CASE WHEN a.Modifier = 'heart' and pcount.LobbySize >= 5 THEN 1 ELSE 0 END) AS AveragePositionLargeLobbyHeart,
	SUM(CASE WHEN a.Modifier = 'club' and pcount.LobbySize >= 5 THEN a.FinalPosition ELSE 0 END) / SUM(CASE WHEN a.Modifier = 'club' and pcount.LobbySize >= 5 THEN 1 ELSE 0 END) AS AveragePositionLargeLobbyClub,
	CASE 
        WHEN SUM(CASE WHEN a.Modifier = 'heart' and pcount.LobbySize = 2 THEN 1 END) = 0 THEN NULL
        ELSE (
            CAST(SUM(CASE WHEN a.Modifier = 'heart' and pcount.LobbySize = 2 AND a.EndSkillMu > a.StartingSkillMu THEN 1 END) AS FLOAT)
            / CAST(SUM(CASE WHEN a.Modifier = 'heart' and pcount.LobbySize = 2 THEN 1 END) AS FLOAT)
        ) * 100
    END AS WR1v1Heart,
	CASE 
        WHEN SUM(CASE WHEN a.Modifier = 'club' and pcount.LobbySize = 2 THEN 1 END) = 0 THEN NULL
        ELSE (
            CAST(SUM(CASE WHEN a.Modifier = 'club' and pcount.LobbySize = 2 AND a.EndSkillMu > a.StartingSkillMu THEN 1 END) AS FLOAT)
            / CAST(SUM(CASE WHEN a.Modifier = 'club' and pcount.LobbySize = 2 THEN 1 END) AS FLOAT)
        ) * 100
    END AS WR1v1Club,
	CASE 
        WHEN SUM(CASE WHEN a.Modifier = 'diamond' and pcount.LobbySize = 2 THEN 1 END) = 0 THEN NULL
        ELSE (
            CAST(SUM(CASE WHEN a.Modifier = 'diamond' and pcount.LobbySize = 2 AND a.EndSkillMu > a.StartingSkillMu THEN 1 END) AS FLOAT)
            / CAST(SUM(CASE WHEN a.Modifier = 'diamond' and pcount.LobbySize = 2 THEN 1 END) AS FLOAT)
        ) * 100
    END AS WR1v1Diamond,
	CASE 
        WHEN SUM(CASE WHEN a.Modifier = 'spade' and pcount.LobbySize = 2 THEN 1 END) = 0 THEN NULL
        ELSE (
            CAST(SUM(CASE WHEN a.Modifier = 'spade' and pcount.LobbySize = 2 AND a.EndSkillMu > a.StartingSkillMu THEN 1 END) AS FLOAT)
            / CAST(SUM(CASE WHEN a.Modifier = 'spade' and pcount.LobbySize = 2 THEN 1 END) AS FLOAT)
        ) * 100
    END AS WR1v1Spade,
	--
	CASE 
        WHEN SUM(CASE WHEN a.Modifier = 'heart' and pcount.LobbySize > 2 and pcount.LobbySize < 5 THEN 1 END) = 0 THEN NULL
        ELSE (
            CAST(SUM(CASE WHEN a.Modifier = 'heart' and pcount.LobbySize > 2 and pcount.LobbySize < 5 AND a.EndSkillMu > a.StartingSkillMu THEN 1 END) AS FLOAT)
            / CAST(SUM(CASE WHEN a.Modifier = 'heart' and pcount.LobbySize > 2 and pcount.LobbySize < 5 THEN 1 END) AS FLOAT)
        ) * 100
    END AS WRSmallLobbyHeart,
	CASE 
        WHEN SUM(CASE WHEN a.Modifier = 'club' and pcount.LobbySize > 2 and pcount.LobbySize < 5 THEN 1 END) = 0 THEN NULL
        ELSE (
            CAST(SUM(CASE WHEN a.Modifier = 'club' and pcount.LobbySize > 2 and pcount.LobbySize < 5 AND a.EndSkillMu > a.StartingSkillMu THEN 1 END) AS FLOAT)
            / CAST(SUM(CASE WHEN a.Modifier = 'club' and pcount.LobbySize > 2 and pcount.LobbySize < 5 THEN 1 END) AS FLOAT)
        ) * 100
    END AS WRSmallLobbyClub,
	CASE 
        WHEN SUM(CASE WHEN a.Modifier = 'diamond' and pcount.LobbySize > 2 and pcount.LobbySize < 5 THEN 1 END) = 0 THEN NULL
        ELSE (
            CAST(SUM(CASE WHEN a.Modifier = 'diamond' and pcount.LobbySize > 2 and pcount.LobbySize < 5 AND a.EndSkillMu > a.StartingSkillMu THEN 1 END) AS FLOAT)
            / CAST(SUM(CASE WHEN a.Modifier = 'diamond' and pcount.LobbySize > 2 and pcount.LobbySize < 5 THEN 1 END) AS FLOAT)
        ) * 100
    END AS WRSmallLobbyDiamond,
	CASE 
        WHEN SUM(CASE WHEN a.Modifier = 'spade' and pcount.LobbySize > 2 and pcount.LobbySize < 5 THEN 1 END) = 0 THEN NULL
        ELSE (
            CAST(SUM(CASE WHEN a.Modifier = 'spade' and pcount.LobbySize > 2 and pcount.LobbySize < 5 AND a.EndSkillMu > a.StartingSkillMu THEN 1 END) AS FLOAT)
            / CAST(SUM(CASE WHEN a.Modifier = 'spade' and pcount.LobbySize  > 2 and pcount.LobbySize < 5 THEN 1 END) AS FLOAT)
        ) * 100
    END AS WRSmallLobbySpade,
	--
	CASE 
        WHEN SUM(CASE WHEN a.Modifier = 'heart' and pcount.LobbySize >=5 THEN 1 END) = 0 THEN NULL
        ELSE (
            CAST(SUM(CASE WHEN a.Modifier = 'heart' and pcount.LobbySize >=5 AND a.EndSkillMu > a.StartingSkillMu THEN 1 END) AS FLOAT)
            / CAST(SUM(CASE WHEN a.Modifier = 'heart' and pcount.LobbySize >=5 THEN 1 END) AS FLOAT)
        ) * 100
    END AS WRLargeLobbyHeart,
	CASE 
        WHEN SUM(CASE WHEN a.Modifier = 'club' and pcount.LobbySize >=5 THEN 1 END) = 0 THEN NULL
        ELSE (
            CAST(SUM(CASE WHEN a.Modifier = 'club' and pcount.LobbySize >=5 AND a.EndSkillMu > a.StartingSkillMu THEN 1 END) AS FLOAT)
            / CAST(SUM(CASE WHEN a.Modifier = 'club' and pcount.LobbySize >=5 THEN 1 END) AS FLOAT)
        ) * 100
    END AS WRLargeLobbyClub,
	CASE 
        WHEN SUM(CASE WHEN a.Modifier = 'diamond' and pcount.LobbySize >=5 THEN 1 END) = 0 THEN NULL
        ELSE (
            CAST(SUM(CASE WHEN a.Modifier = 'diamond' and pcount.LobbySize >=5 AND a.EndSkillMu > a.StartingSkillMu THEN 1 END) AS FLOAT)
            / CAST(SUM(CASE WHEN a.Modifier = 'diamond' and pcount.LobbySize >=5 THEN 1 END) AS FLOAT)
        ) * 100
    END AS WRLargeLobbyDiamond,
	CASE 
        WHEN SUM(CASE WHEN a.Modifier = 'spade' and pcount.LobbySize >=5 THEN 1 END) = 0 THEN NULL
        ELSE (
            CAST(SUM(CASE WHEN a.Modifier = 'spade' and pcount.LobbySize >=5 AND a.EndSkillMu > a.StartingSkillMu THEN 1 END) AS FLOAT)
            / CAST(SUM(CASE WHEN a.Modifier = 'spade' and pcount.LobbySize >=5 THEN 1 END) AS FLOAT)
        ) * 100
    END AS WRLargeLobbySpade



FROM LiveRankedDicePlayers a
INNER JOIN LiveRankedDiceMatches m
    ON a.MatchID = m.ID
	
INNER JOIN (
    SELECT MatchID, COUNT(*) AS LobbySize
    FROM LiveRankedDicePlayers
    GROUP BY MatchID
) AS pcount
    ON pcount.MatchID = a.MatchID
GROUP BY a.UserID, m.GuildID;

CREATE TRIGGER if not exists trg_LLMEvaluations_to_ShadowListQueue
AFTER INSERT ON LLMEvaluations
BEGIN
    INSERT INTO ShadowListQueue (Question, GivenAnswer, UserAnswer, LLMResponse, ShadowAnswers)
    SELECT
        NEW.Question,
        ql.Answers,     
        NEW.UserAnswer,
        NEW.LLMResponse,
		ql.ShadowAnswers
    FROM QuestionList ql
    WHERE ql.ID = NEW.QuestionID;
END;