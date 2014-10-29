Some things I am too forgetful to remember.
Probably not production ready, but for my local server it kinda works for now :P

# pull docker repo and spin up the container
docker pull mysql
run --name twister-mysql -p 127.0.0.1:3306:3306 -e MYSQL_ROOT_PASSWORD=<pwroot> -d mysql

# connect to database
mysql -h 127.0.0.1 -u root --password=<pwroot>

# creating database
CREATE DATABASE twister;

# creating user with access to database
CREATE USER 'twister'@'%' IDENTIFIED BY '<pwtwister>';
GRANT ALL ON twister.* TO 'twister'@'%';

then disconnect from the database

# connect as twister user
mysql -h 127.0.0.1 -u twister --password=<pwtwister> twister

# create tables
CREATE TABLE users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username CHAR(20) CHARACTER SET utf8 COLLATE utf8_bin UNIQUE,
    last_indexed_k INT,
    last_indexed_time TIMESTAMP,
    json MEDIUMTEXT CHARACTER SET utf8 COLLATE utf8_bin
);

CREATE TABLE posts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    userid BIGINT,
    k INT,
    post_type CHAR(6) NOT NULL,
    time TIMESTAMP NOT NULL,
    msg CHAR(200) CHARACTER SET utf8 COLLATE utf8_bin,
    parent_post_username CHAR(16) NULL,
    parent_post_k INT NULL,
    json MEDIUMTEXT CHARACTER SET utf8 COLLATE utf8_bin,
    FOREIGN KEY (userid) REFERENCES users(id),
    UNIQUE unique_index(userid, k)
);

CREATE TABLE blocks(
    height BIGINT PRIMARY KEY,
    hash CHAR(65) NOT NULL,
    user_registrations INT NOT NULL,
    json TEXT NOT NULL
);

