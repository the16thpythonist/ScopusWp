DROP TABLE reference;
DROP TABLE publications;
DROP TABLE publication_cache;
DROP TABLE author_cache;

CREATE TABLE reference
(
    id BIGINT PRIMARY KEY,
    wordpress_id BIGINT,
    scopus_id BIGINT
);
CREATE UNIQUE INDEX reference_id_uindex ON reference (id);
ALTER TABLE reference ENGINE=InnoDB;

CREATE TABLE citation_reference
(
    `internal _id` BIGINT PRIMARY KEY,
    wordpress_post_id BIGINT,
    wordpress_comment_id BIGINT,
    scopus_id BIGINT
);
CREATE UNIQUE INDEX citation_reference_wordpress_post_id_uindex ON citation_reference (wordpress_post_id);
ALTER TABLE citation_reference ENGINE=INNODB;

CREATE TABLE publications
(
  scopus_id BIGINT PRIMARY KEY NOT NULL,
  eid VARCHAR(64),
  doi VARCHAR(64),
  creator TEXT,
  title TEXT,
  description LONGTEXT,
  journal TEXT,
  volume VARCHAR(64),
  date VARCHAR(64),
  authors LONGTEXT,
  keywords TEXT,
  citations TEXT
);
CREATE UNIQUE INDEX publications_scopus_id_uindex ON publications (scopus_id);
CREATE UNIQUE INDEX publications_eid_uindex ON publications (eid);
CREATE UNIQUE INDEX publications_doi_unidex ON publications (doi);
ALTER TABLE publications ENGINE=InnoDB;

CREATE TABLE publication_cache
(
    scopus_id BIGINT PRIMARY KEY NOT NULL,
    eid VARCHAR(64),
    doi VARCHAR(64),
    creator TEXT,
    description LONGTEXT,
    title TEXT,
    journal TEXT,
    volume VARCHAR(32),
    keywords TEXT,
    date VARCHAR(32),
    citations TEXT,
    authors LONGTEXT
);
CREATE UNIQUE INDEX publication_cache_scopus_id_uindex ON publication_cache (scopus_id);
CREATE UNIQUE INDEX publication_cache_eid_uindex ON publication_cache (eid);
CREATE UNIQUE INDEX publication_cache_doi_uindex ON publication_cache (doi);
ALTER TABLE publication_cache ENGINE=InnoDB;

CREATE TABLE author_cache
(
    author_id BIGINT PRIMARY KEY NOT NULL,
    first_name TEXT,
    last_name TEXT,
    h_index INT,
    citation_count INT,
    document_count INT,
    publications TEXT
);
CREATE UNIQUE INDEX author_cache_author_id_uindex ON author_cache (author_id);