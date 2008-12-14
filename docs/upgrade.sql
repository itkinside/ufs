ALTER TABLE accounting_account ADD short_name varchar(100) NOT NULL DEFAULT '';
ALTER TABLE reports_list ADD short_name_width smallint CHECK ("balance_width" >= 0) NOT NULL DEFAULT 0;
ALTER TABLE reports_list DROP COLUMN use_username;

CREATE TABLE "reports_list_user_accounts" (
    "id" serial NOT NULL PRIMARY KEY,
    "list_id" integer NOT NULL REFERENCES "reports_list" ("id") DEFERRABLE INITIALLY DEFERRED,
    "account_id" integer NOT NULL REFERENCES "accounting_account" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("list_id", "account_id")
);

CREATE TABLE "reports_list_group_accounts" (
    "id" serial NOT NULL PRIMARY KEY,
    "list_id" integer NOT NULL REFERENCES "reports_list" ("id") DEFERRABLE INITIALLY DEFERRED,
    "account_id" integer NOT NULL REFERENCES "accounting_account" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("list_id", "account_id")
);

INSERT INTO reports_list_user_accounts (list_id, account_id) SELECT list_id, account_id FROM reports_list_accounts;

DROP TABLE "reports_list_accounts";
