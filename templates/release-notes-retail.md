<img src="https://upload.wikimedia.org/wikipedia/commons/e/e6/Windows_11_logo.svg" width="20%" height="20%">

# Windows Subsystem For Android (WSA) Retail Release

## Builds Last Updated: 
### - <<DATEOFRELEASE>> <<TIMEOFRELEASE>> GMT (Reason: <<REASONFORRELEASE>>) 

---

</br>

> [!CAUTION]
> - ## For anyone updating from a previous WSA Build: 
>   - ### Please backup your Userdata VHDX using this [guide](https://github.com/MustardChef/WSABuilds/blob/master/Documentation/WSABuilds/Backup%20and%20Restore.md), in the case that the builds in this release do not work as intended (crashes, bugs or not working), so that you can revert to the old version if needs be.
>
> - ## Ensure that 7-zip/WinRAR is up-to-date, before extracting, to avoid extraction errors. 

>  [!NOTE] 
> #### **Read the [guide](https://github.com/MustardChef/WSABuilds/blob/master/README.md) in full before installing. Ensure you meet the full [requirements](https://github.com/MustardChef/WSABuilds#requirements) for an installation on Windows 11.**
> #### **If you're updating WSA, merge the folders and replace the files for all items when asked** 

> [!IMPORTANT]
> If you have the official WSA installed or WSA installed that has not been downloaded from this repo, you must [completely uninstall](https://github.com/MustardChef/WSABuilds/blob/master/Documentation/WSABuilds/Uninstallation.md) it to use these builds.

---

### Follow these steps to install on Windows 10 / 11:

1. Extract the `.7z` archive using 7-zip and keep the extracted folder in a safe permanent directory (e.g. `Documents`).
2. Open the extracted folder and run `Run.bat`.
3. If registration fails, verify developer mode is enabled and run `Add-AppxPackage -Register .\AppxManifest.xml` in PowerShell.

## Changelog
- WSA Android Version: <<WSAANDROIDVERSION>>
- WSA Build Version: `<<WSA_VER>>`
- Magisk Stable Version: <<MAGISKSTABLEVERSION>>
- GApps Variant: <<GAPPS VARIANT>> (<<GAPPS TAG>>)

---

### Verified Release Verification
Every build artifact is accompanied by SHA256/SHA512 checksums and a cryptographically deterministic `release-metadata.json` manifest confirming package identity and signature stripping.
