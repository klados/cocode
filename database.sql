create database if not exists cocode;

drop table if exists projects;
drop table if exists users;

create table if not exists users(
id int(11) not null auto_increment,
username varchar(35) not null unique,
fullname varchar(50) not null,
deleted varchar(1) default '0',
registrationDate datetime default current_timestamp,
companyName varchar(35) default null,
email varchar(35) not null unique,
password varchar(100) not null,
primary key(id)

)ENGINE=InnoDB;

create table if not exists projects(
	id int(11) not null auto_increment,
	title varchar(50) not null, 
	owner_email varchar(50) not null,
	src_code text,
	language varchar(35) default null,
	created_day datetime Default current_timestamp,
	updated_dayt datetime Default current_timestamp,
	description varchar(200) default null,
	primary key(id),
	FOREIGN KEY (owner_email) REFERENCES users (email)
)ENGINE=InnoDB;
