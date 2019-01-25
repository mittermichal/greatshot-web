BEGIN TRANSACTION;
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
CREATE INDEX IF NOT EXISTS `IX_demo` ON `demo` (
	`szMd5`
);
COMMIT;
