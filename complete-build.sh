#!/bin/bash

# Complete APK Build and Signing Script for Android Ownership Verification
# Package: com.algoritmplus.app
# Registration Token: CA2372QQOWWKCAAAAAAAAAAAAA

set -e

# Configuration
KEYSTORE_PATH="./android-keystore.jks"
KEY_ALIAS="upload-key"
STORE_PASSWORD="android123"
KEY_PASSWORD="android123"
OUTPUT_DIR="./signed-apk"
ANDROID_DIR="./android-minimal"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}==================================================${NC}"
echo -e "${GREEN}  Android Ownership Verification - APK Builder    ${NC}"
echo -e "${GREEN}==================================================${NC}"
echo ""
echo "Package: com.algoritmplus.app"
echo "Registration Token: CA2372QQOWWKCAAAAAAAAAAAAA"
echo ""

# Step 1: Verify registration properties
echo -e "${YELLOW}Step 1: Verifying registration properties...${NC}"
if [ ! -f "./assets/adi-registration.properties" ]; then
    echo -e "${RED}✗ ERROR: assets/adi-registration.properties not found!${NC}"
    echo "Creating it now with your registration token..."
    cat > ./assets/adi-registration.properties << 'EOF'
# Android Device Integration Registration Properties
registration_token=CA2372QQOWWKCAAAAAAAAAAAAA
EOF
    echo "✓ Created assets/adi-registration.properties"
else
    echo -e "${GREEN}✓ Found assets/adi-registration.properties${NC}"
fi

# Step 2: Generate keystore
echo ""
echo -e "${YELLOW}Step 2: Setting up signing keystore...${NC}"
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
    
    echo -e "${GREEN}✓ Keystore generated${NC}"
else
    echo -e "${GREEN}✓ Keystore already exists${NC}"
fi

# Display certificate info
echo ""
echo "Certificate Fingerprint (SHA256):"
keytool -list -v -keystore "$KEYSTORE_PATH" -alias "$KEY_ALIAS" -storepass "$STORE_PASSWORD" 2>/dev/null | grep "SHA256:" | head -1 | sed 's/.*SHA256: /  /'

# Step 3: Create minimal Android project
echo ""
echo -e "${YELLOW}Step 3: Creating minimal Android project...${NC}"

# Clean previous build
if [ -d "$ANDROID_DIR" ]; then
    rm -rf "$ANDROID_DIR"
fi

# Create directory structure
mkdir -p "$ANDROID_DIR/app/src/main/assets"
mkdir -p "$ANDROID_DIR/app/src/main/java/com/algoritmplus/app"

# Copy adi-registration.properties
cp ./assets/adi-registration.properties "$ANDROID_DIR/app/src/main/assets/"
echo "✓ Created assets directory with registration file"

# Create AndroidManifest.xml
cat > "$ANDROID_DIR/app/src/main/AndroidManifest.xml" << 'EOF'
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.algoritmplus.app">

    <application
        android:allowBackup="true"
        android:label="AlgoritmPlus"
        android:theme="@android:style/Theme.Material.Light">
        <activity
            android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>

</manifest>
EOF

# Create MainActivity.java
cat > "$ANDROID_DIR/app/src/main/java/com/algoritmplus/app/MainActivity.java" << 'EOF'
package com.algoritmplus.app;

import android.app.Activity;
import android.os.Bundle;

public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
    }
}
EOF

# Create build.gradle files
cat > "$ANDROID_DIR/app/build.gradle" << 'EOF'
plugins {
    id 'com.android.application'
}

android {
    namespace 'com.algoritmplus.app'
    compileSdk 34

    defaultConfig {
        applicationId "com.algoritmplus.app"
        minSdk 24
        targetSdk 34
        versionCode 1
        versionName "1.0"
    }

    buildTypes {
        release {
            minifyEnabled false
        }
    }

    compileOptions {
        sourceCompatibility JavaVersion.VERSION_1_8
        targetCompatibility JavaVersion.VERSION_1_8
    }
}

dependencies {
}
EOF

cat > "$ANDROID_DIR/build.gradle" << 'EOF'
buildscript {
    repositories {
        google()
        mavenCentral()
    }
    dependencies {
        classpath 'com.android.tools.build:gradle:8.2.0'
    }
}

allprojects {
    repositories {
        google()
        mavenCentral()
    }
}
EOF

cat > "$ANDROID_DIR/gradle.properties" << 'EOF'
org.gradle.jvmargs=-Xmx2048m
android.useAndroidX=true
EOF

