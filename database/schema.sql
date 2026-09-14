CREATE DATABASE IF NOT EXISTS frauddetection
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'fraud_gateway_user'@'localhost' IDENTIFIED BY 'change-me-local-password';
GRANT ALL PRIVILEGES ON frauddetection.* TO 'fraud_gateway_user'@'localhost';

USE frauddetection;

CREATE TABLE IF NOT EXISTS scored_transactions (
    id BIGINT NOT NULL AUTO_INCREMENT,
    transaction_id VARCHAR(36) NOT NULL,
    timestamp TIMESTAMP(6) NOT NULL,
    amount DOUBLE NOT NULL,
    step INT NULL,
    type VARCHAR(32) NULL,
    old_balance_dest DOUBLE NOT NULL DEFAULT 0,
    new_balance_dest DOUBLE NOT NULL DEFAULT 0,
    transaction_velocity DOUBLE NOT NULL DEFAULT 0,
    amount_deviation DOUBLE NOT NULL DEFAULT 0,
    balance_discrepancy DOUBLE NOT NULL DEFAULT 0,
    biometric_risk_score DOUBLE NULL,
    source_account VARCHAR(64) NULL,
    destination_account VARCHAR(64) NULL,
    device_id VARCHAR(64) NULL,
    region VARCHAR(64) NULL,
    risk_score INT NULL,
    risk_level VARCHAR(32) NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    top_reason_codes TEXT NULL,
    raw_python_response TEXT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uk_scored_transactions_transaction_id (transaction_id)
) ENGINE=InnoDB;

ALTER TABLE scored_transactions
    ADD COLUMN IF NOT EXISTS step INT NULL,
    ADD COLUMN IF NOT EXISTS type VARCHAR(32) NULL,
    ADD COLUMN IF NOT EXISTS old_balance_dest DOUBLE NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS new_balance_dest DOUBLE NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS transaction_velocity DOUBLE NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS amount_deviation DOUBLE NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS balance_discrepancy DOUBLE NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS biometric_risk_score DOUBLE NULL,
    ADD COLUMN IF NOT EXISTS source_account VARCHAR(64) NULL,
    ADD COLUMN IF NOT EXISTS destination_account VARCHAR(64) NULL,
    ADD COLUMN IF NOT EXISTS device_id VARCHAR(64) NULL,
    ADD COLUMN IF NOT EXISTS region VARCHAR(64) NULL;

INSERT IGNORE INTO scored_transactions
(transaction_id, timestamp, amount, step, type, old_balance_dest, new_balance_dest,
 transaction_velocity, amount_deviation, balance_discrepancy, biometric_risk_score,
 source_account, destination_account, device_id, region, risk_score, risk_level,
 status, top_reason_codes, raw_python_response)
VALUES
('LIVE-100001', NOW() - INTERVAL 3 HOUR, 450000.00, 14, 'TRANSFER', 0, 0, 18.5, 95, 450000, 82.0,
 'ACC-100234', 'DEST-900001', 'DEV-8F6A21C9', 'New York', 94, 'high', 'COMPLETED',
 '[{"feature":"amount_deviation","impact":0.42}]', '{"seeded":true,"risk_score":94}'),
('LIVE-100002', NOW() - INTERVAL 2 HOUR, 8750.00, 3, 'CASH_OUT', 12000, 3250, 4.2, 22, 8750, 35.0,
 'ACC-100234', 'DEST-900002', 'DEV-8F6A21C9', 'New York', 48, 'medium', 'COMPLETED',
 '[{"feature":"transaction_velocity","impact":0.42}]', '{"seeded":true,"risk_score":48}'),
('LIVE-100003', NOW() - INTERVAL 1 HOUR, 45.50, 1, 'PAYMENT', 1200, 1154.50, 0.5, 0.1, 0, 8.0,
 'ACC-100556', 'DEST-900003', 'DEV-572418', 'Boston', 6, 'low', 'COMPLETED',
 '[{"feature":"balance_discrepancy","impact":0.42}]', '{"seeded":true,"risk_score":6}'),
('LIVE-100004', NOW() - INTERVAL 35 MINUTE, 3200.00, 8, 'TRANSFER', 7000, 3800, 7.1, 58, 3200, 64.0,
 'ACC-100789', 'DEST-900002', 'DEV-572418', 'Boston', 76, 'high', 'COMPLETED',
 '[{"feature":"amount_deviation","impact":0.42}]', '{"seeded":true,"risk_score":76}'),
('LIVE-100005', NOW() - INTERVAL 12 MINUTE, 125.50, 2, 'PAYMENT', 850, 724.50, 0.8, 2.4, 0, 5.0,
 'ACC-100556', 'DEST-900004', 'DEV-572418', 'Boston', 12, 'low', 'COMPLETED',
 '[{"feature":"transaction_velocity","impact":0.42}]', '{"seeded":true,"risk_score":12}');
