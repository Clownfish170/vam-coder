# round1 spec

round1(x) rounds to 1 decimal place using HALF-UP on the decimal digit (not banker's rounding):
- 2.25 -> 2.3
- 2.35 -> 2.4
- -2.25 -> -2.3 (magnitude grows away from zero on .5)

round2(x) rounds to 2 decimal places with the same HALF-UP rule:
- 2.225 -> 2.23
- 1.5 -> 1.5
