drop table if exists InServerEmoji;
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

drop table if exists OutOfServerEmoji;
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

