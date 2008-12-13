ALTER TABLE accounting_account ADD short_name varchar(100) NOT NULL DEFAULT '';
ALTER TABLE reports_list ADD short_name_width smallint CHECK ("balance_width" >= 0) NOT NULL DEFAULT 0;
ALTER TABLE reports_list DROP COLUMN use_username;
