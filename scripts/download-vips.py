import glob
import os
import platform
import sysconfig
import sys
import shutil
import tarfile

from tempfile import mkstemp
from urllib.request import urlopen, Request
from urllib.error import HTTPError

# Must be kept in sync with `../pyproject.toml`
VIPS_VERSION = '8.16.0'
BASE_LOC = (
    'https://github.com/kleisauke/libvips-packaging/releases'
)
SUPPORTED_PLATFORMS = [
    'linux-aarch64',
    'linux-x86_64',
    'musllinux-aarch64',
    'musllinux-x86_64',
    'win-32',
    'win-amd64',
    # 'win-arm64',
    'macosx-arm64',
    'macosx-x86_64',
]
ARCH_REMAP = {
    '32': 'x86',
    'aarch64': 'arm64',
    'amd64': 'x64',
    'arm64': 'arm64',
    'x86_64': 'x64',
}


def get_plat():
    plat = sysconfig.get_platform()
    plat_split = plat.split("-")
    arch = plat_split[-1]
    if arch == "win32":
        plat = "win-32"
    elif arch in ["universal2", "intel"]:
        plat = f"macosx-{platform.uname().machine}"
    elif len(plat_split) > 2:
        plat = f"{plat_split[0]}-{arch}"
    assert plat in SUPPORTED_PLATFORMS, f'invalid platform {plat}'
    return plat


def get_manylinux(arch):
    return f'linux-{ARCH_REMAP[arch]}.tar.gz'


def get_musllinux(arch):
    return f'linux-musl-{ARCH_REMAP[arch]}.tar.gz'


def get_linux(arch):
    # best way of figuring out whether manylinux or musllinux is to look
    # at the packaging tags. If packaging isn't installed (it's not by default)
    # fallback to sysconfig (which may be flakier)
    try:
        from packaging.tags import sys_tags
        tags = list(sys_tags())
        plat = tags[0].platform
    except ImportError:
        # fallback to sysconfig for figuring out if you're using musl
        plat = 'manylinux'
        # value could be None
        v = sysconfig.get_config_var('HOST_GNU_TYPE') or ''
        if 'musl' in v:
            plat = 'musllinux'

    if 'manylinux' in plat:
        return get_manylinux(arch)
    elif 'musllinux' in plat:
        return get_musllinux(arch)


def get_macosx(arch):
    return f'osx-{ARCH_REMAP[arch]}.tar.gz'


def get_win32(arch):
    return f'win-{ARCH_REMAP[arch]}.tar.gz'


def download_vips(target, plat):
    osname, arch = plat.split("-")
    headers = {'User-Agent':
               ('Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 ; '
                '(KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3')}
    suffix = None
    typ = 'tar.gz'
    if osname == "linux":
        suffix = get_linux(arch)
    elif osname == "musllinux":
        suffix = get_musllinux(arch)
    elif osname == 'macosx':
        suffix = get_macosx(arch)
    elif osname == 'win':
        suffix = get_win32(arch)

    if not suffix:
        return None

    filename = (
        f'{BASE_LOC}/download/v{VIPS_VERSION}/'
        f'libvips-{VIPS_VERSION}-{suffix}'
    )
    print(f'Attempting to download {filename}', file=sys.stderr)
    req = Request(url=filename, headers=headers)
    try:
        response = urlopen(req)
    except HTTPError:
        print(f'Could not download "{filename}"', file=sys.stderr)
        raise
    # length = response.getheader('content-length')
    if response.status != 200:
        print(f'Could not download "{filename}"', file=sys.stderr)
        return None
    # print(f"Downloading {length} from {filename}", file=sys.stderr)
    data = response.read()
    # print("Saving to file", file=sys.stderr)
    with open(target, 'wb') as fid:
        fid.write(data)
    return typ


def setup_vips(plat=get_plat()):
    '''
    Download and setup a libvips library for building. If successful,
    the configuration script will find it automatically.

    Returns
    -------
    msg : str
        path to extracted files on success, otherwise indicates what went wrong
        To determine success, do ``os.path.exists(msg)``
    '''

    _, tmp = mkstemp()
    if not plat:
        raise ValueError('unknown platform')

    typ = download_vips(tmp, plat)
    if not typ:
        return ''
    if not typ == 'tar.gz':
        return 'expecting to download tar.gz, not %s' % str(typ)
    return unpack_targz(tmp)


def unpack_targz(fname):
    target = os.path.abspath(os.path.join('..', 'tmp'))
    if not os.path.exists(target):
        os.mkdir(target)
    with tarfile.open(fname, 'r') as zf:
        # Strip common prefix from paths when unpacking
        prefix = os.path.commonpath(zf.getnames())
        extract_tarfile_to(zf, target, prefix)
        return target


def extract_tarfile_to(tarfileobj, target_path, archive_path):
    """Extract TarFile contents under archive_path/ to target_path/"""

    def get_members():
        for member in tarfileobj.getmembers():
            if archive_path:
                norm_path = os.path.normpath(member.name)
                if norm_path.startswith(archive_path + os.path.sep):
                    member.name = norm_path[len(archive_path) + 1:]
                else:
                    continue

            dst_path = os.path.abspath(os.path.join(target_path, member.name))
            if os.path.commonpath([target_path, dst_path]) != target_path:
                # Path not under target_path, probably contains ../
                continue

            yield member

    tarfileobj.extractall(target_path, members=get_members())


def test_setup(plats):
    '''
    Make sure all the downloadable files needed for wheel building
    exist and can be opened
    '''

    errs = []
    for plat in plats:
        osname, _ = plat.split("-")
        if plat not in plats:
            continue
        target = None
        try:
            try:
                target = setup_vips(plat)
            except Exception as e:
                print(f'Could not setup {plat}')
                print(e)
                errs.append(e)
                continue
            if not target:
                raise RuntimeError(f'Could not setup {plat}')
            print('success with', plat)
            files = [glob.glob(os.path.join(target, "lib", e))
                     for e in ['*.so', '*.dll', '*.dylib']]
            if not files:
                raise RuntimeError("No files unpacked!")
        finally:
            if target:
                if os.path.isfile(target):
                    os.unlink(target)
                else:
                    shutil.rmtree(target)
    if errs:
        raise errs[0]


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Download and extract an libvips library for this '
                    'architecture')
    parser.add_argument('--test', nargs='*', default=None,
                        help='Test different architectures. "all", or any of '
                             f'{SUPPORTED_PLATFORMS}')
    args = parser.parse_args()
    if args.test is None:
        print(setup_vips())
    else:
        if len(args.test) == 0 or 'all' in args.test:
            test_setup(SUPPORTED_PLATFORMS)
        else:
            test_setup(args.test)
