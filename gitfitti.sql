CREATE TABLE users (
  name TEXT PRIMARY KEY,
  password TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  auth TEXT DEFAULT NULL
);

CREATE TABLE graffiti (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL REFERENCES users(name),
  alias TEXT NOT NULL,
  repo TEXT NOT NULL,
  a INTEGER[][],
  nc INTEGER,
  year INTEGER,
  UNIQUE (name, alias)
);