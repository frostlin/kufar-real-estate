DROP TABLE IF EXISTS tg_user CASCADE;
CREATE TABLE tg_user (
    id int NOT NULL,

    PRIMARY KEY (id)
);

DROP TABLE IF EXISTS search_url CASCADE;
CREATE TABLE search_url (
    url text NOT NULL,

    PRIMARY KEY (url)
);

DROP TABLE IF EXISTS user_search_url CASCADE;
CREATE TABLE user_search_url (
    user_id int NOT NULL,
    url text NOT NULL,
    alias text,

    FOREIGN KEY (url) REFERENCES search_url(url) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (user_id) REFERENCES tg_user(id) ON DELETE CASCADE ON UPDATE CASCADE,
    PRIMARY KEY (user_id, url)
);

DROP TABLE IF EXISTS estate CASCADE;
CREATE TABLE estate (
    url text NOT NULL,
    image_url text,
    search_url text,
    price_usd int DEFAULT 0,
    price_byn int DEFAULT 0,
    price_usd_old int DEFAULT 0,
    room_count int DEFAULT 1,
    area float DEFAULT 0,
    address text,

    FOREIGN KEY (search_url) REFERENCES search_url(url) ON DELETE CASCADE ON UPDATE CASCADE,
    PRIMARY KEY (url)
);
DROP TABLE IF EXISTS user_estate CASCADE;
CREATE TABLE user_estate (
    url text NOT NULL,
    user_id int NOT NULL,
    is_followed boolean DEFAULT false,
    notification_status int DEFAULT 0, 
    
    FOREIGN KEY (url) REFERENCES estate(url) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (user_id) REFERENCES tg_user(id) ON DELETE CASCADE ON UPDATE CASCADE,
    PRIMARY KEY (url, user_id)
);

DROP VIEW IF IXESTS estates;
CREATE VIEW estates AS SELECT url, price_usd, price_usd_old, room_count, area, address, is_new, is_changed, is_sold FROM estate;
