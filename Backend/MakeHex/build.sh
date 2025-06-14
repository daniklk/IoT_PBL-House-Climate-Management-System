#!/bin/bash
# Cross-compilation build script

echo "Cross-compiling encodeir for multiple platforms..."

# Create output directories
mkdir -p ../bin/{linux,windows,macos}

# Linux build (native)
echo "Building for Linux..."
g++ -std=c++11 -O2 -c EncodeIR.cpp -o EncodeIR_linux.o
g++ -std=c++11 -O2 -c IRP.cpp -o IRP_linux.o
g++ -std=c++11 -O2 -o ../bin/linux/encodeir EncodeIR_linux.o IRP_linux.o
strip ../bin/linux/encodeir
echo "✓ Linux build complete"

# Windows build (requires mingw-w64)
if command -v x86_64-w64-mingw32-g++ &> /dev/null; then
    echo "Building for Windows..."
    x86_64-w64-mingw32-g++ -std=c++11 -O2 -c EncodeIR.cpp -o EncodeIR_win.o
    x86_64-w64-mingw32-g++ -std=c++11 -O2 -c IRP.cpp -o IRP_win.o
    x86_64-w64-mingw32-g++ -std=c++11 -O2 -o ../bin/windows/encodeir.exe EncodeIR_win.o IRP_win.o -static
    x86_64-w64-mingw32-strip ../bin/windows/encodeir.exe
    echo "✓ Windows build complete"
else
    echo "⚠ mingw-w64 not found. Install with: sudo apt-get install mingw-w64"
fi

# macOS build (requires osxcross)
if command -v x86_64-apple-darwin20-clang++ &> /dev/null; then
    echo "Building for macOS..."
    x86_64-apple-darwin20-clang++ -std=c++11 -O2 -c EncodeIR.cpp -o EncodeIR_mac.o
    x86_64-apple-darwin20-clang++ -std=c++11 -O2 -c IRP.cpp -o IRP_mac.o
    x86_64-apple-darwin20-clang++ -std=c++11 -O2 -o ../bin/macos/encodeir EncodeIR_mac.o IRP_mac.o
    x86_64-apple-darwin20-strip ../bin/macos/encodeir
    echo "✓ macOS build complete"
else
    echo "⚠ OSXCross not found. macOS cross-compilation requires OSXCross setup"
fi

# Clean up object files
rm -f *.o

echo "Build complete! Binaries are in bin/ directory:"
ls -la ../bin/*/
