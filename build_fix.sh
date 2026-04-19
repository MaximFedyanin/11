#!/bin/bash
# Build script with C compiler environment fix for NDK r25b

# Clean previous build artifacts
echo "Cleaning previous build..."
buildozer android clean

# Set explicit compiler environment variables for NDK r25b
export CC=$(find ~/.buildozer/android/platform/android-ndk-r25b/toolchains/llvm/prebuilt/linux-x86_64/bin -name "armv7a-linux-androideabi*-clang" | head -1)
export CXX=$(find ~/.buildozer/android/platform/android-ndk-r25b/toolchains/llvm/prebuilt/linux-x86_64/bin -name "armv7a-linux-androideabi*-clang++" | head -1)
export AR=$(find ~/.buildozer/android/platform/android-ndk-r25b/toolchains/llvm/prebuilt/linux-x86_64/bin -name "llvm-ar")
export RANLIB=$(find ~/.buildozer/android/platform/android-ndk-r25b/toolchains/llvm/prebuilt/linux-x86_64/bin -name "llvm-ranlib")
export STRIP=$(find ~/.buildozer/android/platform/android-ndk-r25b/toolchains/llvm/prebuilt/linux-x86_64/bin -name "llvm-strip")

echo "Using compiler: $CC"
echo "Using C++ compiler: $CXX"

# Build debug APK
echo "Building debug APK..."
buildozer android debug

echo "Build complete!"
