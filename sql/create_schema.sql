-- Create the schema only if it doesn't already exist
CREATE SCHEMA IF NOT EXISTS raw;

-- Create tables only if they don't already exist
CREATE TABLE IF NOT EXISTS raw.exchange_rates (
    id              SERIAL PRIMARY KEY,
    base_currency   VARCHAR(3) NOT NULL,
    target_currency VARCHAR(3) NOT NULL,
    rate            NUMERIC(18, 6) NOT NULL,
    rate_date       DATE NOT NULL,
    source          VARCHAR(50) DEFAULT 'frankfurter',
    loaded_at       TIMESTAMP DEFAULT NOW(),
    UNIQUE (base_currency, target_currency, rate_date)
);

CREATE TABLE IF NOT EXISTS raw.inflation (
    id         SERIAL PRIMARY KEY,
    country    VARCHAR(10) NOT NULL,
    year       INT NOT NULL,
    inflation  NUMERIC(18, 14),
    source     VARCHAR(50) DEFAULT 'worldbank',
    loaded_at  TIMESTAMP DEFAULT NOW(),
    UNIQUE (country, year)
);

CREATE TABLE IF NOT EXISTS raw.interest_rates (
    id        SERIAL PRIMARY KEY,
    country   VARCHAR(10) NOT NULL,
    year      INT NOT NULL, 
    rate_type VARCHAR(50) NOT NULL DEFAULT 'deposit',
    rate_pct  NUMERIC(18, 14),
    source    VARCHAR(50) DEFAULT 'worldbank',
    loaded_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(country, year, rate_type)
);

CREATE TABLE IF NOT EXISTS raw.ngx_asi (
    id         SERIAL PRIMARY KEY,
    index_date DATE NOT NULL UNIQUE,
    asi_value  NUMERIC(14, 2) NOT NULL,
    source     VARCHAR(50) DEFAULT 'ngxpulse',
    loaded_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw.gold_prices (
    id         SERIAL PRIMARY KEY,
    price_date DATE NOT NULL UNIQUE,
    close_usd  NUMERIC(10, 2) NOT NULL,
    source     VARCHAR(50) NOT NULL,
    loaded_at  TIMESTAMP DEFAULT NOW()
);