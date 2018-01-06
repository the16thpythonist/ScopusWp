
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
  authors TEXT,
  keywords TEXT,
  citations TEXT
);
CREATE UNIQUE INDEX publications_scopus_id_uindex ON publications (scopus_id);
CREATE UNIQUE INDEX publications_eid_uindex ON publications (eid);
CREATE UNIQUE INDEX publications doi_unidex ON publications (doi);