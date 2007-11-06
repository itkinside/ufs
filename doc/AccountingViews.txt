The accounting views
====================


First time login
----------------

1. Authentication is done externally with Kerberos and HTTP Basic Auth.
2. If the µFS views see a REMOTE_USER which does not exist as a User object, it
   should be created, and the user redirected to a page saying:

	"A µFS user was just created for you. Please ask your bar administrator
	to create a bar account for you and connect the account with your
	user."

Status: All done.


After login when account is assigned
------------------------------------

- If user is connected with multiple accounts, ask user to select an account.
  Goto URL: /itkufs/(?P<account_group_slug>\w+)/(?P<username>\w+)/

Status: All done.


Main account view
-----------------

- A menu with actions which can be performed by the user.
- If administrator and transactions are pending approval, say so.
- A paginated list with recent transactions involving the user.

Status: Done, except administrators are not informed of pending transactions.


Transfer money view
-------------------

Really a variant of the administrator's register transaction.

- Select deposit, withdrawal or transfer.
- If deposit, show fields for amount and details.
- If withdrawal, show fields for amount and details (e.g. payment details).
- If transfer, show fields for recipient, amount and details.
- In all cases, submit to the same context aware view.

Status: All done


List views
----------

1. Select the wanted list (internal, external) from 'My account' or 'My group'.
   Goto URL: /itkufs/(?P<account_group_slug>\w+)/list/internal/
   Goto URL: /itkufs/(?P<account_group_slug>\w+)/list/external/
2. Show HTML formatted list. Ask user to enable backgrounds in the print
   settings.
3. Print it and profit!.

Status: Done, except list admin must be done from django-admin. (adamcik)


Admin: Approve transaction view
-------------------------------

1. List all transactions which are not payed.
2. Select all transactions you want to mark as payed.
3. Submit and profit!

Status: Missing newforms (adamcik)


Admin: Register transaction view
--------------------------------

1. Enter from, to, amount, and payed (default true).
2. Optionally enter details and settlement.
3. Submit and profit!

(Uses transfer money view)

Status: Done, except settlement and default true (adamcik)


Admin: Register settlement (BSF)
--------------------------------

1. Create a new, or select existing, settlement with date.
2. Select a external account and payment/claim.
3. Submit.
4. If payment, register amount to transfer from each account in
   administrator's account group
5. If claim, register amount received in cash or claimed transfered to
   bank account.
6. Submit and profit!
7. Repeat for other account groups, selecting the same settlement.

Later, when the claim is received from external account, mark transaction as
payed in the approve transaction view.

Status: Barely started (adamcik)


Admin: Statements
-----------------

Show a standard accounting balance sheet with:

- Assets: bank, cash, claims, (inventory)
- Liabilities: user accounts, debts
- Equity: result

Show a standard income/expense statement.

Status: Done, except it is not possible to select a time interval for the
income statement. (jodal)


:Authors: Stein Magnus Jodal, Thomas Adamcik
:Version: 2007-11-04-1