cat > "$ANDROID_DIR/settings.gradle" << 'EOF'
include ':app'
EOF

mkdir -p "$ANDROID_DIR/gradle/wrapper"
cat > "$ANDROID_DIR/gradle/wrapper/gradle-wrapper.properties" << 'EOF'
distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
distributionUrl=https\://services.gradle.org/distributions/gradle-8.2-bin.zip
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
EOF

echo -e "${GREEN}✓ Minimal Android project created${NC}"

# Step 4: Check for Android SDK
echo ""
echo -e "${YELLOW}Step 4: Checking Android SDK...${NC}"
if [ -z "$ANDROID_HOME" ] && [ -z "$ANDROID_SDK_ROOT" ]; then
    # Try to find Android SDK
    if [ -d "$HOME/Library/Android/sdk" ]; then
        export ANDROID_HOME="$HOME/Library/Android/sdk"
        echo -e "${GREEN}✓ Found Android SDK at: $ANDROID_HOME${NC}"
    elif [ -d "$HOME/Android/Sdk" ]; then
        export ANDROID_HOME="$HOME/Android/Sdk"
        echo -e "${GREEN}✓ Found Android SDK at: $ANDROID_HOME${NC}"
    else
        echo -e "${RED}⚠ Android SDK not found!${NC}"
        echo ""
        echo "You need to install Android SDK first."
        echo "Options:"
        echo "  1. Install Android Studio (recommended)"
        echo "  2. Install command-line tools only"
        echo ""
        echo "For macOS with Homebrew:"
        echo "  brew install --cask android-studio"
        echo ""
        echo "After installation, run this script again."
        echo ""
        echo "=========================================="
        echo "ALTERNATIVE: Use Expo/EAS Build"
        echo "=========================================="
        echo ""
        echo "If you don't want to install Android SDK:"
        echo "  1. Run: npx expo install eas-cli"
        echo "  2. Run: eas build --platform android --profile preview"
        echo "  3. Download the APK when build completes"
        echo "  4. Sign it manually with:"
        echo "     apksigner sign --ks $KEYSTORE_PATH --ks-key-alias $KEY_ALIAS \\"
        echo "       --ks-pass pass:$STORE_PASSWORD --key-pass pass:$KEY_PASSWORD \\"
        echo "       --out signed-apk/algoritmplus-signed.apk <downloaded-apk>"
        echo ""
        exit 1
    fi
fi

export PATH="$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$ANDROID_HOME/tools:$ANDROID_HOME/tools/bin:$PATH"

# Check for required tools
if ! command -v sdkmanager &> /dev/null; then
    echo -e "${RED}⚠ sdkmanager not found. Please install Android SDK command-line tools.${NC}"
    echo ""
    echo "Install with:"
    echo "  sdkmanager \"platform-tools\" \"platforms;android-34\" \"build-tools;34.0.0\""
    echo ""
    exit 1
fi

# Install required SDK components if needed
echo "Checking required SDK components..."
REQUIRED_COMPONENTS=("platform-tools" "platforms;android-34" "build-tools;34.0.0")
for component in "${REQUIRED_COMPONENTS[@]}"; do
    if [ ! -d "$ANDROID_HOME/$component" ] && [ ! -d "$ANDROID_HOME/${component/;/-}" ]; then
        echo "Installing: $component"
        sdkmanager "$component" --sdk_root="$ANDROID_HOME" 2>/dev/null || true
    fi
done

echo -e "${GREEN}✓ Android SDK ready${NC}"

# Step 5: Build APK
echo ""
echo -e "${YELLOW}Step 5: Building APK...${NC}"

cd "$ANDROID_DIR"

# Create gradlew if it doesn't exist
if [ ! -f "./gradlew" ]; then
    echo "Downloading Gradle wrapper..."
    curl -sL https://services.gradle.org/distributions/gradle-8.2-bin.zip -o gradle.zip
    unzip -q gradle.zip
    cp gradle-8.2/lib/gradle-launcher-*.jar gradle-wrapper.jar 2>/dev/null || true
    rm -rf gradle.zip gradle-8.2
    
    # Use system gradle to generate wrapper
    if command -v gradle &> /dev/null; then
        gradle wrapper --gradle-version 8.2 2>/dev/null || true
    fi
fi

# Try to build
if [ -f "./gradlew" ]; then
    chmod +x ./gradlew
    ./gradlew assembleRelease 2>&1 | tail -20
else
    echo "Using system gradle..."
    gradle assembleRelease 2>&1 | tail -20
fi

cd ..

