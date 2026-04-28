#!/usr/bin/env python3
"""
dockertui - A TUI sysadmin dashboard for Docker/Podman and system monitoring
Requirements: pip install rich psutil
             Or run: ./install.sh
"""

import subprocess
import shutil
import os
import sys
import time
import json
from datetime import datetime

try:
    import psutil
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.columns import Columns
    from rich.text import Text
    from rich.prompt import Prompt, Confirm
    from rich.progress import Progress, BarColumn, TextColumn
    from rich.layout import Layout
    from rich.live import Live
    from rich import box
    from rich.align import Align
    from rich.rule import Rule
    from rich.style import Style
except ImportError:
    print("Missing dependencies!")
    print("\nOption 1: Run the install script:")
    print("  ./install.sh")
    print("\nOption 2: Install manually:")
    print("  pip install rich psutil")
    print("\nOption 3: Use requirements.txt:")
    print("  pip install -r requirements.txt\n")
    sys.exit(1)

console = Console()

ACCENT = "cyan"
DANGER = "red"
WARN = "yellow"
SUCCESS = "green"
DIM = "dim"
TITLE_STYLE = f"bold {ACCENT}"

BANNER = r"""
 ____             _             _____ _   _ ___ 
|  _ \  ___   ___| | _____ _ __|_   _| | | |_ _|
| | | |/ _ \ / __| |/ / _ \ '__| | | | | | || | 
| |_| | (_) | (__|   <  __/ |    | | | |_| || | 
|____/ \___/ \___|_|\_\___|_|    |_|  \___/|___|
"""

# ─── RUNTIME AUTO-DETECTION ───────────────────────────────────────────────────

