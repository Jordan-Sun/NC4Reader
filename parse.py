import re
import sys

# count the number of reassignments
reassignments = [0] * 24

# ensure a filename is provided
if len(sys.argv) < 2:
    # in rare cases, sys.argv[0] may not exist
    if len(sys.argv) < 1:
        sys.argv.append('parse.py')
    print('Usage: {} <log.txt>'.format(sys.argv[0]))
    sys.exit(1)

# parse 'Rank {0}: {1}' from the output.txt file
fmt = re.compile(r'Rank (\d+): (\d+)')
with open(sys.argv[1]) as f:
    for line in f:
        m = fmt.match(line)
        if m:
            reassignments[int(m.group(2)) - 1] += 1

# print the results
for i, count in enumerate(reassignments):
    print(f'{i} reassignments: {count}')
