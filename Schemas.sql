create table if not exists Master(
 GuildName text,
 GuildID text,
 UserName text,
 UserID text,
 ChannelName text,
 ChannelID text,
 UTCTime text,
 BonusCol text
);


create table if not exists InServerEmoji(
 GuildName text,
 GuildID text,
 UserName text,
 UserID text,
 ChannelName text,
 ChannelID text,
 UTCTime text,
 EmojiID text,
 EmojiName text,
 AnimatedFlag text
);


create table if not exists OutOfServerEmoji(
 GuildName text,
 GuildID text,
 UserName text,
 UserID text,
 ChannelName text,
 ChannelID text,
 UTCTime text,
 EmojiID text,
 EmojiName text,
 AnimatedFlag text
);


create table if not exists ServerSettings (
    GuildID    TEXT UNIQUE,
    TopChatTracking    INTEGER DEFAULT 0,
    PatchNotes    INTEGER DEFAULT 0,
    PRIMARY KEY(GuildID)
);


CREATE TABLE  if not exists TopChatSettings (
    GuildID    TEXT UNIQUE,
    NumberToTrack    INTEGER,
    RefreshCadence    INTEGER,
    LookbackDistance    TEXT,
    PRIMARY KEY(GuildID)
);


CREATE TABLE if not exists TopChatData (
    GuildID    TEXT,
    Position    INTEGER,
    UserID    INTEGER,
    Count    INTEGER,
    PRIMARY KEY(GuildID,Position)
);

CREATE TABLE if not exists PatchNotesSettings(
    GuildID    TEXT UNIQUE,
    ChannelID    INTEGER,
    PRIMARY KEY(GuildID)
);

