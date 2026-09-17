#!/bin/bash
# =============================================================================
# config.sh — Build-target constants for WSABuilds
#
# Target: WSA x64  |  Magisk Stable  |  OpenGApps Pico  |  Retail  |  Win 11
#
# Source this file from build.sh and any other script that needs these values.
# ALL values are declared readonly so downstream scripts cannot accidentally
# override them.
#
# Copyright (C) 2024 WSABuilds Contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
# =============================================================================
# shellcheck disable=SC2034

# ---------------------------------------------------------------------------
# Architecture & WSA release channel
# ---------------------------------------------------------------------------
TARGET_ARCH="${TARGET_ARCH:-x64}"
# Native machine naming used by GApps / OpenGApps artifacts ("x86_64" or "arm64").
# Kept distinct from TARGET_ARCH because WSA x64 packages ship x86_64 GApps images.
# Defaults from TARGET_ARCH (x64 -> x86_64, arm64 -> arm64); an explicit
# TARGET_ARCH_NATIVE in the environment still wins for custom GApps images.
case "${TARGET_ARCH_NATIVE:-}" in
    x86_64|arm64) : ;;
    *) case "${TARGET_ARCH}" in
           arm64) TARGET_ARCH_NATIVE="arm64" ;;
           *)     TARGET_ARCH_NATIVE="x86_64" ;;
       esac ;;
esac
TARGET_RELEASE_TYPE="${TARGET_RELEASE_TYPE:-retail}"

# ---------------------------------------------------------------------------
# Root solution
# ---------------------------------------------------------------------------
TARGET_ROOT_SOL="${TARGET_ROOT_SOL:-magisk}"
TARGET_MAGISK_VER="${TARGET_MAGISK_VER:-stable}"
MIN_MAGISK_VERSION_CODE=26000         # Magisk 26.0 minimum requirement

# ---------------------------------------------------------------------------
# GApps
# ---------------------------------------------------------------------------
TARGET_GAPPS_VARIANT="${TARGET_GAPPS_VARIANT:-pico}"           # Minimal GApps (Play Store + GMS)
TARGET_GAPPS_SOURCE="${TARGET_GAPPS_SOURCE:-wsa-addon}"       # wsa-addon (LSPosed/WSA-Addon)

# Android API level shipped by the current WSA generation.
# WSA >= 2211 ships API 33 (Android 13); older builds ship API 32.
# This is the *default*; build.sh may downgrade it after inspecting the WSA
# major version extracted from the package.
readonly DEFAULT_ANDROID_API=33
readonly ANDROID_API_MAP_30="11.0"
readonly ANDROID_API_MAP_32="12.1"
readonly ANDROID_API_MAP_33="13.0"

# GApps ext4 images and initrd mount scripts for Android 13 (x86_64 and arm64)
# are published in the LSPosed/WSA-Addon releases repo and consumed by
# generateGappsLink.py.
readonly GAPPS_ADDON_OWNER="LSPosed"
readonly GAPPS_ADDON_REPO="WSA-Addon"

# ---------------------------------------------------------------------------
# Device model (used by fixGappsProp.py for GApps compatibility)
# ---------------------------------------------------------------------------
readonly TARGET_DEVICE_MODEL="redfin"         # Pixel 5
readonly TARGET_DEVICE_NAME="redfin"

# ---------------------------------------------------------------------------
# Derived file / directory names (computed, not overridable)
# ---------------------------------------------------------------------------
# These are functions rather than readonly vars because they depend on
# ANDROID_API which may be adjusted at runtime.
gapps_image_name() {
    local api="${1:-$DEFAULT_ANDROID_API}"
    local api_ver
    case "$api" in
        30) api_ver="$ANDROID_API_MAP_30" ;;
        32) api_ver="$ANDROID_API_MAP_32" ;;
        33) api_ver="$ANDROID_API_MAP_33" ;;
        *)  echo "config.sh: unknown API level: $api" >&2; return 1 ;;
    esac
    case "$TARGET_ARCH_NATIVE" in
        x86_64|arm64) : ;;
        *) echo "config.sh: unsupported GApps arch: $TARGET_ARCH_NATIVE" >&2; return 1 ;;
    esac
    echo "gapps-${api_ver}-${TARGET_ARCH_NATIVE}.img"
}

gapps_rc_name() {
    local api="${1:-$DEFAULT_ANDROID_API}"
    local api_ver
    case "$api" in
        30) api_ver="$ANDROID_API_MAP_30" ;;
        32) api_ver="$ANDROID_API_MAP_32" ;;
        33) api_ver="$ANDROID_API_MAP_33" ;;
        *)  echo "config.sh: unknown API level: $api" >&2; return 1 ;;
    esac
    echo "gapps-${api_ver}.rc"
}