# Find the APK
UNSIGNED_APK=$(find "$ANDROID_DIR/app/build/outputs/apk/release" -name "*.apk" 2>/dev/null | head -1)

if [ -z "$UNSIGNED_APK" ]; then
    echo -e "${RED}✗ ERROR: APK build failed. Check the errors above.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ APK built: $UNSIGNED_APK${NC}"

# Step 6: Sign the APK
echo ""
echo -e "${YELLOW}Step 6: Signing APK...${NC}"
mkdir -p "$OUTPUT_DIR"

SIGNED_APK="$OUTPUT_DIR/algoritmplus-signed.apk"

# Find apksigner
if [ -n "$ANDROID_HOME" ]; then
    APKSIGNER=$(find "$ANDROID_HOME/build-tools" -name "apksigner" 2>/dev/null | head -1)
fi

if [ -n "$APKSIGNER" ] && [ -f "$APKSIGNER" ]; then
    echo "Using apksigner from: $APKSIGNER"
    "$APKSIGNER" sign \
        --ks "$KEYSTORE_PATH" \
        --ks-key-alias "$KEY_ALIAS" \
        --ks-pass "pass:$STORE_PASSWORD" \
        --key-pass "pass:$KEY_PASSWORD" \
        --out "$SIGNED_APK" \
        "$UNSIGNED_APK"
    echo -e "${GREEN}✓ APK signed successfully${NC}"
elif command -v apksigner &> /dev/null; then
    apksigner sign \
        --ks "$KEYSTORE_PATH" \
        --ks-key-alias "$KEY_ALIAS" \
        --ks-pass "pass:$STORE_PASSWORD" \
        --key-pass "pass:$KEY_PASSWORD" \
        --out "$SIGNED_APK" \
        "$UNSIGNED_APK"
    echo -e "${GREEN}✓ APK signed successfully${NC}"
else
    echo -e "${YELLOW}apksigner not found, using jarsigner...${NC}"
    cp "$UNSIGNED_APK" "$SIGNED_APK"
    jarsigner \
        -verbose \
        -keystore "$KEYSTORE_PATH" \
        -storepass "$STORE_PASSWORD" \
        -keypass "$KEY_PASSWORD" \
        "$SIGNED_APK" \
        "$KEY_ALIAS"
    echo -e "${GREEN}✓ APK signed with jarsigner${NC}"
fi

# Step 7: Verify signature
echo ""
echo -e "${YELLOW}Step 7: Verifying APK signature...${NC}"
if [ -n "$APKSIGNER" ] && [ -f "$APKSIGNER" ]; then
    "$APKSIGNER" verify --verbose "$SIGNED_APK" 2>&1 || true
elif command -v apksigner &> /dev/null; then
    apksigner verify --verbose "$SIGNED_APK" 2>&1 || true
else
    jarsigner -verify -verbose -certs "$SIGNED_APK" 2>&1 | head -10 || true
fi

# Step 8: Display final information
echo ""
echo -e "${GREEN}==================================================${NC}"
echo -e "${GREEN}  Build Complete!                                 ${NC}"
echo -e "${GREEN}==================================================${NC}"
echo ""
echo "Signed APK: ${GREEN}$SIGNED_APK${NC}"
echo ""
echo "Package: com.algoritmplus.app"
echo ""
echo "Keystore Details:"
echo "  Path: $KEYSTORE_PATH"
echo "  Alias: $KEY_ALIAS"
echo "  Store Password: $STORE_PASSWORD"
echo "  Key Password: $KEY_PASSWORD"
echo ""
echo "SHA256 Certificate Fingerprint:"
keytool -list -v -keystore "$KEYSTORE_PATH" -alias "$KEY_ALIAS" -storepass "$STORE_PASSWORD" 2>/dev/null | grep "SHA256:" | head -1 | sed 's/.*SHA256: /  /'
echo ""
echo -e "${YELLOW}=========================================${NC}"
echo -e "${YELLOW}  Next Steps:                           ${NC}"
echo -e "${YELLOW}=========================================${NC}"
echo ""
echo "1. Upload the signed APK to complete ownership verification:"
echo "   - Go to Google Play Console"
echo "   - Navigate to app ownership verification"
echo "   - Upload: $SIGNED_APK"
echo ""
echo "2. Save your keystore securely!"
echo "   You will need it for all future app updates."
echo ""
echo "3. Keep these credentials safe:"
echo "   - Keystore file: $KEYSTORE_PATH"
echo "   - Alias: $KEY_ALIAS"
echo "   - Passwords: $STORE_PASSWORD / $KEY_PASSWORD"
echo ""
