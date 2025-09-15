#/usr/bin/env bash
set -xe

cd "$(dirname "$0")"

# Download and install vips
basedir=$(python download-vips.py)

if [[ $RUNNER_OS == "Linux" ]]; then
  linkname="-l:libvips.so.42"
elif [[ $RUNNER_OS == "Windows" ]]; then
  # MSVC convention: import library is called "libvips.lib"
  linkname="-llibvips"
elif [[ $RUNNER_OS == "macOS" ]]; then
  # -l:<LIB> syntax is unavailable with ld on macOS
  ln -sf libvips.42.dylib $basedir/lib/libvips.dylib
  # Allow delocate to find libvips.42.dylib by using an absolute path instead of @loader_path
  install_name_tool -id "$basedir/lib/libvips.42.dylib" $basedir/lib/libvips.42.dylib
  linkname="-lvips"
fi

mkdir -p $basedir/lib/pkgconfig
cat > $basedir/lib/pkgconfig/vips.pc << EOL
prefix=\${pcfiledir}/../..
libdir=\${prefix}/lib
includedir=\${prefix}/include

Name: vips
Description: Image processing library
Version: 8.17.2
Requires:
Libs: -L\${libdir} ${linkname}
Cflags: -I\${includedir} -I\${includedir}/glib-2.0 -I\${libdir}/glib-2.0/include
EOL
