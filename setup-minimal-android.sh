#!/bin/bash

# Setup minimal Android project for ownership verification
# This creates a bare-minimum Android project with the required package name

set -e

PROJECT_DIR="./android-minimal"
APP_DIR="$PROJECT_DIR/app/src/main"

echo "=== Creating Minimal Android Project ==="

# Create directory structure
mkdir -p "$APP_DIR/assets"
mkdir -p "$APP_DIR/java/com/algoritmplus/app"

# Copy adi-registration.properties
if [ -f "./assets/adi-registration.properties" ]; then
    cp ./assets/adi-registration.properties "$APP_DIR/assets/"
    echo "✓ Copied adi-registration.properties"
else
    echo "✗ ERROR: assets/adi-registration.properties not found"
    exit 1
fi

# Create AndroidManifest.xml
cat > "$APP_DIR/AndroidManifest.xml" << 'EOF'
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

echo "✓ Created AndroidManifest.xml"

# Create MainActivity.java
cat > "$APP_DIR/java/com/algoritmplus/app/MainActivity.java" << 'EOF'
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

echo "✓ Created MainActivity.java"

# Create app-level build.gradle
cat > "$PROJECT_DIR/app/build.gradle" << 'EOF'
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

echo "✓ Created app/build.gradle"

# Create root build.gradle
cat > "$PROJECT_DIR/build.gradle" << 'EOF'
// Top-level build file
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

echo "✓ Created root build.gradle"

# Create gradle.properties
cat > "$PROJECT_DIR/gradle.properties" << 'EOF'
org.gradle.jvmargs=-Xmx2048m
android.useAndroidX=true
EOF

echo "✓ Created gradle.properties"

# Create settings.gradle
cat > "$PROJECT_DIR/settings.gradle" << 'EOF'
include ':app'
EOF

echo "✓ Created settings.gradle"

# Create Gradle wrapper
mkdir -p "$PROJECT_DIR/gradle/wrapper"
cat > "$PROJECT_DIR/gradle/wrapper/gradle-wrapper.properties" << 'EOF'
distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
distributionUrl=https\://services.gradle.org/distributions/gradle-8.2-bin.zip
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
EOF

echo "✓ Created Gradle wrapper properties"

echo ""
echo "=== Minimal Android Project Created ==="
echo "Location: $PROJECT_DIR"
echo ""
echo "Next Steps:"
echo "1. cd $PROJECT_DIR"
echo "2. ./gradlew assembleRelease"
echo "3. Sign the APK with your keystore"
echo "4. Upload to complete ownership verification"
