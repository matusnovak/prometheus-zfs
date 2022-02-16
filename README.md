# Prometheus ZFS metrics exporter

![build](https://github.com/matusnovak/prometheus-zfs/workflows/build/badge.svg)

This is a simple exporter for the [Prometheus metrics](https://prometheus.io/) for [zfs](https://zfsonlinux.org/) by utilizing [py-libzfs](https://github.com/truenas/py-libzfs). The script `zfsprom.py` also comes with `zfsprom.service` so that you can run this script in the background on your Linux OS via `systemctl`. The script will use port `9901`, you can change it by changing it directly in the script.

This python script only exports the following metrics:
  * active - Enum, zfsprom_active, Active state (ACTIVE, EXPORTED, DESTROYED, etc...)
  * size - Gauge, zfsprom_size, Size (bytes)
  * alloc - Gauge, zfsprom_alloc, Allocated space (bytes)
  * free - Gauge, zfsprom_free, Free space (bytes)
  * op_read - Gauge, zfsprom_op_read, Operations read
  * op_write - Gauge, zfsprom_op_write, Operations write
  * bw_read - Gauge, zfsprom_bw_read, Bandwidth read (bytes)
  * bw_write - Gauge, zfsprom_bw_write, Bandwidth write (bytes)
  * errors_read - Gauge, zfsprom_errors_read, Read errors
  * errors_write - Gauge, zfsprom_errors_write, Write errors
  * errors_cksum - Gauge, zfsprom_errors_cksum, Checksum errors
  * status - Enum, zfsprom_disk_status, Disk status', (ONLINE, OFFLINE, etc...)

Docker image here: <https://hub.docker.com/r/matusnovak/prometheus-zfs>

## Why?

The [node-exporter](https://github.com/prometheus/node_exporter) for Prometheus does a very good job at exporting most of the ZFS metrics, but this script exports the ones that can not be obtained via node-exporter, such as available space.

## Install

1. Make sure you have successfully built and installed (run make install as sudo!) the [py-libzfs](https://github.com/truenas/py-libzfs) library.
2. Copy the `zfsprom.service` file into `/etc/systemd/system` folder.
3. Copy the `zfsprom.py` file anywhere into your system.
4. Modify `ExecStart=` in the `zfsprom.service` so that it points to `zfsprom.py` in your system.
5. Run `chmod +x zfsprom.py` 
6. Install `prometheus_client` for the root user, example: `sudo -H python3 -m pip install prometheus_client`
7. Run `systemctl enable zfsprom` and `systemctl start zfsprom`
8. Your metrics will now be available at `http://localhost:9901`

## Ports

### FreeBSD

* <https://www.freshports.org/sysutils/py-prometheus-zfs> thanks to [@0mp](https://github.com/0mp)

## Docker Usage

```yml
version: '3'
services:
  zfs-metrics:
    image: matusnovak/prometheus-zfs:latest
    restart: unless-stopped
    privileged: true
    ports:
      - 9901:9901
```

Your metrics will be available at <http://localhost:9901/metrics>

