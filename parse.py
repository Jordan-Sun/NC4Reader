import re

# count the number of reassignments
reassignments = [0] * 24

# parse 'Rank {0}: {1}' from the output.txt file
fmt = re.compile(r'Rank (\d+): (\d+)')
with open('Mappings/log.txt') as f:
    for line in f:
        m = fmt.match(line)
        if m:
            reassignments[int(m.group(2)) - 1] += 1

# print the results
for i, count in enumerate(reassignments):
    print(f'{i + 1} reassignments: {count}')
