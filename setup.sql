# Creating the database for all the tables
CREATE DATABASE scopus;
USE scopus;

CREATE TABLE reference(
  id BIGINT,
  wordpress_id BIGINT,
  scopus_id BIGINT
);


CREATE TABLE publications(
  scopus_id BIGINT,
  eid VARCHAR(32),
  doi VARCHAR(32),
  creator TEXT,
  title TEXT,
  description TEXT,
  journal VARCHAR(64),
  volume VARCHAR(32),
  date VARCHAR(32),
  authors TEXT,
  keywords TEXT,
  citations TEXT
);