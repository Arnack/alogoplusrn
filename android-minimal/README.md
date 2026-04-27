# Minimal Android Project for Ownership Verification
# Package: com.algoritmplus.app

This directory contains a minimal Android project structure for APK signing.

## Structure
```
android-minimal/
├── app/
│   ├── src/
│   │   └── main/
│   │       ├── AndroidManifest.xml
│   │       ├── assets/
│   │       │   └── adi-registration.properties
│   │       └── java/com/algoritmplus/app/
│   │           └── MainActivity.java
│   └── build.gradle
├── build.gradle
├── gradle.properties
└── settings.gradle
```

## Quick Build

```bash
# Create the minimal project
mkdir -p android-minial
cd android-minimal

# Use the setup script
../setup-minimal-android.sh
```
