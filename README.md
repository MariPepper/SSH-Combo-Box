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
