create table if not exists InServerEmoji(
 GuildName text,
 GuildID text,
 UserName text,
 UserID text,
 ChannelName text,
 ChannelID text,
 UTCTime text,
 EmojiID text,
 AnimatedFlag text
);

create table if not exists OutOfServerEmotji(
 GuildName text,
 GuildID text,
 UserName text,
 UserID text,
 ChannelName text,
 ChannelID text,
 UTCTime text,
 EmojiName text
);

