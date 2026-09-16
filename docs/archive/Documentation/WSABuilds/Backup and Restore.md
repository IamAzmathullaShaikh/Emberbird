# WSABuilds &nbsp; &nbsp; <img src="https://img.shields.io/github/downloads/IamAzmathullaShaikh/WSABuilds/total?label=Total%20Downloads&style=for-the-badge"/> &nbsp; 

<picture><img style="float: left;" src="https://img.icons8.com/fluency/96/cloud-backup-restore.png" width="60" height="60"/></picture><h1> &nbsp; Backup and Restore Userdata</h1>

This guide provides instructions for backing up and restoring your WSA user data (`userdata.vhdx`), which stores installed Android applications, settings, game saves, and accounts.

---

## Method 1: WSABuilds Manager (Recommended)

WSABuilds Manager provides automated, atomic cold VHDX backups with checksum verification and rollback safety.

### Creating a Backup
1. Launch **WSABuilds Manager**.
2. Navigate to the **Backups** tab.
3. Ensure WSA is not running (WSABuilds Manager automatically performs a shutdown check).
4. Click **Create Backup**.
5. The engine verifies file lock release, streams `userdata.vhdx` to the backup directory, records SHA-256 integrity checksums, and saves retention metadata.

### Restoring a Backup
1. Open the **Backups** tab in **WSABuilds Manager**.
2. Select a verified backup candidate from the candidate list.
3. Click **Restore**.
4. The restore coordinator validates the backup archive checksum, creates a safety rollback snapshot (`.pre_restore.bak`), writes the candidate, and confirms filesystem integrity.

---

## Method 2: Manual Backup and Restore

If you prefer performing manual file operations via Windows Explorer or PowerShell:

### Backing Up Manually
1. Stop WSA completely:
   - Open **Windows Subsystem for Android™ Settings**.
   - Click **Turn off Windows Subsystem for Android™**.
2. Wait 10 seconds to ensure the VHDX file handle is released.
3. Copy `userdata.vhdx` from:
   ```text
   %LOCALAPPDATA%\Packages\MicrosoftCorporationII.WindowsSubsystemForAndroid_8wekyb3d8bbwe\LocalCache\userdata.vhdx
   ```
   to a secure backup folder.

### Restoring Manually
1. Fully terminate WSA using `WsaClient.exe /shutdown` or WSA Settings.
2. Verify that no processes (`WsaService.exe`, `vmmemWSL`) are holding locks on `userdata.vhdx`.
3. Copy your saved `userdata.vhdx` into:
   ```text
   %LOCALAPPDATA%\Packages\MicrosoftCorporationII.WindowsSubsystemForAndroid_8wekyb3d8bbwe\LocalCache\userdata.vhdx
   ```
4. Launch WSA. Your apps and data will be restored.
