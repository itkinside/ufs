ITK µFS Roadmap
===============

Version 1: Accounting
---------------------

:Scheduled release date: December 2007

Version 1 requirements:

- Entities of types: users, accounts, account groups, transactions, and
  settlements.
- Support transactions between two entities.
- Allow a transaction to be registered before it is payed, so it is possible to
  owe money.
- Enable a person to see transactions to and from his account.
- Enable a person to transfer money from his account to another persons
  account.
- Enable an administrator to register transactions of the following types:
  - from person to the persons account (deposit)
  - from account to the account owner (withdrawal)
  - from account to account (transfer)
  - from user account to (internal or external) bar account (payment)
  - from bar account to user account (repay expenses)
- Enable all users to print new *krysselister*, both for internal and
  external use.

For details, please refer to docs/AccountingModel.txt (and
docs/historic/AccountingViews.txt).


Version 2: Inventory
--------------------

:Scheduled release date: 2008

Version 2 ideas:

- Support inventory
  - When adding items to inventory, let administrator add purchasing price.
  - Suggest profit and selling price, but let the administrator decide himself.
  - Inventory counting with date, items, amount, and total value.
  - Let users register receipts and give the user a tracking number to put on
    the receipt.
  - Let administrators approve receipts registered by users and add receipts himself
    too.
- Other suggestions?

Please document the inventory application in docs/InventoryModel.txt and
docs/InventoryViews.txt before implementing them, and document needed changes to
the accounting application in the files mentioned under `Version 1:
Accounting`_.


Version 3: Point-of-Sale
------------------------

:Scheduled release date: 2008

Version 3 ideas:

- Point-of-Sale (a computer) on top of ITK's refrigerator.
- Can use bar codes on the inventory or at sheets (for 'smågodt' and such) for
  registering all sales.
- Can use future bar codes on our ID cards for registering payments.
- Both sales and payment can be replaced or supplemented by a touch screen
  monitor.
- For motivation, please take a look at `Pils 2000`_.


.. _Pils 2000: http://www.ping.uio.no/pils2000.shtml


..
    vim: ft=rst tw=74 ai
