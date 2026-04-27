#!/bin/bash

# Script to generate keystore and build signed APK for Android ownership verification
# Package: com.algoritmplus.app

echo "=== Android APK Signing Setup ==="
echo "Package: com.algoritmplus.app"
echo ""

# Step 1: Generate a keystore (if it doesn't exist)
KEYSTORE_PATH="./android-keystore.jks"
KEY_ALIAS="upload-key"

if [ ! -f "$KEYSTORE_PATH" ]; then
    echo "Step 1: Generating new keystore..."
    keytool -genkey -v \
        -keystore "$KEYSTORE_PATH" \
        -alias "$KEY_ALIAS" \
        -keyalg RSA \
        -keysize 2048 \
        -validity 10000 \
        -storepass android123 \
        -keypass android123 \
        -dname "CN=com.algoritmplus.app, OU=AlgoritmPlus, O=AlgoritmPlus, L=City, S=State, C=US"
    
    echo "✓ Keystore generated at: $KEYSTORE_PATH"
else
    echo "Step 1: Keystore already exists at: $KEYSTORE_PATH"
fi

echo ""
echo "Step 2: Getting certificate fingerprint..."
keytool -list -v -keystore "$KEYSTORE_PATH" -alias "$KEY_ALIAS" -storepass android123 | grep "SHA256:"

echo ""
echo "=== Next Steps ==="
echo "1. Use this keystore to sign your APK"
echo "2. Build the Android project with: npx expo prebuild --platform android"
echo "3. Build APK with: cd android && ./gradlew assembleRelease"
echo "4. Sign the APK with: apksigner sign --ks $KEYSTORE_PATH --ks-key-alias $KEY_ALIAS --ks-pass pass:android123 --key-pass pass:android123 <apk-file>"
echo ""
echo "Keystore Details:"
echo "  Path: $KEYSTORE_PATH"
echo "  Alias: $KEY_ALIAS"
echo "  Store Password: android123"
echo "  Key Password: android123"
