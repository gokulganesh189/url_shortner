-- URL Shortener Database Schema
-- This file runs automatically when MySQL container starts for the first time

CREATE DATABASE IF NOT EXISTS urlshortener;
USE urlshortener;

-- Main table storing all shortened URLs
CREATE TABLE IF NOT EXISTS urls (
    id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,  -- This ID gets base62-encoded into the short code
    short_code  VARCHAR(20)  NOT NULL UNIQUE,               -- e.g. "3xK9mP"
    long_url    TEXT         NOT NULL,                      -- the original URL
    created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
    expires_at  DATETIME     DEFAULT NULL,                  -- NULL means never expires
    click_count BIGINT       DEFAULT 0,                     -- how many times this link was visited
    
    INDEX idx_short_code (short_code),                      -- fast lookup by short code
    INDEX idx_created_at (created_at)
);

-- Click analytics table (each redirect logs one row here)
CREATE TABLE IF NOT EXISTS clicks (
    id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    short_code  VARCHAR(20)  NOT NULL,
    clicked_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
    user_agent  VARCHAR(500) DEFAULT NULL,                  -- browser/device info
    ip_address  VARCHAR(45)  DEFAULT NULL,                  -- IPv4 or IPv6
    
    INDEX idx_short_code (short_code),
    INDEX idx_clicked_at (clicked_at)
);