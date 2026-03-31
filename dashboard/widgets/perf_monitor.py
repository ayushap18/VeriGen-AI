"""CPU and memory usage monitor — expanded with detailed metrics."""

import os
import psutil
from textual.widgets import Static


class PerfMonitor(Static):
    DEFAULT_CSS = """
    PerfMonitor {
        height: auto;
        min-height: 12;
        border: solid #1a3a1a;
        background: #050a05;
        padding: 0 1;
    }
    """

    def __init__(self):
        super().__init__("[#00ff88 bold]\u25c9 PERFORMANCE MONITOR[/#00ff88 bold]")
        self._history_cpu: list[float] = []
        self._history_mem: list[float] = []
        self._history_net_sent: list[float] = []
        self._proc = psutil.Process(os.getpid())
        self._prev_net = psutil.net_io_counters()
        self._peak_cpu = 0.0
        self._peak_mem = 0.0

    def tick(self):
        try:
            cpu = psutil.cpu_percent(interval=0)
            mem = psutil.virtual_memory()
            net = psutil.net_io_counters()

            self._peak_cpu = max(self._peak_cpu, cpu)
            self._peak_mem = max(self._peak_mem, mem.percent)

            self._history_cpu.append(cpu)
            self._history_mem.append(mem.percent)
            if len(self._history_cpu) > 40:
                self._history_cpu = self._history_cpu[-40:]
                self._history_mem = self._history_mem[-40:]

            blocks = " \u2581\u2582\u2583\u2584\u2585\u2586\u2587\u2588"

            # CPU section
            cpu_color = "#00ff88" if cpu < 60 else "#ffaa00" if cpu < 85 else "#ff4444"
            cpu_bar_len = int(cpu / 100 * 24)
            cpu_bar = f"[{cpu_color}]\u2588[/{cpu_color}]" * cpu_bar_len + "[#0a2a0a]\u2591[/#0a2a0a]" * (24 - cpu_bar_len)

            # Memory section
            mem_color = "#00ff88" if mem.percent < 60 else "#ffaa00" if mem.percent < 85 else "#ff4444"
            mem_bar_len = int(mem.percent / 100 * 24)
            mem_bar = f"[{mem_color}]\u2588[/{mem_color}]" * mem_bar_len + "[#0a2a0a]\u2591[/#0a2a0a]" * (24 - mem_bar_len)

            # Sparklines
            cpu_spark = "".join(
                f"[{cpu_color}]{blocks[min(int(v / 100 * 8), 8)]}[/{cpu_color}]"
                for v in self._history_cpu[-30:]
            )
            mem_spark = "".join(
                f"[{mem_color}]{blocks[min(int(v / 100 * 8), 8)]}[/{mem_color}]"
                for v in self._history_mem[-30:]
            )

            # System stats
            mem_used_gb = mem.used / (1024 ** 3)
            mem_total_gb = mem.total / (1024 ** 3)
            mem_avail_gb = mem.available / (1024 ** 3)
            proc_mem = self._proc.memory_info().rss / (1024 ** 2)
            num_threads = self._proc.num_threads()
            cpu_count = psutil.cpu_count()

            # CPU load averages
            load1, load5, load15 = os.getloadavg()

            # Network I/O
            net_sent_mb = net.bytes_sent / (1024 ** 2)
            net_recv_mb = net.bytes_recv / (1024 ** 2)

            # Disk I/O
            try:
                disk = psutil.disk_usage('/')
                disk_pct = disk.percent
                disk_color = "#00ff88" if disk_pct < 70 else "#ffaa00" if disk_pct < 90 else "#ff4444"
            except Exception:
                disk_pct = 0
                disk_color = "#3a6a3a"

            # Avg CPU
            avg_cpu = sum(self._history_cpu) / len(self._history_cpu) if self._history_cpu else 0

            text = (
                f"[#00ff88 bold]\u25c9 PERFORMANCE MONITOR[/#00ff88 bold]\n"
                f"[#1a3a1a]{'─' * 36}[/#1a3a1a]\n"
                f"  [#3a6a3a]CPU  [/#3a6a3a] [{cpu_color}]{cpu:5.1f}%[/{cpu_color}] {cpu_bar}\n"
                f"  [#3a6a3a]     [/#3a6a3a] {cpu_spark}\n"
                f"  [#3a6a3a]MEM  [/#3a6a3a] [{mem_color}]{mem.percent:5.1f}%[/{mem_color}] {mem_bar}\n"
                f"  [#3a6a3a]     [/#3a6a3a] {mem_spark}\n"
                f"[#1a3a1a]{'─' * 36}[/#1a3a1a]\n"
                f"  [#3a6a3a]CORES:[/#3a6a3a] [#ccddcc]{cpu_count}[/#ccddcc]"
                f"  [#3a6a3a]LOAD:[/#3a6a3a] [#ccddcc]{load1:.1f} {load5:.1f} {load15:.1f}[/#ccddcc]\n"
                f"  [#3a6a3a]PEAK: [/#3a6a3a] [#ffaa00]CPU {self._peak_cpu:.1f}%[/#ffaa00]"
                f"  [#ffaa00]MEM {self._peak_mem:.1f}%[/#ffaa00]\n"
                f"  [#3a6a3a]SYS: [/#3a6a3a] [#ccddcc]{mem_used_gb:.1f}/{mem_total_gb:.1f} GB[/#ccddcc]"
                f"  [#3a6a3a]FREE:[/#3a6a3a] [#ccddcc]{mem_avail_gb:.1f} GB[/#ccddcc]\n"
                f"  [#3a6a3a]APP: [/#3a6a3a] [#00d4ff]{proc_mem:.0f} MB[/#00d4ff]"
                f"  [#3a6a3a]THR:[/#3a6a3a] [#ccddcc]{num_threads}[/#ccddcc]"
                f"  [#3a6a3a]DSK:[/#3a6a3a] [{disk_color}]{disk_pct:.0f}%[/{disk_color}]\n"
                f"  [#3a6a3a]NET\u2191:[/#3a6a3a] [#ccddcc]{net_sent_mb:.1f}MB[/#ccddcc]"
                f"  [#3a6a3a]NET\u2193:[/#3a6a3a] [#ccddcc]{net_recv_mb:.1f}MB[/#ccddcc]"
            )
            self.update(text)
        except Exception:
            pass
