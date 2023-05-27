#!/usr/bin/env python3

import argparse
import time
from prometheus_client import start_http_server, Gauge, Enum
import libzfs


def recursive_children(metrics: dict, pool: str, source: str, vdev: libzfs.ZFSVdev):
    for idx, child in enumerate(vdev.children):
        stats = child.stats

        source_nested = source + '_' + child.type + '_' + str(idx)

        ops_read = stats.ops[1]  # ZIO_TYPE_READ
        ops_write = stats.ops[2]  # ZIO_TYPE_WRITE

        # bytes read/written
        bytes_read = stats.bytes[1]  # ZIO_TYPE_READ
        bytes_write = stats.bytes[2]  # ZIO_TYPE_WRITE

        errors_read = stats.read_errors
        errors_write = stats.write_errors
        errors_checksum = stats.checksum_errors

        labels = {
            'source': source_nested,
            'pool': pool,
            'type': child.type,
            'path': child.path
        }

        metrics['errors_read'].labels(**labels).set(errors_read)
        metrics['errors_write'].labels(**labels).set(errors_write)
        metrics['errors_cksum'].labels(**labels).set(errors_checksum)
        metrics['status'].labels(**labels).state(child.status)

        allocated = stats.allocated
        free = stats.size - allocated

        metrics['alloc'].labels(**labels).set(allocated)
        metrics['free'].labels(**labels).set(free)

        if child.type != 'disk':
            metrics['size'].labels(**labels).set(child.size)

        metrics['op_read'].labels(**labels).set(ops_read)
        metrics['op_write'].labels(**labels).set(ops_write)
        metrics['bw_read'].labels(**labels).set(bytes_read)
        metrics['bw_write'].labels(**labels).set(bytes_write)

        if child.type != 'disk':
            recursive_children(metrics, pool, source_nested, child)


def collect(metrics: dict):
    pools = list(libzfs.ZFS().pools)

    for pool in pools:
        labels = {
            'source': pool.name,
            'pool': pool.name,
            'type': 'pool',
            'path': None
        }

        metrics['active'].labels(**labels).state(pool.state.name)
        metrics['status'].labels(**labels).state(pool.status)

        stats = pool.root_vdev.stats

        allocated = stats.allocated
        free = stats.size - allocated

        metrics['alloc'].labels(**labels).set(allocated)
        metrics['free'].labels(**labels).set(free)

        recursive_children(metrics, pool.name, pool.name, pool.root_vdev)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-port', '--listen-port', dest='listen_port', type=int, default=9901, help="Port to listen on")
    parser.add_argument('-addr', '--listen-address', dest='listen_address', type=str, default="0.0.0.0", help="Address to listen on")
    args = parser.parse_args()
    start_http_server(args.listen_port, addr=args.listen_address)

    labels = ['source', 'pool', 'type', 'path']

    metrics = {
        'active': Enum('zfsprom_active', 'Active state', labels, states=['ACTIVE', 'EXPORTED', 'DESTROYED', 'SPARE', 'L2CACHE', 'UNINITIALIZED', 'UNAVAIL', 'POTENTIALLY_ACTIVE']),
        'size': Gauge('zfsprom_size', 'Size (bytes)', labels),
        'alloc': Gauge('zfsprom_alloc', 'Allocated space (bytes)', labels),
        'free': Gauge('zfsprom_free', 'Free space (bytes)', labels),
        'op_read': Gauge('zfsprom_op_read', 'Operations read', labels),
        'op_write': Gauge('zfsprom_op_write', 'Operations write', labels),
        'bw_read': Gauge('zfsprom_bw_read', 'Bandwidth read (bytes)', labels),
        'bw_write': Gauge('zfsprom_bw_write', 'Bandwidth write (bytes)', labels),
        'errors_read': Gauge('zfsprom_errors_read', 'Read errors', labels),
        'errors_write': Gauge('zfsprom_errors_write', 'Write errors', labels),
        'errors_cksum': Gauge('zfsprom_errors_cksum', 'Checksum errors', labels),
        'status': Enum('zfsprom_disk_status', 'Disk status', labels, states=['ONLINE', 'CLOSED', 'OFFLINE', 'REMOVED', 'CANT_OPEN', 'FAULTED', 'DEGRADED', 'HEALTHY']),
    }

    collect(metrics)
    start_time = time.time()
    while True:
        elapsed_time = time.time() - start_time
        if elapsed_time > 30.0:
            start_time = time.time()
            collect(metrics)
        time.sleep(0.1)


if __name__ == '__main__':
    main()
