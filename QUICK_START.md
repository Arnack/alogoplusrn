# Quick Start - Android Ownership Verification

## What You Need
- Android SDK installed (or use EAS Build alternative)
- Java JDK 8 or higher

## One-Command Solution

```bash
./complete-build.sh
```

This will:
1. ✅ Create the `adi-registration.properties` file with your token
2. ✅ Generate a signing keystore
3. ✅ Create a minimal Android project with package `com.algoritmplus.app`
4. ✅ Build a release APK
5. ✅ Sign the APK with your keystore
6. ✅ Display the SHA256 fingerprint
7. ✅ Output the signed APK ready for upload

## Alternative: Manual Steps

If the automatic script doesn't work, follow these manual steps:

### 1. Generate Keystore
```bash
keytool -genkey -v \
    -keystore android-keystore.jks \
    -alias upload-key \
    -keyalg RSA \
    -keysize 2048 \
    -validity 10000 \
    -storepass android123 \
    -keypass android123 \
    -dname "CN=com.algoritmplus.app, OU=AlgoritmPlus, O=AlgoritmPlus, L=City, S=State, C=US"
```

### 2. Create Android Project
```bash
./setup-minimal-android.sh
```

### 3. Build APK
```bash
cd android-minimal
./gradlew assembleRelease
cd ..
```

### 4. Sign APK
```bash
apksigner sign \
    --ks android-keystore.jks \
    --ks-key-alias upload-key \
    --ks-pass pass:android123 \
    --key-pass pass:android123 \
    --out signed-apk/algoritmplus-signed.apk \
    android-minimal/app/build/outputs/apk/release/app-release-unsigned.apk
```

### 5. Get Fingerprint
```bash
keytool -list -v -keystore android-keystore.jks -alias upload-key -storepass android123 | grep SHA256
```

## No Android SDK? Use EAS Build

1. Install EAS CLI: `npm install -g eas-cli`
2. Build: `eas build --platform android --profile preview`
3. Download the APK when complete
4. Sign it: `apksigner sign --ks android-keystore.jks --ks-key-alias upload-key --ks-pass pass:android123 --key-pass pass:android123 --out signed.apk downloaded.apk`

## Files Created

| File | Purpose |
|------|---------|
| `assets/adi-registration.properties` | Registration token file |
| `android-keystore.jks` | Signing keystore |
| `android-minimal/` | Minimal Android project |
| `signed-apk/algoritmplus-signed.apk` | Final signed APK |

## Upload

Upload `signed-apk/algoritmplus-signed.apk` to Google Play Console to complete ownership verification.

## Important

⚠️ **Save your keystore!** You'll need it for all future updates to this app.
