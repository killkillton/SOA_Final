-- Initialize the 6 logical databases (one per microservice) in the single PostgreSQL instance.
-- Mounted at /docker-entrypoint-initdb.d/01-init-databases.sql and executed automatically
-- when the PostgreSQL data volume is first initialized.

CREATE DATABASE auth_db;
CREATE DATABASE room_inventory_db;
CREATE DATABASE reservation_db;
CREATE DATABASE payment_db;
CREATE DATABASE stay_db;
CREATE DATABASE notification_db;
