# Play Integrity & Banking Compatibility Setup Guide

This guide details how to configure Magisk, Zygisk, and the PlayIntegrityFix module on Windows Subsystem for Android to pass Google Play Integrity attestation and run banking, UPI, and financial applications.

---

## 1. Overview

Many banking and financial applications (such as PhonePe, Paytm, Google Pay, SBI YONO, and BHIM) require your device to pass Google Play Integrity attestation (MEETS_DEVICE_INTEGRITY) and detect whether the environment is modified or rooted.

By following this guide, you can cloak root access and pass device attestation on WSA.

---

## 2. Step 1: Enable Zygisk in Magisk

1. Launch the **Magisk** application from your Windows Start Menu or Android app list.
2. In the top-right corner of Magisk, click the **Settings (gear)** icon.
3. Scroll down to the **Magisk** section:
   - Toggle **Zygisk** to **Enabled**.
   - Toggle **Enforce DenyList** to **Enabled**.
4. Click **Configure DenyList**:
   - Tap the three-dot menu in the top right and check **Show system apps**.
   - Search for **Google Play Services** (com.google.android.gms) and expand it.
   - Check the boxes for com.google.android.gms and com.google.android.gms.unstable.
   - Search for your banking apps (e.g. PhonePe, SBI YONO, Paytm) and check all their processes.

---

## 3. Step 2: Install PlayIntegrityFix Module

1. Download the latest **PlayIntegrityFix** module zip release from the [PlayIntegrityFix Releases](https://github.com/chiteroman/PlayIntegrityFIX/releases).
2. Open the **Magisk** app on WSA.
3. Tap the **Modules** tab at the bottom right.
4. Tap **Install from storage**.
5. Select the downloaded PlayIntegrityFIX.zip.
6. Once installation completes, do not reboot immediately.

---

## 4. Step 3: Hide the Magisk App

1. In Magisk Settings, tap **Hide the Magisk app**.
2. When prompted, enter a generic name (e.g. Settings Manager or Tools).
3. Magisk will repackage itself under a randomized package name.

---

## 5. Step 4: Disable USB Debugging for Strict Banking Apps

Strict banking apps such as **SBI YONO** detect active Android Debug Bridge (ADB) connections:
1. Open the **Windows Subsystem for Android Settings** app from Windows Start.
2. Go to **Advanced settings**.
3. Toggle **Developer options** to **Off** (or ensure **USB debugging** is disabled).

---

## 6. Step 5: Restart WSA

1. In the WSA Settings application, click **Turn off Windows Subsystem for Android**.
2. Launch your banking app or Google Play Store.
3. Verify that the app launches and functions normally.