def detect_runtime():
    """
    Auto-detect container runtime. Returns (binary, label, color).
    Prefers Docker if both are present. Falls back to Podman.
    Returns (None, None, None) if neither found.
    """
    has_docker = shutil.which("docker") is not None
    has_podman = shutil.which("podman") is not None

    if has_docker:
        # Verify Docker daemon is actually running
        result = subprocess.run(
            "docker info", shell=True,
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return "docker", "Docker", "blue"

    if has_podman:
        result = subprocess.run(
            "podman info", shell=True,
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return "podman", "Podman", "magenta"

    # Neither daemon is responsive
    if has_docker:
        return "docker", "Docker (daemon offline)", "red"
    if has_podman:
        return "podman", "Podman (daemon offline)", "red"

    return None, None, None

# Detect at startup
RUNTIME, RUNTIME_LABEL, RUNTIME_COLOR = detect_runtime()

def rt(subcmd):
    """Build a runtime command string."""
    if not RUNTIME:
        return ""
    return f"{RUNTIME} {subcmd}"

def run(cmd, capture=True):
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=capture,
            text=True, timeout=15
        )
        return result.stdout.strip() if capture else result.returncode
    except Exception:
        return ""

def check_runtime():
    return RUNTIME is not None

def clear():
    console.clear()

def print_banner():
    console.print(f"[bold {ACCENT}]{BANNER}[/]", justify="center")
    # Show which runtime is active
    if RUNTIME:
        rt_badge = f"[bold {RUNTIME_COLOR}] {RUNTIME_LABEL} [/]"
    else:
        rt_badge = f"[bold {DANGER}] No Runtime Detected [/]"
    console.print(
        f"[{DIM}]  System Admin Dashboard  •  {datetime.now().strftime('%A, %d %B %Y  %H:%M:%S')}[/]  {rt_badge}\n",
        justify="center"
    )

def bytes_to_human(n):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"

# ─── SYSTEM OVERVIEW ──────────────────────────────────────────────────────────

def show_system_overview():
    clear()
    print_banner()
    console.print(Rule(f"[{TITLE_STYLE}]  System Overview"))
    console.print()

    # CPU
    cpu_pct = psutil.cpu_percent(interval=0.5)
    cpu_count = psutil.cpu_count()
    cpu_bar = int(cpu_pct / 5)
    cpu_color = DANGER if cpu_pct > 80 else WARN if cpu_pct > 50 else SUCCESS
    cpu_bar_str = f"[{cpu_color}]{'█' * cpu_bar}[/][dim]{'░' * (20 - cpu_bar)}[/]"

    # RAM
    mem = psutil.virtual_memory()
    ram_pct = mem.percent
    ram_bar = int(ram_pct / 5)
    ram_color = DANGER if ram_pct > 85 else WARN if ram_pct > 60 else SUCCESS
    ram_bar_str = f"[{ram_color}]{'█' * ram_bar}[/][dim]{'░' * (20 - ram_bar)}[/]"

    # Swap
    swap = psutil.swap_memory()
    swap_pct = swap.percent
    swap_bar = int(swap_pct / 5)
    swap_color = DANGER if swap_pct > 50 else WARN if swap_pct > 20 else SUCCESS
    swap_bar_str = f"[{swap_color}]{'█' * swap_bar}[/][dim]{'░' * (20 - swap_bar)}[/]"

    # Disk
    disk = psutil.disk_usage('/')
    disk_pct = disk.percent
    disk_bar = int(disk_pct / 5)
    disk_color = DANGER if disk_pct > 85 else WARN if disk_pct > 70 else SUCCESS
    disk_bar_str = f"[{disk_color}]{'█' * disk_bar}[/][dim]{'░' * (20 - disk_bar)}[/]"

    # Network
    net = psutil.net_io_counters()

    table = Table(box=box.ROUNDED, border_style=ACCENT, expand=True, show_header=False)
    table.add_column("Metric", style="bold", width=20)
    table.add_column("Bar", width=25)
    table.add_column("Value", justify="right")

    table.add_row(
        "CPU Usage",
        cpu_bar_str,
        f"[{cpu_color}]{cpu_pct:.1f}%[/]  [{DIM}]{cpu_count} cores[/]"
    )
    table.add_row(
        "RAM Usage",
        ram_bar_str,
        f"[{ram_color}]{bytes_to_human(mem.used)}[/] / [{DIM}]{bytes_to_human(mem.total)}[/]  [{SUCCESS}]{bytes_to_human(mem.available)} free[/]"
    )
    table.add_row(
        "Swap",
        swap_bar_str,
        f"[{swap_color}]{bytes_to_human(swap.used)}[/] / [{DIM}]{bytes_to_human(swap.total)}[/]"
    )
    table.add_row(
        "Disk (/)",
        disk_bar_str,
        f"[{disk_color}]{bytes_to_human(disk.used)}[/] / [{DIM}]{bytes_to_human(disk.total)}[/]  [{SUCCESS}]{bytes_to_human(disk.free)} free[/]"
    )
    table.add_row(
        "Network I/O",
        "",
        f"[{SUCCESS}]↑ {bytes_to_human(net.bytes_sent)}[/]  [{ACCENT}]↓ {bytes_to_human(net.bytes_recv)}[/]"
    )

    console.print(table)

    # Uptime
    boot_time = psutil.boot_time()
    uptime_seconds = time.time() - boot_time
    days = int(uptime_seconds // 86400)
    hours = int((uptime_seconds % 86400) // 3600)
    mins = int((uptime_seconds % 3600) // 60)
    console.print(f"\n[{DIM}]  Uptime:[/] [{SUCCESS}]{days}d {hours}h {mins}m[/]   [{DIM}]Load avg:[/] [{ACCENT}]{' '.join([str(round(x,2)) for x in os.getloadavg()])}[/]\n")

    input_pause()

# ─── TOP PROCESSES ────────────────────────────────────────────────────────────

def show_top_processes():
    clear()
    print_banner()
    console.print(Rule(f"[{TITLE_STYLE}]  Top Processes by RAM"))
    console.print()

    procs = []
    for p in psutil.process_iter(['pid', 'name', 'username', 'memory_info', 'cpu_percent', 'status']):
        try:
            procs.append(p.info)
        except Exception:
            pass

    procs.sort(key=lambda x: x['memory_info'].rss if x['memory_info'] else 0, reverse=True)

    table = Table(box=box.ROUNDED, border_style=ACCENT, expand=True)
    table.add_column("PID", style="dim", width=8)
    table.add_column("Name", style="bold")
    table.add_column("User", style=DIM)
    table.add_column("RAM", justify="right", style=WARN)
    table.add_column("CPU%", justify="right", style=ACCENT)
    table.add_column("Status", justify="center")

    for p in procs[:25]:
        mem = p['memory_info']
        ram = bytes_to_human(mem.rss) if mem else "N/A"
        status = p['status'] or "?"
        status_color = SUCCESS if status == "running" else DIM
        table.add_row(
            str(p['pid']),
            p['name'] or "?",
            p['username'] or "?",
            ram,
            f"{p['cpu_percent']:.1f}",
            f"[{status_color}]{status}[/]"
        )

    console.print(table)
    input_pause()

# ─── DOCKER STATUS ────────────────────────────────────────────────────────────

def show_docker_status():
    clear()
    print_banner()
    console.print(Rule(f"[{TITLE_STYLE}]  Docker Container Status"))
    console.print()

    raw = run("docker ps -a --format '{{json .}}'")
    if not raw:
        console.print(f"[{DANGER}]No Docker output — is Docker running?[/]")
        input_pause()
        return

    containers = []
    for line in raw.splitlines():
        try:
            containers.append(json.loads(line))
        except Exception:
            pass

    table = Table(box=box.ROUNDED, border_style=ACCENT, expand=True)
    table.add_column("Name", style="bold")
    table.add_column("Image", style=DIM)
    table.add_column("Status", justify="center")
    table.add_column("Ports", style=DIM, overflow="fold")
    table.add_column("Created", style=DIM)

    for c in containers:
        status = c.get("Status", "")
        name = c.get("Names", "?")
        image = c.get("Image", "?")
        ports = c.get("Ports", "") or ""
        created = c.get("RunningFor", c.get("Created", "?"))

        if "Up" in status:
            status_text = f"[{SUCCESS}]● {status}[/]"
        elif "Exited" in status:
            status_text = f"[{DANGER}]● {status}[/]"
        else:
            status_text = f"[{WARN}]● {status}[/]"

        # Clean up ports
        port_list = []
        for p in ports.split(","):
            p = p.strip()
            if "->" in p:
                parts = p.split("->")
                host = parts[0].split(":")[-1] if ":" in parts[0] else parts[0]
                container = parts[1]
                port_list.append(f"{host}→{container}")
        ports_display = ", ".join(port_list[:3]) if port_list else "—"

        table.add_row(name, image, status_text, ports_display, created)

    console.print(table)

    # Summary
    total = len(containers)
    running = sum(1 for c in containers if "Up" in c.get("Status", ""))
    stopped = total - running
    console.print(f"\n[{DIM}]Total:[/] [{ACCENT}]{total}[/]   [{SUCCESS}]Running: {running}[/]   [{DANGER}]Stopped: {stopped}[/]\n")
    input_pause()

# ─── DOCKER STATS ─────────────────────────────────────────────────────────────

def show_docker_stats():
    clear()
    print_banner()
    console.print(Rule(f"[{TITLE_STYLE}]  Docker Resource Usage"))
    console.print()
    console.print(f"[{DIM}]Fetching stats (may take a moment)...[/]\n")

    raw = run("docker stats --no-stream --format '{{json .}}'")
    if not raw:
        console.print(f"[{DANGER}]No stats available.[/]")
        input_pause()
        return

    stats = []
    for line in raw.splitlines():
        try:
            stats.append(json.loads(line))
        except Exception:
            pass

    stats.sort(key=lambda x: x.get("MemPerc", "0%").replace("%", ""), reverse=True)

    table = Table(box=box.ROUNDED, border_style=ACCENT, expand=True)
    table.add_column("Container", style="bold")
    table.add_column("CPU%", justify="right", style=ACCENT)
    table.add_column("RAM Used", justify="right", style=WARN)
    table.add_column("RAM%", justify="right")
    table.add_column("RAM Limit", justify="right", style=DIM)
    table.add_column("Net I/O", justify="right", style=DIM)
    table.add_column("Block I/O", justify="right", style=DIM)

    total_mem_pct = 0.0
    for s in stats:
        name = s.get("Name", "?")
        cpu = s.get("CPUPerc", "0%")
        mem_usage = s.get("MemUsage", "? / ?")
        mem_perc = s.get("MemPerc", "0%")
        net_io = s.get("NetIO", "?")
        block_io = s.get("BlockIO", "?")

        try:
            mem_pct_val = float(mem_perc.replace("%", ""))
            total_mem_pct += mem_pct_val
        except Exception:
            mem_pct_val = 0

        mem_color = DANGER if mem_pct_val > 80 else WARN if mem_pct_val > 50 else SUCCESS
        cpu_val = float(cpu.replace("%", "")) if "%" in cpu else 0
        cpu_color = DANGER if cpu_val > 80 else WARN if cpu_val > 40 else SUCCESS

        parts = mem_usage.split("/")
        used = parts[0].strip() if len(parts) > 0 else "?"
        limit = parts[1].strip() if len(parts) > 1 else "?"

        table.add_row(
            name,
            f"[{cpu_color}]{cpu}[/]",
            f"[{mem_color}]{used}[/]",
            f"[{mem_color}]{mem_perc}[/]",
            limit,
            net_io,
            block_io
        )

    console.print(table)
    console.print(f"\n[{DIM}]Total RAM consumed by Docker:[/] [{WARN}]{total_mem_pct:.1f}% of host[/]\n")
    input_pause()

# ─── DOCKER PRUNE ─────────────────────────────────────────────────────────────

def docker_prune():
    clear()
    print_banner()
    console.print(Rule(f"[{TITLE_STYLE}]  Docker Cleanup"))
    console.print()

    options = {
        "1": ("Stopped containers only", "docker container prune -f"),
        "2": ("Unused images only", "docker image prune -af"),
        "3": ("Unused volumes only", "docker volume prune -f"),
        "4": ("Unused networks only", "docker network prune -f"),
        "5": ("Everything (containers, images, networks)", "docker system prune -af"),
        "6": ("EVERYTHING including volumes ⚠️", "docker system prune -af --volumes"),
    }

    for k, (label, _) in options.items():
        color = DANGER if k == "6" else WARN if k == "5" else ACCENT
        console.print(f"  [{color}][{k}][/] {label}")

    console.print(f"  [{DIM}][0][/] Back\n")
    choice = Prompt.ask("Select", choices=["0","1","2","3","4","5","6"])

    if choice == "0":
        return

    label, cmd = options[choice]
    if choice in ("5", "6"):
        confirm = Confirm.ask(f"[{DANGER}]This will delete {label.lower()}. Are you sure?[/]")
        if not confirm:
            console.print(f"[{DIM}]Cancelled.[/]")
            time.sleep(1)
            return

    console.print(f"\n[{WARN}]Running:[/] [{DIM}]{cmd}[/]\n")
    result = subprocess.run(cmd, shell=True, capture_output=False, text=True)
    console.print(f"\n[{SUCCESS}]Done![/]")
    input_pause()

# ─── DOCKER CONTROL ───────────────────────────────────────────────────────────

def docker_control():
    clear()
    print_banner()
    console.print(Rule(f"[{TITLE_STYLE}]  Docker Container Control"))
    console.print()

    raw = run("docker ps -a --format '{{.Names}}\t{{.Status}}'")
    if not raw:
        console.print(f"[{DANGER}]No containers found.[/]")
        input_pause()
        return

    containers = []
    for line in raw.splitlines():
        parts = line.split("\t")
        if len(parts) == 2:
            containers.append({"name": parts[0], "status": parts[1]})

    table = Table(box=box.SIMPLE, border_style=DIM)
    table.add_column("#", style=DIM, width=4)
    table.add_column("Container", style="bold")
    table.add_column("Status")

    for i, c in enumerate(containers, 1):
        status = c["status"]
        color = SUCCESS if "Up" in status else DANGER
        table.add_row(str(i), c["name"], f"[{color}]{status}[/]")

    console.print(table)
    console.print(f"\n[{DIM}]Enter container number (or 0 to go back):[/]")
    
    choices = ["0"] + [str(i) for i in range(1, len(containers)+1)]
    choice = Prompt.ask("Container #", choices=choices)
    if choice == "0":
        return

    container = containers[int(choice)-1]["name"]
    is_running = "Up" in containers[int(choice)-1]["status"]

    console.print(f"\nContainer: [{ACCENT}]{container}[/]\n")
    if is_running:
        console.print(f"  [{SUCCESS}][1][/] Stop")
        console.print(f"  [{WARN}][2][/] Restart")
        console.print(f"  [{ACCENT}][3][/] View logs (last 50 lines)")
        console.print(f"  [{DIM}][0][/] Back\n")
        action = Prompt.ask("Action", choices=["0","1","2","3"])
        cmds = {"1": f"docker stop {container}", "2": f"docker restart {container}", "3": f"docker logs --tail 50 {container}"}
    else:
        console.print(f"  [{SUCCESS}][1][/] Start")
        console.print(f"  [{DANGER}][2][/] Remove container")
        console.print(f"  [{ACCENT}][3][/] View logs (last 50 lines)")
        console.print(f"  [{DIM}][0][/] Back\n")
        action = Prompt.ask("Action", choices=["0","1","2","3"])
        cmds = {"1": f"docker start {container}", "2": f"docker rm {container}", "3": f"docker logs --tail 50 {container}"}

    if action == "0":
        return

    cmd = cmds.get(action)
    if cmd:
        console.print(f"\n[{WARN}]Running:[/] [{DIM}]{cmd}[/]\n")
        subprocess.run(cmd, shell=True)
        console.print(f"\n[{SUCCESS}]Done![/]")
        input_pause()

# ─── DISK USAGE ───────────────────────────────────────────────────────────────

def show_disk_usage():
    clear()
    print_banner()
    console.print(Rule(f"[{TITLE_STYLE}]  Disk Usage"))
    console.print()

    partitions = psutil.disk_partitions()
    table = Table(box=box.ROUNDED, border_style=ACCENT, expand=True)
    table.add_column("Mount", style="bold")
    table.add_column("Device", style=DIM)
    table.add_column("FS Type", style=DIM)
    table.add_column("Total", justify="right")
    table.add_column("Used", justify="right", style=WARN)
    table.add_column("Free", justify="right", style=SUCCESS)
    table.add_column("Usage%", justify="right")

    for p in partitions:
        try:
            usage = psutil.disk_usage(p.mountpoint)
            pct = usage.percent
            color = DANGER if pct > 85 else WARN if pct > 70 else SUCCESS
            bar = f"[{color}]{pct:.1f}%[/]"
            table.add_row(
                p.mountpoint, p.device, p.fstype,
                bytes_to_human(usage.total),
                bytes_to_human(usage.used),
                bytes_to_human(usage.free),
                bar
            )
        except Exception:
            pass

    console.print(table)
    input_pause()

# ─── SYSTEMD SERVICES ─────────────────────────────────────────────────────────

def show_services():
    clear()
    print_banner()
    console.print(Rule(f"[{TITLE_STYLE}]  Systemd Services"))
    console.print()

    raw = run("systemctl list-units --type=service --state=running --no-pager --no-legend")
    if not raw:
        console.print(f"[{DANGER}]Could not fetch services.[/]")
        input_pause()
        return

    table = Table(box=box.ROUNDED, border_style=ACCENT, expand=True)
    table.add_column("Service", style="bold")
    table.add_column("Load", justify="center")
    table.add_column("Active", justify="center")
    table.add_column("Sub", justify="center")
    table.add_column("Description", style=DIM)

    for line in raw.splitlines()[:30]:
        parts = line.split(None, 4)
        if len(parts) >= 4:
            name = parts[0].replace(".service","")
            load = parts[1]
            active = parts[2]
            sub = parts[3]
            desc = parts[4] if len(parts) > 4 else ""
            sub_color = SUCCESS if sub == "running" else WARN
            table.add_row(name, load, active, f"[{sub_color}]{sub}[/]", desc)

    console.print(table)
    input_pause()

# ─── LIVE MONITOR ─────────────────────────────────────────────────────────────

def live_monitor():
    """Live monitoring with process details, Docker containers, and 'q' to quit."""
    import tty
    import termios
    import select
    
    def get_key():
        """Get a single keystroke without waiting for Enter."""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch
    
    console.print(f"[{DIM}]Live monitor — press 'q' to go back to main menu[/]\n")
    
    try:
        while True:
            # Check for 'q' key press (non-blocking)
            if select.select([sys.stdin], [], [], 0)[0]:
                ch = sys.stdin.read(1)
                if ch and ch.lower() == 'q':
                    break
            
            # Clear screen for fresh update
            clear()
            console.print(f"[{DIM}]Live monitor — press 'q' to go back to main menu[/]\n")
            
            # Gather system stats
            mem = psutil.virtual_memory()
            cpu = psutil.cpu_percent(interval=0.3)
            swap = psutil.swap_memory()
            
            # Get top 8 processes by RAM
            top_procs = []
            for p in psutil.process_iter(['pid', 'name', 'username', 'memory_info', 'cpu_percent', 'status']):
                try:
                    info = p.info
                    if info['memory_info']:
                        top_procs.append(info)
                except Exception:
                    pass
            top_procs.sort(key=lambda x: x['memory_info'].rss if x['memory_info'] else 0, reverse=True)
            top_procs = top_procs[:8]
            
            # Get Docker container stats if available
            docker_stats = []
            if RUNTIME == "docker":
                raw = run("docker stats --no-stream --format '{{json .}}'", capture=True)
                if raw:
                    for line in raw.splitlines():
                        try:
                            s = json.loads(line)
                            docker_stats.append(s)
                        except Exception:
                            pass
            
            # Build the display
            cpu_color = DANGER if cpu > 80 else WARN if cpu > 50 else SUCCESS
            ram_color = DANGER if mem.percent > 85 else WARN if mem.percent > 60 else SUCCESS
            
            # System overview panel
            sys_table = Table(box=box.ROUNDED, border_style=ACCENT, expand=True, show_header=False)
            sys_table.add_column("Metric", style="bold", width=18)
            sys_table.add_column("Value")
            
            sys_table.add_row("CPU", f"[{cpu_color}]{cpu:.1f}%[/]")
            sys_table.add_row("RAM Used", f"[{ram_color}]{bytes_to_human(mem.used)} / {bytes_to_human(mem.total)} ({mem.percent:.1f}%)[/]")
            sys_table.add_row("RAM Free", f"[{SUCCESS}]{bytes_to_human(mem.available)}[/]")
            sys_table.add_row("Swap", f"[{WARN}]{bytes_to_human(swap.used)} / {bytes_to_human(swap.total)}[/]")
            sys_table.add_row("Updated", f"[{DIM}]{datetime.now().strftime('%H:%M:%S')}[/]")
            
            # Process table
            proc_table = Table(box=box.ROUNDED, border_style=SUCCESS, expand=True, title=f"[{TITLE_STYLE}] Top Processes (by RAM)", title_style=f"bold {SUCCESS}")
            proc_table.add_column("PID", style="dim", width=6)
            proc_table.add_column("Name", style="bold", width=20)
            proc_table.add_column("User", style=DIM, width=12)
            proc_table.add_column("RAM", justify="right", style=WARN, width=10)
            proc_table.add_column("CPU%", justify="right", style=ACCENT, width=7)
            proc_table.add_column("Status", justify="center", width=10)
            
            for p in top_procs:
                mem_info = p['memory_info']
                ram = bytes_to_human(mem_info.rss) if mem_info else "N/A"
                status = p['status'] or "?"
                status_color = SUCCESS if status == "running" else DIM
                proc_table.add_row(
                    str(p['pid']),
                    (p['name'] or "?")[:20],
                    (p['username'] or "?")[:12],
                    ram,
                    f"{p['cpu_percent']:.1f}",
                    f"[{status_color}]{status}[/]"
                )
            
            # Docker containers panel
            docker_title = f"[{TITLE_STYLE}] Docker Containers (Live)" if docker_stats else f"[{TITLE_STYLE}] Docker Containers (none running)"
            docker_table = Table(box=box.ROUNDED, border_style="blue", expand=True, title=docker_title, title_style=f"bold blue")
            docker_table.add_column("Container", style="bold", width=20)
            docker_table.add_column("CPU%", justify="right", style=ACCENT, width=7)
            docker_table.add_column("RAM", justify="right", style=WARN, width=10)
            docker_table.add_column("RAM%", justify="right", width=7)
            docker_table.add_column("Net I/O", style=DIM, width=15)
            
            if docker_stats:
                for s in docker_stats:
                    name = s.get("Name", "?")[:20]
                    cpu_pct = s.get("CPUPerc", "0%")
                    mem_usage = s.get("MemUsage", "? / ?")
                    mem_perc = s.get("MemPerc", "0%")
                    net_io = s.get("NetIO", "?")
                    
                    # Parse mem_usage to get just the used amount
                    mem_used = mem_usage.split("/")[0].strip() if "/" in mem_usage else mem_usage
                    
                    cpu_val = float(cpu_pct.replace("%", "")) if "%" in cpu_pct else 0
                    cpu_c = DANGER if cpu_val > 80 else WARN if cpu_val > 40 else ACCENT
                    mem_pct_val = float(mem_perc.replace("%", "")) if "%" in mem_perc else 0
                    mem_c = DANGER if mem_pct_val > 80 else WARN if mem_pct_val > 50 else SUCCESS
                    
                    docker_table.add_row(
                        name,
                        f"[{cpu_c}]{cpu_pct}[/]",
                        f"[{mem_c}]{mem_used}[/]",
                        f"[{mem_c}]{mem_perc}[/]",
                        net_io[:15] if len(net_io) > 15 else net_io
                    )
            else:
                docker_table.add_row("", "", "", "", "")
            
            # Combine into layout
            layout = Layout()
            layout.split_column(
                Layout(Panel(sys_table, title=f"[{TITLE_STYLE}] System Overview", border_style=ACCENT), size=10),
                Layout(proc_table, ratio=2),
                Layout(docker_table, ratio=2),
                Layout(Panel(f"[{DIM}]Press [bold]q[/] to return to main menu[/]", box=box.SIMPLE), size=3)
            )
            
            console.print(layout)
            
            # Short delay before checking for input again
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        pass
    except Exception as e:
        console.print(f"[{DANGER}]Error: {e}[/]")
        input_pause()


# ─── CADDY MANAGER ────────────────────────────────────────────────────────────

CADDYFILE_PATH = "/etc/caddy/Caddyfile"
CADDY_BINARY   = "caddy"

def caddy_is_installed():
    return shutil.which(CADDY_BINARY) is not None

def caddyfile_exists():
    return os.path.isfile(CADDYFILE_PATH)

def caddy_reload():
    result = subprocess.run(
        "sudo systemctl reload caddy",
        shell=True, capture_output=True, text=True
    )
    return result.returncode == 0

def read_caddyfile():
    try:
        with open(CADDYFILE_PATH, "r") as f:
            return f.read()
    except PermissionError:
        result = subprocess.run(
            f"sudo cat {CADDYFILE_PATH}",
            shell=True, capture_output=True, text=True
        )
        return result.stdout if result.returncode == 0 else None
    except Exception:
        return None

def write_caddyfile(content):
    try:
        with open(CADDYFILE_PATH, "w") as f:
            f.write(content)
        return True
    except PermissionError:
        import tempfile
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".caddyfile", delete=False)
        tmp.write(content)
        tmp.flush()
        tmp.close()
        result = subprocess.run(
            f"sudo mv {tmp.name} {CADDYFILE_PATH} && sudo chown root:root {CADDYFILE_PATH}",
            shell=True, capture_output=True, text=True
        )
        return result.returncode == 0
    except Exception:
        return False

def parse_caddy_entries(content):
    entries = []
    lines = content.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line and not line.startswith("#") and line.endswith("{"):
            domain = line.rstrip("{").strip()
            proxy = None
            i += 1
            depth = 1
            while i < len(lines) and depth > 0:
                inner = lines[i].strip()
                if inner.endswith("{"):
                    depth += 1
                if inner == "}":
                    depth -= 1
                if depth > 0 and "reverse_proxy" in inner:
                    proxy = inner.replace("reverse_proxy", "").strip()
                i += 1
            entries.append((domain, proxy or "?"))
            continue
        i += 1
    return entries

def remove_caddy_block(content, domain_to_remove):
    lines = content.splitlines(keepends=True)
    new_lines = []
    skip = False
    depth = 0
    for line in lines:
        stripped = line.strip()
        if domain_to_remove in stripped and stripped.endswith("{") and not skip:
            skip = True
            depth = 1
            continue
        if skip:
            if stripped.endswith("{"):
                depth += 1
            if stripped == "}":
                depth -= 1
                if depth == 0:
                    skip = False
            continue
        new_lines.append(line)
    return "".join(new_lines)

def manage_caddy():
    clear()
    print_banner()
    console.print(Rule(f"[{TITLE_STYLE}]  Caddy Reverse Proxy Manager"))
    console.print()

    if not caddy_is_installed():
        console.print(f"[{DANGER}]Caddy is not installed or not in PATH.[/]")
        console.print(f"[{DIM}]Install: sudo dnf install caddy  (Fedora)  |  sudo apt install caddy  (Debian/Ubuntu)[/]")
        input_pause()
        return

    console.print(f"[{SUCCESS}]✔ Caddy:[/] [{DIM}]{shutil.which(CADDY_BINARY)}[/]")

    if not caddyfile_exists():
        console.print(f"[{WARN}]Caddyfile not found at {CADDYFILE_PATH}[/]")
        create = Confirm.ask("Create a new empty Caddyfile?")
        if not create:
            input_pause()
            return
        subprocess.run(f"sudo mkdir -p {os.path.dirname(CADDYFILE_PATH)}", shell=True)
        ok = write_caddyfile("# Caddyfile — managed by dockertui\n\n")
        if ok:
            console.print(f"[{SUCCESS}]Created {CADDYFILE_PATH}[/]")
        else:
            console.print(f"[{DANGER}]Failed to create Caddyfile. Try running with sudo.[/]")
            input_pause()
            return
    else:
        console.print(f"[{SUCCESS}]✔ Caddyfile:[/] [{DIM}]{CADDYFILE_PATH}[/]\n")

    while True:
        console.print(f"  [{ACCENT}][1][/]  View current entries")
        console.print(f"  [{SUCCESS}][2][/]  Add new reverse proxy entry")
        console.print(f"  [{DANGER}][3][/]  Remove an entry")
        console.print(f"  [{WARN}][4][/]  Reload Caddy")
        console.print(f"  [{DIM}][0][/]  Back\n")
        choice = Prompt.ask("Select", choices=["0","1","2","3","4"])

        if choice == "0":
            return

        elif choice == "1":
            content = read_caddyfile()
            if content is None:
                console.print(f"[{DANGER}]Cannot read Caddyfile (permission denied?)[/]")
                input_pause()
            else:
                entries = parse_caddy_entries(content)
                if not entries:
                    console.print(f"[{WARN}]No entries found in Caddyfile.[/]")
                else:
                    table = Table(box=box.ROUNDED, border_style=ACCENT, expand=True)
                    table.add_column("#", style=DIM, width=4)
                    table.add_column("Domain", style="bold")
                    table.add_column("Proxy Target", style=ACCENT)
                    for i, (domain, proxy) in enumerate(entries, 1):
                        table.add_row(str(i), domain, proxy)
                    console.print(table)
                console.print()
                input_pause()

        elif choice == "2":
            console.print()
            console.print(f"[{ACCENT}]Add New Reverse Proxy Entry[/]\n")

            domain = Prompt.ask(f"  [{ACCENT}]Subdomain[/] (e.g. sonarr.omar.lab)").strip()
            if not domain:
                console.print(f"[{DANGER}]Domain cannot be empty.[/]")
                time.sleep(1)
                continue

            ip = Prompt.ask(f"  [{ACCENT}]Target IP[/] (e.g. 192.168.0.115)").strip()
            port = Prompt.ask(f"  [{ACCENT}]Target Port[/] (e.g. 8989)").strip()

            if not ip or not port:
                console.print(f"[{DANGER}]IP and port cannot be empty.[/]")
                time.sleep(1)
                continue

            https_upstream = Confirm.ask(f"  Does the target use HTTPS internally? (e.g. Cockpit)", default=False)

            if https_upstream:
                proxy_block = (
                    f"    reverse_proxy https://{ip}:{port} {{\n"
                    f"        transport http {{\n"
                    f"            tls_insecure_skip_verify\n"
                    f"        }}\n"
                    f"    }}"
                )
            else:
                proxy_block = f"    reverse_proxy {ip}:{port}"

            entry = f"\nhttp://{domain} {{\n{proxy_block}\n}}\n"

            content = read_caddyfile() or ""
            if domain in content:
                console.print(f"[{WARN}]Entry for [{ACCENT}]{domain}[/] already exists.[/]")
                overwrite = Confirm.ask("Overwrite it?", default=False)
                if not overwrite:
                    continue
                content = remove_caddy_block(content, domain)

            ok = write_caddyfile(content + entry)
            if ok:
                console.print(f"\n[{SUCCESS}]✔ Added:[/] [{ACCENT}]http://{domain}[/] → [{WARN}]{ip}:{port}[/]")
                if Confirm.ask("Reload Caddy now?", default=True):
                    if caddy_reload():
                        console.print(f"[{SUCCESS}]✔ Caddy reloaded.[/]")
                    else:
                        console.print(f"[{WARN}]Reload may have failed. Check: sudo systemctl status caddy[/]")
            else:
                console.print(f"[{DANGER}]Failed to write Caddyfile. Try running with sudo.[/]")
            console.print()
            input_pause()

        elif choice == "3":
            content = read_caddyfile()
            if not content:
                console.print(f"[{DANGER}]Cannot read Caddyfile.[/]")
                input_pause()
                continue

            entries = parse_caddy_entries(content)
            if not entries:
                console.print(f"[{WARN}]No entries to remove.[/]")
                input_pause()
                continue

            table = Table(box=box.SIMPLE, border_style=DIM)
            table.add_column("#", style=DIM, width=4)
            table.add_column("Domain", style="bold")
            table.add_column("Proxy", style=DIM)
            for i, (domain, proxy) in enumerate(entries, 1):
                table.add_row(str(i), domain, proxy)
            console.print(table)

            choices = ["0"] + [str(i) for i in range(1, len(entries)+1)]
            sel = Prompt.ask("Remove # (0 to cancel)", choices=choices)
            if sel == "0":
                continue

            domain_to_remove = entries[int(sel)-1][0]
            if Confirm.ask(f"[{DANGER}]Remove {domain_to_remove}?[/]"):
                ok = write_caddyfile(remove_caddy_block(content, domain_to_remove))
                if ok:
                    console.print(f"[{SUCCESS}]✔ Removed {domain_to_remove}[/]")
                    if Confirm.ask("Reload Caddy now?", default=True):
                        if caddy_reload():
                            console.print(f"[{SUCCESS}]✔ Caddy reloaded.[/]")
                        else:
                            console.print(f"[{WARN}]Reload may have failed.[/]")
                else:
                    console.print(f"[{DANGER}]Failed to write Caddyfile.[/]")
            console.print()
            input_pause()

        elif choice == "4":
            console.print(f"\n[{WARN}]Reloading Caddy...[/]")
            if caddy_reload():
                console.print(f"[{SUCCESS}]✔ Caddy reloaded successfully.[/]")
            else:
                console.print(f"[{DANGER}]Reload failed. Check: sudo systemctl status caddy[/]")
            console.print()
            input_pause()

        clear()
        print_banner()
        console.print(Rule(f"[{TITLE_STYLE}]  Caddy Reverse Proxy Manager"))
        console.print()
        console.print(f"[{SUCCESS}]✔ Caddy found[/]  [{SUCCESS}]✔ Caddyfile: {CADDYFILE_PATH}[/]\n")

# ─── HELPERS ──────────────────────────────────────────────────────────────────

def input_pause():
    console.print(f"[{DIM}]Press Enter to return to menu...[/]")
    input()

# ─── MAIN MENU ────────────────────────────────────────────────────────────────

def main():
    if not check_runtime():
        console.print(f"[{WARN}]No container runtime detected (Docker or Podman).[/]")

    while True:
        clear()
        print_banner()
        console.print(Rule(f"[{TITLE_STYLE}]  Main Menu"))
        console.print()

        runtime_label = RUNTIME_LABEL if RUNTIME_LABEL else "Container Runtime"
        menu = [
            ("1", "System Overview", "CPU, RAM, Swap, Disk, Network", ACCENT),
            ("2", "Top Processes", "RAM & CPU by process", ACCENT),
            ("3", f"{runtime_label} Status", "All containers + state", ACCENT),
            ("4", f"{runtime_label} Stats", "Per-container CPU & RAM", ACCENT),
            ("5", f"{runtime_label} Control", "Start / Stop / Restart / Logs", ACCENT),
            ("6", f"{runtime_label} Cleanup", "Prune containers, images, volumes", WARN),
            ("7", "Disk Usage", "All mounted partitions", ACCENT),
            ("8", "Systemd Services", "Running services", ACCENT),
            ("9", "Live Monitor", "Real-time CPU & RAM", SUCCESS),
            ("c", "Caddy Manager", "Add/remove reverse proxy entries", "magenta"),
            ("0", "Exit", "", DANGER),
        ]

        for key, label, desc, color in menu:
            desc_part = f"[{DIM}]— {desc}[/]" if desc else ""
            console.print(f"  [{color}][{key}][/]  [bold]{label}[/]  {desc_part}")

        console.print()
        choice = Prompt.ask(f"[{ACCENT}]Enter selection[/]", choices=[m[0] for m in menu], show_choices=False).strip().lower()

        actions = {
            "1": show_system_overview,
            "2": show_top_processes,
            "3": show_docker_status,
            "4": show_docker_stats,
            "5": docker_control,
            "6": docker_prune,
            "7": show_disk_usage,
            "8": show_services,
            "9": live_monitor,
            "c": manage_caddy,
            "0": lambda: sys.exit(0),
        }

        if choice in actions:
            actions[choice]()

if __name__ == "__main__":
    main()
