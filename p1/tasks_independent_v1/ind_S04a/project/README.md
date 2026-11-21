# ratio.py spec

simplify(a, b) must return the reduced fraction as a tuple:
- divide both sides by their greatest common divisor (gcd)
- gcd(0, 0) is undefined: return (0, 1)
- keep the sign on the numerator
