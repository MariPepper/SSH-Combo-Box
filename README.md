# Required Installations

## Dependencies

```bash
sudo apt install -y python3 python3-paramiko iproute2
```

Or, if `python3-paramiko` is not available:

```bash
sudo apt install -y python3 python3-pip iproute2
pip3 install paramiko --break-system-packages
```

## Wordlist

```bash
cp /usr/share/seclists/Passwords/Common-Credentials/Pwdb_top-1000.txt ~/wl_custom.txt
```

Or, if you don't have SecLists:

```bash
sudo apt install -y seclists
cp /usr/share/seclists/Passwords/Common-Credentials/Pwdb_top-1000.txt ~/wl_custom.txt
```
<img width="1021" height="609" alt="2026-09-30 21_04_47-Zephir - VMware Workstation" src="https://github.com/user-attachments/assets/40b26baf-484f-474d-b4d3-a3dd8bf06604" />

## Comparative Table — fail2ban vs MaxStartups

### Definitions

| Parameter | What it controls | Where |
|-----------|------------------|-------|
| `fail2ban` | Blocks IPs after N failed attempts | Server |
| `MaxStartups` | Accepts N simultaneous unauthenticated connections | Server (`sshd_config`) |
| `Delay` | Time between attempts of the same instance | Attacker |
| `Instances` | Number of simultaneous connections from the attacker | Attacker |

### Scenarios

| Scenario | fail2ban | MaxStartups | Inst | Delay | Blocks? | Accepts? |
|----------|----------|-------------|------|-------|---------|----------|
| A | Active | 10 | 1 | 10s | Yes | Yes |
| B | Active | 10 | 4 | 10s | Yes | Yes |
| C | Active | 10 | 10 | 10s | Yes | Limit |
| D | Active | 10 | 20 | 10s | Yes | No |
| E | Active | 10 | 4 | 120s | No | Yes |
| F | Inactive | 10 | 4 | 10s | No | Yes |
| G | Inactive | 10 | 10 | 10s | No | Limit |
| H | Inactive | 10 | 20 | 10s | No | No |
| I | Inactive | 100 | 50 | 10s | No | Yes |
| J | Inactive | 100 | 150 | 1s | No | No |

### Summary

| Condition | Result |
|-----------|--------|
| `fail2ban` active + delay < 120s | BLOCKED |
| `fail2ban` active + delay > 120s | Not blocked, but SLOW |
| `fail2ban` inactive + instances <= 10 | WORKS |
| `fail2ban` inactive + instances > 10 | `MaxStartups` DISCARD |
| `fail2ban` inactive + `MaxStartups` high + instances <= limit | WORKS |

### Recommendation

- Disable `fail2ban` on the server
- Use delay 1-10s
- Use 4-10 instances

## Usage

```bash
python3 ~/ssh_combos_menu.py
```

### Menu Options

| # | Option |
|---|--------|
| 1 | Server IP |
| 2 | Wordlist |
| 3 | Users |
| 4 | Delay |
| 5 | Case variations |
| 6 | Numbers |
| 7 | Symbols |
| 8 | Positions |
| 9 | Letters (prefix/suffix) |
| 10 | Combination mode (1 or 2 words) |
| 11 | Execution mode (single or parallel) |
