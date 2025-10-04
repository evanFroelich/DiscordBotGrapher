-- Step 1: Drop the dependent view if it exists
DROP VIEW IF EXISTS GamblingUnlockMetricsView;

-- Step 2: Rename the temporary table to replace the original
ALTER TABLE sqlb_temp_table_8 RENAME TO GamblingUserStats;

-- Step 3: Recreate the view based on the new GamblingUserStats table
CREATE VIEW GamblingUnlockMetricsView AS
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
