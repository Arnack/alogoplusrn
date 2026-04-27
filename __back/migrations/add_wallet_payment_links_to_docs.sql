ALTER TABLE contracts
    ADD COLUMN IF NOT EXISTS wallet_payment_id INTEGER REFERENCES wallet_payments(id) ON DELETE SET NULL;

ALTER TABLE worker_acts
    ADD COLUMN IF NOT EXISTS wallet_payment_id INTEGER REFERENCES wallet_payments(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_contracts_wallet_payment_id ON contracts(wallet_payment_id);
CREATE INDEX IF NOT EXISTS idx_worker_acts_wallet_payment_id ON worker_acts(wallet_payment_id);
