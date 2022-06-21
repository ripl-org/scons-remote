import sys
import os

if __name__ == '__main__':
    in_fp = sys.argv[1]
    out_fp = sys.argv[2]
    with open(in_fp) as f:
        lines = f.readlines()
        lines = [line.replace('[code]', '') for line in lines]
    with open(out_fp, 'w') as f:
        for item in lines:
            f.write(item)
    print(lines)
