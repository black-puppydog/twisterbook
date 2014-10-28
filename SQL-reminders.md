Some things I am too forgetful to remember.
Probably not production ready, but for my local server it kinda works for now :P

# connect to database
mysql -h 127.0.0.1 -u root --password=<pwroot>

# creating database
CREATE DATABASE twister;

# creating user with access to database
CREATE USER 'twister'@'%' IDENTIFIED BY '<pwtwister>';
GRANT ALL ON twister.* TO 'twister'@'%';

# create tables
CREATE TABLE users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username CHAR(20) CHARACTER SET utf8 COLLATE utf8_bin,
    last_indexed_k INT,
    last_indexed_time TIMESTAMP,
    json MEDIUMTEXT CHARACTER SET utf8 COLLATE utf8_bin
);

CREATE TABLE posts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    userid BIGINT,
    k INT,
    time TIMESTAMP NOT NULL,
    ms CHAR(200) CHARACTER SET utf8 COLLATE utf8_bin,
    reply_to BIGINT NULL,
    rt_of BIGINT NULL,
    json MEDIUMTEXT CHARACTER SET utf8 COLLATE utf8_bin,

    FOREIGN KEY (userid) REFERENCES users(id),
    FOREIGN KEY (reply_to) REFERENCES posts(id),
    FOREIGN KEY (rt_of) REFERENCES posts(id)
);
