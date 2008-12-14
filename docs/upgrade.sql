-- Added shortnames to accounts which can be used on lists
ALTER TABLE accounting_account ADD short_name varchar(100) NOT NULL DEFAULT '';

-- Added short_name_width to control releative size of short_name on list
ALTER TABLE reports_list ADD short_name_width smallint CHECK ("balance_width" >= 0) NOT NULL DEFAULT 0;
-- Which in turn replaces the use_username option.
ALTER TABLE reports_list DROP COLUMN use_username;

-- Changed table name to match django model and give more coherent naming (ref
-- next CREATE TABLE statement)
ALTER TABLE reports_list_accounts RENAME TO reports_list_user_accounts;

-- Add a table that should contain group accounts to show in addition to what
-- ever reports_list_user_accounts says
CREATE TABLE "reports_list_group_accounts" (
    "id" serial NOT NULL PRIMARY KEY,
    "list_id" integer NOT NULL REFERENCES "reports_list" ("id") DEFERRABLE INITIALLY DEFERRED,
    "account_id" integer NOT NULL REFERENCES "accounting_account" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("list_id", "account_id")
);
