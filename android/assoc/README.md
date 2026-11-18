# Itonami Registry Assoc for Android

The Android app starts at the Registry site's existing association page. The build embeds the static site and the verified association snapshots from the same checkout. Search and source information work without network access. Tap the EDN link to read the verified bundled record in the app. A citation can be opened in Android's browser when connectivity is available.

The wrapper pins and verifies the canonical Kotoba browser runtime, license and notice at build time. The descriptor declares memory-only filters, zero workers and zero external service operations. The Tauri window keeps the Registry on its local HTTPS origin and hands web citations to the system browser.

## Build a developer APK

Install the root Python requirements into a virtual environment on PATH. Set up the Android SDK, NDK, JDK and arm64 Rust target with the [Tauri prerequisites](https://v2.tauri.app/start/prerequisites/#android). The Android SDK platform must support the compile SDK selected by the pinned Tauri CLI.

From this directory:

```sh
npm ci
npm run android:init
npm run android:apk -- --target aarch64
```

The APK appears under `src-tauri/gen/android/app/build/outputs/apk/`. It uses Android's developer signing identity and is intended for testing and sideloading. Install with `adb -s DEVICE install APK`. The launcher label is **Itonami Registry Assoc**. Confirm the device ABI with `adb -s DEVICE shell getprop ro.product.cpu.abilist`.

To check offline search, enable airplane mode and turn off Wi-Fi before launching. Choose Switzerland and ISIC 6419, then open **Swiss Bankers Association**. The **CDB 20** record should show its retrieval date and the Swiss Banking source. Opening the external source page requires connectivity.
