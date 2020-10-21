#!/bin/sh
python3 setup.py py2app
rm -rf dist/flux.app/Contents/Resources/lib/python3.8/PyQt5/Qt/lib/Qt{WebEngine,Designer,Quick}*
rm -rf dist/Flux.app/Contents/Resources/lib/python3.8/PyQt5/Qt/qml/
codesign -s "Developer ID Application: Simon Cozens (GHYRZM4TBD)" -v --deep --timestamp --entitlements entitlements.plist -o runtime `find dist/Flux.app -name '*.so' -or -name '*.dylib'` `find . -type f | grep 'framework/Versions/5/'`
codesign -s "Developer ID Application: Simon Cozens (GHYRZM4TBD)" -v --deep --timestamp --entitlements entitlements.plist -o runtime dist/Flux.app
ditto -c -k --keepParent "dist/Flux.app" dist/Flux.zip
xcrun altool --notarize-app -t osx -f dist/Flux.zip \
    --primary-bundle-id uk.co.corvelsoftware.flux -u simon@simon-cozens.org --password "@keychain:AC_PASSWORD" --asc-provider GHYRZM4TBD
# Later
# xcrun stapler staple "dist/Flux.app"
# spctl --assess --type execute -vvv "dist/Flux.app"
# rm dist/Flux.zip
# ditto -c -k --keepParent "dist/Flux.app" dist/Flux.zip
