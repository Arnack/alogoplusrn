#!/bin/bash

# Monitor EAS Build Status
BUILD_ID="c79d5a17-64a0-4e24-ae6a-6358efa6f6d6"

echo "Monitoring EAS Build: $BUILD_ID"
echo "View online: https://expo.dev/accounts/utrom/projects/algoritmplus-mobile/builds/$BUILD_ID"
echo ""

while true; do
    STATUS=$(eas build:view $BUILD_ID --json 2>/dev/null | grep -o '"status":"[^"]*"' | head -1 | cut -d'"' -f4)
    
    if [ -z "$STATUS" ]; then
        STATUS=$(eas build:list --platform android --limit 1 --json 2>/dev/null | grep -o '"status":"[^"]*"' | head -1 | cut -d'"' -f4)
    fi
    
    echo "[$(date '+%H:%M:%S')] Status: $STATUS"
    
    if [ "$STATUS" = "finished" ]; then
        echo ""
        echo "✅ Build complete!"
        echo "Download APK from: https://expo.dev/accounts/utrom/projects/algoritmplus-mobile/builds/$BUILD_ID"
        echo ""
        echo "Then upload the APK to Google Play Console for ownership verification."
        break
    elif [ "$STATUS" = "errored" ] || [ "$STATUS" = "cancelled" ]; then
        echo "❌ Build failed with status: $STATUS"
        echo "Check logs: https://expo.dev/accounts/utrom/projects/algoritmplus-mobile/builds/$BUILD_ID"
        break
    fi
    
    sleep 60
done
