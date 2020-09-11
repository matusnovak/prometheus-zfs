#!/usr/bin/env python3

import os
import sys
import re
import subprocess
import time
from prometheus_client import start_http_server, Gauge, Enum


def run(args: [str]):
    # print('Running: {}'.format(' '.join(args)))
    out = subprocess.Popen(args, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT)
    stdout, stderr = out.communicate()

    if out.returncode != 0:
        if stdout:
            print(stdout.decode("utf-8"))
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
                metrics['alloc'].labels(
                    source=label,
                    pool=levels[0]
                ).set(alloc)
            if free:
                metrics['free'].labels(
                    source=label,
                    pool=levels[0]
                ).set(free)
            if op_read:
                metrics['op_read'].labels(
                    source=label,
                    pool=levels[0]
                ).set(op_read)
            if op_write:
                metrics['op_write'].labels(
                    source=label,
                    pool=levels[0]
                ).set(op_write)
            if bw_read:
                metrics['bw_read'].labels(
                    source=label,
                    pool=levels[0]
                ).set(bw_read)
            if bw_write:
                metrics['bw_write'].labels(
                    source=label,
                    pool=levels[0]
                ).set(bw_write)


def getspace(metrics):
    results = run(['zfs', 'get', 'space'])
    for result in results.split('\n'):
        tokens = result.split()
        if len(tokens) == 4:
            label = tokens[0]
            prop = tokens[1]

            if prop == 'available':
                available = parseCapacity(tokens[2])
                metrics['space_available'].labels(
                    source=label
                ).set(available)

            if prop == 'used':
                used = parseCapacity(tokens[2])
                metrics['space_used'].labels(
                    source=label
                ).set(used)


def status(metrics):
    results = run(['zpool', 'status', '-c', 'serial,upath'])
    header = False
    for result in results.split('\n'):
        if result.strip().startswith('NAME'):
            header = True
            continue

        if header:
            tokens = result.split()
            if len(tokens) >= 7:
                metrics['status_state'].labels(
                    source=tokens[0],
                    serial=tokens[5],
                    upath=tokens[6]
                ).state(tokens[1])
                metrics['status_read'].labels(
                    source=tokens[0],
                    serial=tokens[5],
                    upath=tokens[6]
                ).set(int(tokens[2]))
                metrics['status_write'].labels(
                    source=tokens[0],
                    serial=tokens[5],
                    upath=tokens[6]
                ).set(int(tokens[3]))
                metrics['status_cksum'].labels(
                    source=tokens[0],
                    serial=tokens[5],
                    upath=tokens[6]
                ).set(int(tokens[4]))


def status2(metrics):
    results = run(['zpool', 'status', '-c', 'serial,upath'])
    header = False
    header_offset = 0
    levels = []
    for result in results.split('\n'):
        if result.strip().startswith('NAME'):
            header = True
            for c in result:
                if c == ' ':
                    header_offset += 1
                else:
                    break
            continue

        elif header:
            tokens = result.split()
            
            if len(tokens) != 5 and len(tokens) != 7:
                continue

            # Count spaces
            spaces = 0
            for c in result:
                if c == '\t':
                    continue
                elif c == ' ':
                    spaces += 1
                else:
                    break

            spaces -= header_offset
            level = int(spaces / 2)

            if len(levels) <= level:
                levels.append(tokens[0])
            if len(levels) > level + 1:
                levels.pop()
            levels[level] = tokens[0]
            label = '_'.join(levels)

            if len(tokens) >= 7:
                metrics['status_state'].labels(
                    pool=levels[0],
                    source=tokens[0],
                    serial=tokens[5],
                    upath=tokens[6]
                ).state(tokens[1])
                metrics['status_read'].labels(
                    pool=levels[0],
                    source=tokens[0],
                    serial=tokens[5],
                    upath=tokens[6]
                ).set(int(tokens[2]))
                metrics['status_write'].labels(
                    pool=levels[0],
                    source=tokens[0],
                    serial=tokens[5],
                    upath=tokens[6]
                ).set(int(tokens[3]))
                metrics['status_cksum'].labels(
                    pool=levels[0],
                    source=tokens[0],
                    serial=tokens[5],
                    upath=tokens[6]
                ).set(int(tokens[4]))
            



def collect(metrics):
    iostat(metrics)
    getspace(metrics)
    status2(metrics)


def main():
    start_http_server(9901)
    metrics = {
        'alloc': Gauge('zfsprom_iostat_alloc', 'Allocated space', ['source', 'pool']),
        'free': Gauge('zfsprom_iostat_free', 'Free space', ['source', 'pool']),
        'op_read': Gauge('zfsprom_iostat_op_read', 'Operations read in GB', ['source', 'pool']),
        'op_write': Gauge('zfsprom_iostat_op_write', 'Operations read in GB', ['source', 'pool']),
        'bw_read': Gauge('zfsprom_iostat_bw_read', 'Bandwidth read in MB', ['source', 'pool']),
        'bw_write': Gauge('zfsprom_iostat_bw_write', 'Bandwidth write in MB', ['source', 'pool']),
        'space_available': Gauge('zfsprom_space_available', 'Space available in GB', ['source']),
        'space_used': Gauge('zfsprom_space_used', 'Space used in GB', ['source']),
        'status_state': Enum('zfsprom_status_state', 'Disk status', ['source', 'serial', 'upath', 'pool'], states=['ONLINE', 'DEGRADED', 'FAULTED', 'OFFLINE', 'UNAVAIL', 'REMOVED']),
        'status_read': Gauge('zfsprom_status_read', 'Read errors', ['source', 'serial', 'upath', 'pool']),
        'status_write': Gauge('zfsprom_status_write', 'Write errors', ['source', 'serial', 'upath', 'pool']),
        'status_cksum': Gauge('zfsprom_status_cksum', 'Checksum errors', ['source', 'serial', 'upath', 'pool']),
    }

    start_time = time.time()
    while True:
        elapsed_time = time.time() - start_time
        if elapsed_time > 30.0:
            start_time = time.time()
            collect(metrics)
        time.sleep(0.1)

if __name__ == '__main__':
    main()
