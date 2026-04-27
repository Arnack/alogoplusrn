#!/bin/bash

# Script to build and sign an APK for Android ownership verification
# Package: com.algoritmplus.app

set -e

echo "=== Building and Signing APK for Android Ownership Verification ==="
echo "Package: com.algoritmplus.app"
echo ""

# Configuration
KEYSTORE_PATH="./android-keystore.jks"
KEY_ALIAS="upload-key"
STORE_PASSWORD="android123"
KEY_PASSWORD="android123"
OUTPUT_DIR="./signed-apk"

# Step 1: Check if adi-registration.properties exists
echo "Step 1: Checking adi-registration.properties..."
if [ ! -f "./assets/adi-registration.properties" ]; then
    echo "✗ ERROR: assets/adi-registration.properties not found!"
    echo "Please create this file with your registration token."
    exit 1
fi
echo "✓ Found assets/adi-registration.properties"

# Step 2: Generate keystore if it doesn't exist
echo ""
echo "Step 2: Checking keystore..."
if [ ! -f "$KEYSTORE_PATH" ]; then
    echo "Generating new keystore..."
    keytool -genkey -v \
        -keystore "$KEYSTORE_PATH" \
        -alias "$KEY_ALIAS" \
        -keyalg RSA \
        -keysize 2048 \
        -validity 10000 \
        -storepass "$STORE_PASSWORD" \
        -keypass "$KEY_PASSWORD" \
        -dname "CN=com.algoritmplus.app, OU=AlgoritmPlus, O=AlgoritmPlus, L=City, S=State, C=US" \
        2>/dev/null
    echo "✓ Keystore generated"
else
    echo "✓ Keystore already exists"
fi

# Step 3: Get certificate fingerprint
echo ""
echo "Step 3: Certificate fingerprint (SHA256):"
keytool -list -v -keystore "$KEYSTORE_PATH" -alias "$KEY_ALIAS" -storepass "$STORE_PASSWORD" 2>/dev/null | grep "SHA256:" | head -1

# Step 4: Prebuild Android project
echo ""
echo "Step 4: Generating Android project..."
npx expo prebuild --platform android --clean 2>/dev/null || {
    echo "Note: If prebuild fails, make sure you have Android SDK installed"
    echo "Alternative: Use EAS Build (eas build --platform android --profile preview)"
}

# Step 5: Build unsigned APK
echo ""
echo "Step 5: Building APK..."
if [ -d "./android" ]; then
    cd android
    chmod +x ./gradlew
    ./gradlew assembleRelease 2>/dev/null || {
        echo "✗ ERROR: Gradle build failed"
        echo "Make sure you have Android SDK and NDK installed"
        exit 1
    }
    cd ..
    
    UNSIGNED_APK=$(find ./android/app/build/outputs/apk/release -name "*.apk" | head -1)
    
    if [ -z "$UNSIGNED_APK" ]; then
        echo "✗ ERROR: No APK found after build"
        exit 1
    fi
    
    echo "✓ Built APK: $UNSIGNED_APK"
    
    # Step 6: Sign the APK
    echo ""
    echo "Step 6: Signing APK..."
    mkdir -p "$OUTPUT_DIR"
    
    SIGNED_APK="$OUTPUT_DIR/algoritmplus-signed.apk"
    
    # Try using apksigner first, fallback to jarsigner
    if command -v apksigner &> /dev/null; then
        apksigner sign \
            --ks "$KEYSTORE_PATH" \
            --ks-key-alias "$KEY_ALIAS" \
            --ks-pass "pass:$STORE_PASSWORD" \
            --key-pass "pass:$KEY_PASSWORD" \
            --out "$SIGNED_APK" \
            "$UNSIGNED_APK"
        echo "✓ APK signed with apksigner"
    else
        echo "apksigner not found, using jarsigner..."
        cp "$UNSIGNED_APK" "$SIGNED_APK"
        jarsigner \
            -verbose \
            -keystore "$KEYSTORE_PATH" \
            -storepass "$STORE_PASSWORD" \
            -keypass "$KEY_PASSWORD" \
            "$SIGNED_APK" \
            "$KEY_ALIAS"
        echo "✓ APK signed with jarsigner"
    fi
    
    # Step 7: Verify the signature
    echo ""
    echo "Step 7: Verifying APK signature..."
    if command -v apksigner &> /dev/null; then
        apksigner verify --verbose "$SIGNED_APK"
    fi
    
    # Step 8: Display APK info
    echo ""
    echo "=== Build Complete ==="
    echo "Signed APK: $SIGNED_APK"
    echo "Package: com.algoritmplus.app"
    echo ""
    echo "Keystore Details:"
    echo "  Path: $KEYSTORE_PATH"
    echo "  Alias: $KEY_ALIAS"
    echo "  Store Password: $STORE_PASSWORD"
    echo "  Key Password: $KEY_PASSWORD"
    echo ""
    echo "SHA256 Fingerprint:"
    keytool -list -v -keystore "$KEYSTORE_PATH" -alias "$KEY_ALIAS" -storepass "$STORE_PASSWORD" 2>/dev/null | grep "SHA256:" | head -1
    echo ""
    echo "Next: Upload $SIGNED_APK to complete ownership verification"
    
else
    echo "✗ ERROR: Android project not found"
    echo ""
    echo "Alternative approach - Use EAS Build:"
    echo "1. eas build --platform android --profile preview"
    echo "2. Download the APK"
    echo "3. Sign it manually with the keystore"
    echo ""
    echo "Or create a minimal Android project:"
    echo "1. Create a new Android Studio project with package com.algoritmplus.app"
    echo "2. Copy assets/adi-registration.properties to android/app/src/main/assets/"
    echo "3. Build and sign the APK"
fi
