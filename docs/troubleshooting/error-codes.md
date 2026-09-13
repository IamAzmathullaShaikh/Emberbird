# Common WSA Error Codes & Troubleshooting Resolutions

This guide provides cause analysis, symptoms, and exact resolution steps for the most common error codes encountered during Windows Subsystem for Android installation and runtime.

---

## 1. Error `0x80370102` (Virtual Machine Failed to Start)

### Cause
This error occurs when the Windows Subsystem for Android Hyper-V virtual machine envelope cannot initialize because **Hardware Virtualization** is disabled in the system BIOS/UEFI, or the **Virtual Machine Platform** Windows optional component is inactive.

### Symptoms
- When launching WSA or an Android app, an error dialog displays:
  > *"The virtual machine could not be started because a required feature is not installed." (Error code: 0x80370102)*
- WSA window terminates immediately upon startup.

### Resolution Steps

#### Step 1: Enable Hardware Virtualization in BIOS/UEFI
1. Shut down your PC completely.
2. Power on and repeatedly tap your motherboard BIOS key (`F2`, `F12`, `Del`, or `Esc` depending on manufacturer).
3. Locate the CPU / Virtualization configuration menu:
   - **For Intel Motherboards**: Enable **Intel Virtualization Technology (Intel VT-x)** and **Intel VT-d**.
   - **For AMD Motherboards**: Enable **SVM Mode (Secure Virtual Machine)** or **AMD-V**.
4. Save changes (`F10`) and restart into Windows.
5. Open **Task Manager** (`Ctrl + Shift + Esc`) -> **Performance** -> **CPU** and verify that **Virtualization: Enabled** is shown.

#### Step 2: Enable Virtual Machine Platform via PowerShell
Open an elevated PowerShell console (Run as Administrator) and execute:
```powershell
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
dism.exe /online /enable-feature /featurename:HypervisorPlatform /all /norestart
```
**Reboot your computer** immediately after running these commands.

---

## 2. Error `0x80070005` (Access is Denied / E_ACCESSDENIED)

### Cause
This error occurs when the Windows AppX deployment service (`AppXSvc`) lacks read or execute access to the folder containing your extracted WSA files, or when PowerShell script execution policy blocks local script execution.

### Symptoms
- PowerShell installer outputs red text:
  > *Add-AppxPackage : Deployment failed with HRESULT: 0x80070005, Access is denied.*
- AppX registration fails during `Install.ps1` execution.

### Resolution Steps

#### Step 1: Move WSA Folder to an Unrestricted Directory
Do not install WSA from protected user paths like `C:\Users\[Username]\AppData\Local\Temp` or directly off an external USB drive.
1. Move the extracted WSA folder to `C:\WSA` or `D:\WSA`.

#### Step 2: Grant Read & Execute Permissions to Application Packages
Windows sandboxed apps require the `ALL APPLICATION PACKAGES` security principal:
1. Right-click your extracted `WSA` folder and select **Properties**.
2. Go to the **Security** tab and click **Edit...**.
3. If `ALL APPLICATION PACKAGES` is not listed:
   - Click **Add...**.
   - In the object names box, enter: `ALL APPLICATION PACKAGES` and click **Check Names**.
   - Click **OK**.
4. Check **Read & execute**, **List folder contents**, and **Read**.
5. Click **Apply** -> **OK**.

#### Step 3: Run PowerShell with Execution Policy Bypass
Launch an elevated PowerShell console and run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process -Force
cd "C:\WSA"
.\Install.ps1
```

---

## 3. Error `0x80073CF9` (AppX Deployment Failed / Package Cache Error)

### Cause
Error `0x80073CF9` indicates that the Windows Store package manager failed to register the application because the Windows `AppReadiness` staging directory is missing, corrupt, or locked by a background Windows Update transaction.

### Symptoms
- PowerShell outputs:
  > *Deployment failed with HRESULT: 0x80073CF9, An internal error occurred with error 0x80073CF9.*
- Installation halts at 0% or 99% progress.

### Resolution Steps

#### Step 1: Verify and Recreate the `AppReadiness` Folder
A known Windows bug causes the `C:\Windows\AppReadiness` directory to go missing after certain Windows updates:
1. Open File Explorer and navigate to `C:\Windows`.
2. Look for a folder named `AppReadiness`:
   - If it is missing: Right-click -> **New** -> **Folder**, and name it `AppReadiness`.
3. Open `C:\Windows\System32` and verify if a folder named `AU` exists. If missing, create `C:\Windows\System32\AU`.

#### Step 2: Clear Windows Store Cache
1. Press `Windows Key + R` to open the Run dialog.
2. Type `wsreset.exe` and press `Enter`.
3. A blank command prompt window will open. Wait approximately 30 seconds until the Windows Store opens automatically.
4. Close the Windows Store.

#### Step 3: Restart AppX & Windows Update Services
Open an elevated PowerShell console and restart the required background services:
```powershell
net stop wuauserv
net stop bits
net stop appxsvc
net start appxsvc
net start bits
net start wuauserv
```
5. Rerun `Install.ps1`.
