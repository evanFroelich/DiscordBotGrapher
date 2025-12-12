
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
GROUP BY a.UserID, m.GuildID