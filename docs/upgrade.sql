-- Added shortnames to accounts which can be used on lists
ALTER TABLE accounting_account ADD short_name varchar(100) NOT NULL DEFAULT '';

-- Added short_name_width to control releative size of short_name on list
ALTER TABLE reports_list ADD short_name_width smallint CHECK ("balance_width" >= 0) NOT NULL DEFAULT 0;
-- Which in turn replaces the use_username option.
ALTER TABLE reports_list DROP COLUMN use_username;

-- Setting that should indicate if we should add all active acounts by default
ALTER TABLE reports_list ADD add_active_accounts boolean;

-- Additional accounts to add
ALTER TABLE reports_list_accounts RENAME TO reports_list_extra_accounts;

-- Use the following two lines if the database has been throught the
-- intermedatie state with group_accounts and user_accounts
-- ALTER TABLE reports_list_user_accounts RENAME TO reports_list_extra_accounts;
-- DROP TABLE reports_list_group_accounts;

ALTER TABLE accounting_account ADD group_account boolean;
UPDATE accounting_account set group_account = NOT (accounting_account.owner_id IS NOT NULL AND accounting_account.type = 'Li');
