-- Payment Tracker Database Schema

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create ENUM types
CREATE TYPE currency_type AS ENUM ('USD', 'INR');
CREATE TYPE category_type AS ENUM ('LOAN', 'SUBSCRIPTION', 'INVESTMENT', 'INSURANCE', 'UTILITY', 'OTHER');
CREATE TYPE recurrence_type AS ENUM ('MONTHLY', 'WEEKLY', 'BIWEEKLY', 'QUARTERLY', 'ANNUAL', 'ONETIME');

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    default_currency currency_type DEFAULT 'USD',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Payments table
CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    currency currency_type NOT NULL DEFAULT 'USD',
    category category_type NOT NULL DEFAULT 'OTHER',
    recurrence recurrence_type NOT NULL DEFAULT 'MONTHLY',
    day_of_month INTEGER CHECK (day_of_month >= 1 AND day_of_month <= 31),
    day_of_week INTEGER CHECK (day_of_week >= 0 AND day_of_week <= 6),
    start_date DATE NOT NULL,
    end_date DATE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Statements table (analyzed bank statements)
CREATE TABLE statements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    bank_name VARCHAR(100) NOT NULL,
    account_number_masked VARCHAR(20),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    original_filename VARCHAR(255),
    analysis JSONB NOT NULL,
    ai_model VARCHAR(100),
    ai_tokens_used INTEGER,
    ai_cost_estimate VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Exchange rates table
CREATE TABLE exchange_rates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    from_currency currency_type NOT NULL,
    to_currency currency_type NOT NULL,
    rate DECIMAL(10, 4) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(from_currency, to_currency)
);

-- Create indexes for better query performance
CREATE INDEX idx_payments_user_id ON payments(user_id);
CREATE INDEX idx_payments_start_date ON payments(start_date);
CREATE INDEX idx_payments_end_date ON payments(end_date);
CREATE INDEX idx_payments_category ON payments(category);
CREATE INDEX idx_statements_user_id ON statements(user_id);
CREATE INDEX idx_statements_period ON statements(period_start, period_end);
CREATE INDEX idx_statements_bank ON statements(bank_name);

-- Insert default exchange rates
INSERT INTO exchange_rates (from_currency, to_currency, rate) VALUES
    ('USD', 'INR', 83.50),
    ('INR', 'USD', 0.012);

-- Insert default admin user
-- Password: changeme123 (bcrypt hash)
INSERT INTO users (username, password_hash, default_currency) VALUES
    ('admin', '$2b$12$UTfxo6eYkpDeK7kiDX2eruFn7sbTXecZA3o9P2GWPXRY/lk6plgu2', 'USD');

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update updated_at on payments table
CREATE TRIGGER update_payments_updated_at
    BEFORE UPDATE ON payments
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger to auto-update updated_at on statements table
CREATE TRIGGER update_statements_updated_at
    BEFORE UPDATE ON statements
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
