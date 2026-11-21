# ratio.py spec

simplify(a, b) must return the reduced fraction as a tuple:
- divide both sides by their greatest common divisor (gcd)
- if b == 0 (any a, including 0): raise ValueError
- keep the sign on the numerator
