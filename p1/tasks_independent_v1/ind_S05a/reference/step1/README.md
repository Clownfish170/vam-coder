# withdraw contract

withdraw(balance, amount) must:
- raise ValueError when amount <= 0
- raise InsufficientFunds (defined in balance.py) when amount > balance
- otherwise return the new balance
