-- One row per (place, browser). `voter` is a random id the browser makes up.
CREATE TABLE IF NOT EXISTS ratings (
  venue  TEXT    NOT NULL,
  voter  TEXT    NOT NULL,
  rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
  time   TEXT    NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (venue, voter)
);
CREATE INDEX IF NOT EXISTS ratings_voter ON ratings (voter);
