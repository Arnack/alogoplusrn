# Android Ownership Verification Setup

## Overview
This guide will help you create and sign an APK to prove ownership of `com.algoritmplus.app`.

## Files Created
- `assets/adi-registration.properties` - Contains your registration token
- `generate-keystore.sh` - Generates a signing keystore
- `build-signed-apk.sh` - Builds and signs the APK

## Quick Start

### Option 1: Automated Build (Recommended)

```bash
# Run the build script
./build-signed-apk.sh
```

This will:
1. Verify the registration properties file
2. Generate a keystore (if needed)
3. Build the Android project
4. Sign the APK
5. Output the signed APK to `./signed-apk/algoritmplus-signed.apk`

### Option 2: Manual Steps

#### 1. Generate Keystore
```bash
./generate-keystore.sh
```

Or manually:
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

#### 2. Generate Android Project
```bash
npx expo prebuild --platform android
```

#### 3. Build APK
```bash
cd android
./gradlew assembleRelease
cd ..
```

#### 4. Sign the APK
```bash
# Find the unsigned APK
UNSIGNED_APK=$(find ./android/app/build/outputs/apk/release -name "*.apk" | head -1)

# Sign it
apksigner sign \
    --ks android-keystore.jks \
    --ks-key-alias upload-key \
    --ks-pass pass:android123 \
    --key-pass pass:android123 \
    --out signed-apk/algoritmplus-signed.apk \
    "$UNSIGNED_APK"
```

#### 5. Verify Signature
```bash
apksigner verify --verbose signed-apk/algoritmplus-signed.apk
```

#### 6. Get Certificate Fingerprint
```bash
keytool -list -v -keystore android-keystore.jks -alias upload-key -storepass android123 | grep "SHA256:"
```

## Upload the APK

Once you have the signed APK:
1. Go to your Google Play Console
2. Navigate to the app ownership verification page
3. Upload `signed-apk/algoritmplus-signed.apk`
4. Google will verify the signature matches your public key

## Keystore Details

- **Path:** `./android-keystore.jks`
- **Alias:** `upload-key`
- **Store Password:** `android123`
- **Key Password:** `android123`

⚠️ **IMPORTANT:** Save this keystore securely. You'll need it for all future app updates.

## Troubleshooting

### Android SDK Not Found
Make sure you have Android SDK installed and configured:
```bash
export ANDROID_HOME=$HOME/Library/Android/sdk
export PATH=$ANDROID_HOME/platform-tools:$PATH
export PATH=$ANDROID_HOME/emulator:$PATH
export PATH=$ANDROID_HOME/tools:$PATH
export PATH=$ANDROID_HOME/tools/bin:$PATH
```

### Gradle Build Fails
Ensure you have the required Android build tools:
```bash
sdkmanager "platform-tools" "platforms;android-34" "build-tools;34.0.0"
```

### apksigner Not Found
Install Android SDK Build-Tools:
```bash
sdkmanager "build-tools;34.0.0"
```

The apksigner will be at: `$ANDROID_HOME/build-tools/34.0.0/apksigner`

## Package Information
- **Package Name:** `com.algoritmplus.app`
- **Registration Token:** `CA2372QQOWWKCAAAAAAAAAAAAA`
