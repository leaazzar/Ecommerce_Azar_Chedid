DROP TABLE IF EXISTS customer;

CREATE TABLE customer (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    age INTEGER,
    address TEXT,
    gender TEXT,
    marital_status TEXT,
    wallet REAL DEFAULT 0.0
);
