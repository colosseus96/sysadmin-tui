# DockerTUI - Terminal User Interface for Docker Monitoring

A powerful, interactive terminal-based user interface for monitoring Docker containers and system resources in real-time. Built with Python, this tool provides an intuitive way to view container statistics, manage containers, and monitor system performance without leaving your terminal.

## Features

### 🐳 Docker Container Management
- **View all containers** (running and stopped) with detailed information
- **Real-time statistics** including CPU usage, memory consumption, and network I/O
- **Container lifecycle management**: Start, stop, restart, pause, unpause, and remove containers
- **Detailed container inspection** showing configuration, networks, mounts, and environment variables
- **Access container logs** directly from the TUI
- **Execute shell commands** inside running containers

### 💻 System Resource Monitoring
- **Live process monitoring** showing PID, process name, user, RAM usage, CPU%, and status
- **Docker daemon statistics** including total containers, running/paused/stopped counts
- **System-wide resource usage** (CPU, Memory, Disk)
- **Network statistics** for Docker containers

### 🎨 User-Friendly Interface
- **Interactive main menu** with keyboard navigation
- **Color-coded tables** using the Rich library for better readability
- **Non-blocking input** allowing instant response to user commands
- **Press 'q'** at any time to return to the main menu from live monitoring
- **Clear footer instructions** showing available keyboard shortcuts

## Requirements

- Python 3.6 or higher
- Docker installed and running
- pip (Python package manager)

### Python Dependencies
- `rich>=13.0.0` - For beautiful terminal formatting
- `psutil>=5.9.0` - For system and process monitoring

## Installation

### Option 1: Automated Installation (Recommended)

Run the provided installation script:

```bash
./install.sh
```

This script will:
- Check if Python 3 is installed
- Automatically install pip if missing
- Detect virtual environments and warn about system-wide installation
- Install all required dependencies from `requirements.txt`
- Provide helpful next steps

### Option 2: Manual Installation

Install dependencies manually using pip:

```bash
pip install rich psutil
```

Or using the requirements file:

```bash
pip install -r requirements.txt
```

## Usage

Run the application:

```bash
python dockertui.py
```

### Main Menu Options

1. **List Containers** - View all Docker containers with their status
2. **Container Stats** - See real-time resource usage for containers
3. **Start Container** - Start a stopped container
4. **Stop Container** - Stop a running container
5. **Restart Container** - Restart a container
6. **Remove Container** - Delete a container
7. **Pause Container** - Pause a running container
8. **Unpause Container** - Resume a paused container
9. **View Logs** - Access container logs
10. **Inspect Container** - View detailed container configuration
11. **Live Process Monitor** - Real-time system and Docker monitoring *(Press 'q' to return)*
12. **Exit** - Close the application

### Keyboard Navigation

- Use **number keys (0-9)** to select menu options
- Press **'q'** in live monitoring mode to return to the main menu
- Follow on-screen prompts for container ID selection

## Live Process Monitor

The live monitoring feature (Option 11) provides:

### System Overview
- Total CPU cores and current CPU usage percentage
- Total and available memory with usage statistics
- Disk usage information

### Top Processes Table
Shows the top 10 processes by memory usage:
- **PID** - Process ID
- **Name** - Process name
- **User** - Owner of the process
- **RAM** - Memory usage in MB
- **CPU%** - CPU utilization percentage
- **Status** - Current process status

### Docker Containers Table
Displays all running containers:
- **Name** - Container name
- **CPU%** - Container CPU usage
- **RAM Used** - Memory consumption
- **RAM%** - Memory percentage
- **Net I/O** - Network input/output statistics

## Project Structure

```
dockertui/
├── dockertui.py        # Main application file
├── requirements.txt    # Python dependencies
├── install.sh         # Automated installation script
├── README.md          # This file
└── LICENSE            # MIT License
```

## Examples

### Viewing Container Statistics
```
Select option: 2
Enter container ID or name: my-nginx-container
```

### Live Monitoring
```
Select option: 11
[Live monitoring starts - press 'q' to return to menu]
```

### Removing a Container
```
Select option: 6
Enter container ID or name: old-container
Confirm removal? (y/n): y
```

## Troubleshooting

### Docker Permission Issues
If you encounter permission errors, ensure your user is in the docker group:
```bash
sudo usermod -aG docker $USER
newgrp docker
```

### Missing Dependencies
If you see import errors, run:
```bash
./install.sh
```
or
```bash
pip install -r requirements.txt
```

### Docker Not Running
Ensure Docker daemon is running:
```bash
sudo systemctl start docker
```

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests to improve the project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

DockerTUI - A terminal-based Docker management tool built for developers and system administrators who prefer working in the command line.

---

**Note**: This tool requires Docker to be installed and running on your system. Make sure you have appropriate permissions to interact with the Docker daemon.
