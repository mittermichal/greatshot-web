BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS `renders` (
	`id`	INTEGER NOT NULL,
	`celery_id`	VARCHAR ( 50 ),
	`streamable_short`	VARCHAR ( 8 ),
	`title`	VARCHAR ( 255 ),
	`gtv_match_id`	INTEGER,
	`client_num`	INTEGER,
	`map_number`	INTEGER,
	`player_id`	INTEGER,
	PRIMARY KEY(`id`),
	CONSTRAINT `fk_renders_player_id_players` FOREIGN KEY(`player_id`) REFERENCES `players`(`id`)
);
CREATE TABLE IF NOT EXISTS `players` (
	`id`	INTEGER NOT NULL,
	`name`	VARCHAR ( 255 ),
	`country`	VARCHAR ( 5 ),
	PRIMARY KEY(`id`)
);
CREATE TABLE IF NOT EXISTS `player` (
	`dwSeq`	integer PRIMARY KEY AUTOINCREMENT,
	`szMd5`	varchar ( 32 ) NOT NULL,
	`szName`	varchar ( 128 ) NOT NULL,
	`szCleanName`	varchar ( 64 ) NOT NULL,
	`bClientNum`	smallint NOT NULL,
	`szInfoString`	varchar ( 256 ) NOT NULL,
	`bTeam`	smallint NOT NULL,
	`bTVClient`	tinyint NOT NULL
);
CREATE TABLE IF NOT EXISTS `matches` (
	`id`	INTEGER NOT NULL,
	`gamestv_id`	INTEGER,
	`title`	VARCHAR ( 255 ),
	PRIMARY KEY(`id`)
);
CREATE TABLE IF NOT EXISTS `match_players` (
	`id`	INTEGER NOT NULL,
	`gtv_match_id`	INTEGER,
	`client_num`	INTEGER,
	`player_id`	INTEGER,
	PRIMARY KEY(`id`),
	FOREIGN KEY(`player_id`) REFERENCES `players`(`id`),
	FOREIGN KEY(`player_id`) REFERENCES `players`(`id`)
);
CREATE TABLE IF NOT EXISTS `maps` (
	`id`	INTEGER NOT NULL,
	`match_id`	INTEGER,
	`map_name`	VARCHAR ( 50 ),
	PRIMARY KEY(`id`)
);
CREATE TABLE IF NOT EXISTS `demo` (
	`dwSeq`	integer PRIMARY KEY AUTOINCREMENT,
	`szMd5`	varchar ( 32 ) NOT NULL,
	`szName`	varchar ( 64 ) NOT NULL,
	`szMapName`	varchar ( 64 ) NOT NULL,
	`szPOVName`	varchar ( 64 ) NOT NULL,
	`szTeamA`	varchar ( 128 ) NOT NULL,
	`szTeamB`	varchar ( 128 ) NOT NULL,
	`szServerConfig`	text NOT NULL,
	`dwScanTime`	integer NOT NULL,
	`dwPlayerCount`	integer NOT NULL,
	`dwObitCount`	integer NOT NULL,
	`dwBulletCount`	integer NOT NULL,
	`dwChatCount`	integer NOT NULL,
	`dwFrameCount`	integer NOT NULL,
	`bPOVId`	smallint NOT NULL,
	`bIsTVDemo`	smallint NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS `ix_renders_celery_id` ON `renders` (
	`celery_id`
);
CREATE UNIQUE INDEX IF NOT EXISTS `ix_matches_gamestv_id` ON `matches` (
	`gamestv_id`
);
CREATE INDEX IF NOT EXISTS `ix_maps_match_id` ON `maps` (
	`match_id`
);
CREATE INDEX IF NOT EXISTS `IX_player` ON `player` (
	`szMd5`
);
CREATE INDEX IF NOT EXISTS `IX_demo` ON `demo` (
	`szMd5`
);
COMMIT;
