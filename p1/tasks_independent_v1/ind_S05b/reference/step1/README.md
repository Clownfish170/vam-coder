# parse_line contract

parse_line(line) splits one `key,value` record:
- must raise BadFeed (defined in feed.py) when the line has fewer than 2 comma-separated fields
- must raise BadFeed when either field is empty/whitespace
- otherwise return (key, value) with surrounding spaces stripped
