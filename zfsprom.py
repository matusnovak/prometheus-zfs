#!/usr/bin/env python3

import os
import sys
import re
import subprocess
import time
from prometheus_client import start_http_server, Gauge


def run(args: [str]):
    # print('Running: {}'.format(' '.join(args)))
    out = subprocess.Popen(args, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT)
    stdout, stderr = out.communicate()

    if out.returncode != 0:
        if stderr:
            print(stderr.decode("utf-8"))
        raise Exception('Command returned code {}'.format(out.returncode))

    return stdout.decode("utf-8")


def parseCapacity(s: str):
    if s == '-':
        return None
    if s.endswith('T'):
        return float(s[:-1]) * 1000.0
    if s.endswith('G'):
        return float(s[:-1])


def parseCapacitySmall(s: str):
    if s == '-':
        return None
    if s.endswith('T'):
        return float(s[:-1]) * 1000.0 * 1000.0
    if s.endswith('G'):
        return float(s[:-1]) * 1000.0
    if s.endswith('M'):
        return float(s[:-1])
    if s.endswith('K'):
        return float(s[:-1]) / 1000.0
    if s.endswith('B'):
        return float(s[:-1]) / 1000.0 / 1000.0
    return float(s) / 1000.0 / 1000.0


def iostat(metrics):
    results = run(['zpool', 'iostat', '-v'])
    separator = False
    levels = []
    for result in results.split('\n'):
        if re.match('^[-\t\ ]+$', result):
            separator = not separator
            continue

        if separator:
            # Count spaces
            spaces = 0
            for c in result:
                if c == ' ':
                    spaces += 1
                else:
                    break
            level = int(spaces / 2)
            tokens = result.split()

            if len(levels) <= level:
                levels.append(tokens[0])
            if len(levels) > level + 1:
                levels.pop()
            levels[level] = tokens[0]
            label = '_'.join(levels)

            alloc = parseCapacity(tokens[1])
            free = parseCapacity(tokens[2])
            op_read = int(tokens[3])
            op_write = int(tokens[4])
            bw_read = parseCapacitySmall(tokens[5])
            bw_write = parseCapacitySmall(tokens[6])

            if alloc:
                metrics['alloc'].labels(label).set(alloc)
            if free:
                metrics['free'].labels(label).set(free)
            if op_read:
                metrics['op_read'].labels(label).set(op_read)
            if op_write:
                metrics['op_write'].labels(label).set(op_write)
            if bw_read:
                metrics['bw_read'].labels(label).set(bw_read)
            if bw_write:
                metrics['bw_write'].labels(label).set(bw_write)


def getspace(metrics):
    results = run(['zfs', 'get', 'space'])
    for result in results.split('\n'):
        tokens = result.split()
        if len(tokens) == 4:
            label = tokens[0]
            prop = tokens[1]

            if prop == 'available':
                available = parseCapacity(tokens[2])
                metrics['space_available'].labels(label).set(available)

            if prop == 'used':
                used = parseCapacity(tokens[2])
                metrics['space_used'].labels(label).set(used)


def collect(metrics):
    iostat(metrics)
    getspace(metrics)


def main():
    start_http_server(9901)
    metrics = {
        'alloc': Gauge('zfsprom_iostat_alloc', 'Allocated space', ['source']),
        'free': Gauge('zfsprom_iostat_free', 'Free space', ['source']),
        'op_read': Gauge('zfsprom_iostat_op_read', 'Operations read in GB', ['source']),
        'op_write': Gauge('zfsprom_iostat_op_write', 'Operations read in GB', ['source']),
        'bw_read': Gauge('zfsprom_iostat_bw_read', 'Bandwidth read in MB', ['source']),
        'bw_write': Gauge('zfsprom_iostat_bw_write', 'Bandwidth write in MB', ['source']),
        'space_available': Gauge('zfsprom_space_available', 'Space available in GB', ['source']),
        'space_used': Gauge('zfsprom_space_used', 'Space used in GB', ['source']),
    }
    # collect(metrics)

    start_time = time.time()
    while True:
        elapsed_time = time.time() - start_time
        if elapsed_time > 10.0:
            start_time = time.time()
            collect(metrics)
        time.sleep(0.1)


if __name__ == '__main__':
    main()
