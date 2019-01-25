['C:\\Users\\admin\\AppData\\Local\\Programs\\Python\\Python35-32\\Scripts', 'C:\\Users\\admin\\Documents\\et\\gtv', 'c:\\users\\admin\\appdata\\local\\programs\\python\\python35-32\\python35.zip', 'c:\\users\\admin\\appdata\\local\\programs\\python\\python35-32\\DLLs', 'c:\\users\\admin\\appdata\\local\\programs\\python\\python35-32\\lib', 'c:\\users\\admin\\appdata\\local\\programs\\python\\python35-32', 'c:\\users\\admin\\appdata\\local\\programs\\python\\python35-32\\lib\\site-packages']
CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> e361d65f075c

ALTER TABLE renders ADD COLUMN title VARCHAR(255);

INSERT INTO alembic_version (version_num) VALUES ('e361d65f075c');

-- Running upgrade e361d65f075c -> 45aa7927492c

CREATE TABLE maps (
    id INTEGER NOT NULL, 
    match_id INTEGER, 
    map_name VARCHAR(50), 
    CONSTRAINT pk_maps PRIMARY KEY (id)
);

CREATE INDEX ix_maps_match_id ON maps (match_id);

CREATE TABLE matches (
    id INTEGER NOT NULL, 
    gamestv_id INTEGER, 
    title VARCHAR(255), 
    CONSTRAINT pk_matches PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_matches_gamestv_id ON matches (gamestv_id);

UPDATE alembic_version SET version_num='45aa7927492c' WHERE alembic_version.version_num = 'e361d65f075c';

-- Running upgrade 45aa7927492c -> a3b2622bc481

ALTER TABLE renders ADD COLUMN gtv_match_id INTEGER;

UPDATE alembic_version SET version_num='a3b2622bc481' WHERE alembic_version.version_num = '45aa7927492c';

-- Running upgrade a3b2622bc481 -> b795470cf5b7

ALTER TABLE renders ADD COLUMN client_num INTEGER;

ALTER TABLE renders ADD COLUMN map_number INTEGER;

UPDATE alembic_version SET version_num='b795470cf5b7' WHERE alembic_version.version_num = 'a3b2622bc481';

-- Running upgrade b795470cf5b7 -> e4800e6be8b1

CREATE TABLE players (
    id INTEGER NOT NULL, 
    name VARCHAR(255), 
    country VARCHAR(5), 
    player_id INTEGER, 
    CONSTRAINT pk_players PRIMARY KEY (id), 
    CONSTRAINT fk_players_player_id_players FOREIGN KEY(player_id) REFERENCES players (id)
);

UPDATE alembic_version SET version_num='e4800e6be8b1' WHERE alembic_version.version_num = 'b795470cf5b7';

-- Running upgrade e4800e6be8b1 -> 831471f4db93

CREATE TABLE match_players (
    id INTEGER NOT NULL, 
    gtv_match_id INTEGER, 
    client_num INTEGER, 
    player_id INTEGER, 
    CONSTRAINT pk_match_players PRIMARY KEY (id), 
    CONSTRAINT fk_match_players_player_id_players FOREIGN KEY(player_id) REFERENCES players (id), 
    CONSTRAINT fk_match_players_player_id_players FOREIGN KEY(player_id) REFERENCES players (id)
);

UPDATE alembic_version SET version_num='831471f4db93' WHERE alembic_version.version_num = 'e4800e6be8b1';

-- Running upgrade 831471f4db93 -> 3719fb5b193a

