drop table if exists StdSensorTypes;
drop table if exists Master;

create table StdSensorTypes (
 SensorCode text,
 SensorType text,
 SensorImage text
);

create table Master(
 GuildName text,
 GuildID text,
 UserName text,
 UserID text,
 ChannelName text,
 ChannelID text,
 UTCTime text,
 BonusCol text
);

INSERT INTO StdSensorTypes (SensorCode, SensorType) VALUES ("s0", "Temperature and Humidity Sensor: DHT22");
INSERT INTO StdSensorTypes (SensorCode, SensorType) VALUES ("s1", "Pressure Sensor: BMP180");
INSERT INTO StdSensorTypes (SensorCode, SensorType) VALUES ("s2", "Light Sensor: LDR");
INSERT INTO StdSensorTypes (SensorCode, SensorType) VALUES ("s3", "Door-Windows Sensor");