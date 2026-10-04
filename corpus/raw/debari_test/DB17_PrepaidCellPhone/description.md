The contract of a prepaid cell phone should be modelled and implemented. A basic contract has a contract number (of type int) and a balance (of type double), but no monthly charges. The contract number is not automatically generated, but is to be set as a parameter by the constructor as well as the initial balance. The balance has a getter and a setter. The following options can be added to a contract (if needed also several times):
- 100 MB of data (monthly charge 1.00€)
- 50 SMS (monthly charge 0.50€)
- 50 minutes (monthly charge 1.50€)
- Double Transfer Rate (monthly charge 2.00€) implement this requirement with the help of the decorator pattern. All contract elements should be able to understand the methods getCharges():double, getBalance():double and setBalance(double).
The method getCharges() should provide the monthly charge of a contract with all its options selected. The methods getBalance() and setBalance() should be passed through and access the basic contract.
