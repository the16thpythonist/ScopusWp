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

CREATE TABLE publications(
  scopus_id BIGINT PRIMARY KEY,
  eid VARCHAR(32),
  doi VARCHAR(32),
  creator TEXT,
  title TEXT,
  description TEXT,
  journal VARCHAR(64),
  volume VARCHAR(32),
  date VARCHAR(32),
  authors LONGTEXT,
  keywords TEXT,
  citations TEXT
);
CREATE UNIQUE INDEX publications_scopus_id_uindex ON publications (scopus_id);
CREATE UNIQUE INDEX publications_eid_uindex ON publications (eid);
CREATE UNIQUE INDEX publications_doi_unidex ON publications (doi);

CREATE TABLE publication_cache
(
    scopus_id BIGINT PRIMARY KEY NOT NULL,
    eid VARCHAR(32),
    doi VARCHAR(32),
    creator TEXT,
    description TEXT,
    title TEXT,
    journal VARCHAR(64),
    volume VARCHAR(32),
    keywords TEXT,
    date VARCHAR(32),
    citations TEXT,
    authors LONGTEXT
);
CREATE UNIQUE INDEX publication_cache_scopus_id_uindex ON publication_cache (scopus_id);
CREATE UNIQUE INDEX publication_cache_eid_uindex ON publication_cache (eid);
CREATE UNIQUE INDEX publication_cache_doi_uindex ON publication_cache (doi);

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