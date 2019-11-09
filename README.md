# Prometheus ZFS metrics exporter

This is a simple exporter for the [Prometheus metrics](https://prometheus.io/) for [zfs](https://zfsonlinux.org/) by calling `zfs get space` and `zpool iostat`. The script `zfsprom.py` also comes with `zfsprom.service` so that you can run this script in the background on your Linux OS via `systemctl`. The script will use port `9901`, you can change it by changing it directly in the script.

This python script only exports the following metrics: `alloc`, `free`, `op_read`, `op_write`, `bw_read`, `bw_write`, `space_available`, and `space_used`. These are the same values you can extract by calling `zfs get space` and `zpool iostat` in terminal. The metrics will be exported for each pool, vdev, and drive, example:

```
zfsprom_iostat_bw_write{source="pool0"} 0.149
zfsprom_iostat_bw_write{source="pool0_raidz2"} 0.0787
zfsprom_iostat_bw_write{source="pool0_raidz2_sdm"} 0.0116
zfsprom_iostat_bw_write{source="pool0_raidz2_sdd"} 0.012
... and more ...
```

## Why?

The [node-exporter](https://github.com/prometheus/node_exporter) for Prometheus does a very good job at exporting most of the ZFS metrics, but this script exports the ones that can not be obtained via node-exporter, such as available space.

## Install

1. Copy the `zfsprom.service` file into `/etc/systemd/system` folder.
2. Copy the `zfsprom.py` file anywhere into your system.
3. Modify `ExecStart=` in the `zfsprom.service` so that it points to `zfsprom.py` in your system.
4. Run `chmod +x zfsprom.py` 
5. Install `prometheus_client` for the root user, example: `sudo -H python3 -m pip install prometheus_client`
6. Run `systemctl enable zfsprom` and `systemctl start zfsprom`
7. Your metrics will now be available at `http://localhost:9901`
