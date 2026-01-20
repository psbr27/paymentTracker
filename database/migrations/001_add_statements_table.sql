-- Migration: Add statements table for bank statement analysis feature
-- Run this on existing databases that don't have the statements table

-- Check if table exists before creating
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'statements') THEN
        -- Create statements table
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

        -- Create indexes
        CREATE INDEX idx_statements_user_id ON statements(user_id);
        CREATE INDEX idx_statements_period ON statements(period_start, period_end);
        CREATE INDEX idx_statements_bank ON statements(bank_name);

        -- Create trigger for updated_at
        CREATE TRIGGER update_statements_updated_at
            BEFORE UPDATE ON statements
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();

        RAISE NOTICE 'Created statements table with indexes and trigger';
    ELSE
        RAISE NOTICE 'statements table already exists, skipping';
    END IF;
END $$;
