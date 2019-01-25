BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS `roundstats` (
	`dwSeq`	integer PRIMARY KEY AUTOINCREMENT,
	`szMd5`	varchar ( 32 ) NOT NULL,
	`bRound`	varchar ( 128 ) NOT NULL,
	`szTimeToBeat`	varchar ( 32 ) NOT NULL,
	`szStats`	varchar ( 512 ) NOT NULL
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
CREATE TABLE IF NOT EXISTS `obituary` (
	`dwSeq`	integer PRIMARY KEY AUTOINCREMENT,
	`szMd5`	varchar ( 32 ) NOT NULL,
	`bAttacker`	smallint NOT NULL,
	`bTarget`	smallint NOT NULL,
	`bWeapon`	smallint NOT NULL,
	`dwTime`	integer NOT NULL,
	`bIsTeamkill`	tinyint NOT NULL,
	`szTimeString`	varchar ( 32 ) NOT NULL,
	`szMessage`	varchar ( 256 ) NOT NULL
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
CREATE TABLE IF NOT EXISTS `chatmessage` (
	`dwSeq`	integer PRIMARY KEY AUTOINCREMENT,
	`szMd5`	varchar ( 32 ) NOT NULL,
	`szMessage`	varchar ( 512 ) NOT NULL,
	`bPlayer`	smallint NOT NULL,
	`dwTime`	integer NOT NULL,
	`szTimeString`	varchar ( 32 ) NOT NULL,
	`szChatIdent`	varchar ( 8 ) NOT NULL
);
CREATE TABLE IF NOT EXISTS `bulletevent` (
	`dwSeq`	integer PRIMARY KEY AUTOINCREMENT,
	`szMd5`	varchar ( 32 ) NOT NULL,
	`bRegion`	smallint NOT NULL,
	`bTarget`	smallint NOT NULL,
	`bAttacker`	smallint NOT NULL,
	`dwTime`	integer NOT NULL
);
CREATE INDEX IF NOT EXISTS `IX_roundstats` ON `roundstats` (
	`szMd5`
);
CREATE INDEX IF NOT EXISTS `IX_player` ON `player` (
	`szMd5`
);
CREATE INDEX IF NOT EXISTS `IX_obituary` ON `obituary` (
	`szMd5`
);
CREATE INDEX IF NOT EXISTS `IX_demo` ON `demo` (
	`szMd5`
);
CREATE INDEX IF NOT EXISTS `IX_chatMessage` ON `chatmessage` (
	`szMd5`
);
CREATE INDEX IF NOT EXISTS `IX_bulletevent` ON `bulletevent` (
	`szMd5`
);
COMMIT;
