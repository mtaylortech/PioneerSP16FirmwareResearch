#!/usr/bin/env python3
"""SP-16 partial board emulator (firmware 1.50) — consolidated reference tool.

Boots Pioneer's ORIGINAL, UNMODIFIED 1.50 Linux kernel under STOCK QEMU
(machine `sabrelite`, an i.MX6Q reference board), installs the original root
filesystem onto a synthetic SD disk using the firmware's own guest tools, then
boots that disk through the stock init scripts and launches the sampler app.

Expected result (reproduced in the research, ~65-77 s per boot): original
switch_root, rootfs services, apl_start and application launch, then a stop at
a known checkpoint: missing AK4458 audio device, application SIGSEGV, missing
/dev/mtd12. This is NOT a working instrument: no usable UI, no audio, no NAND,
no bootloader. See README.md and ../../DISCLAIMER.md.

The kernel bytes are never changed. Three interventions are made through
QEMU's GDB stub (they are valid ONLY for the 1.50 kernel pinned below):
  1. backlight init call at 0x800089a8: skipped (PC+4, r0=0)
  2. gpu_init at 0x8002394c: returns -ENODEV without running
  3. SRC_SBMR1 (0x020d8004) set to 0x60 so the stock helper reports MMC boot
     (control/cold boots only)

Consolidated from the original research scripts (persistent-boot-update,
original-rootfs-control and arm-drawing-retention studies, October 2026); this
encodes the FINAL working recipe from those studies (the "builder3" disk layout
and udev alias rule). Differences from the research scripts are listed in
README.md.

Subcommands:  check | build-disk | install-rootfs | control NAME | cold NAME --from NAME2 | report NAME
License: MIT (see repository LICENSE). No firmware or key is included.
"""
import argparse, hashlib, json, os, shutil, signal, socket, struct, subprocess, sys, time, zlib
from pathlib import Path

# --- Pinned firmware 1.50 identities (from the research) -----------------------
KERNEL_SHA256 = "f9a5931feb0bf11b3e64b74e2a874b5cf58f0927204e890273f5e8def2a3566b"  # images/uImage, 1.50
ASSETS = {  # images/<name> inside the decrypted 1.50 ISO
    "rootfs1.tar.gz": "883f94e4a211c7fd3ed919c9a12545c006ef39eab5b832545c5b86670b95b677",
    "rootfs2.tar.gz": "58296e94103cf42d999ca6ca6916c7d76d9f49d4d1730d826499f685a572b1e5",
    "rootfs3.tar.gz": "71abd67b9e952387084756ddfeac1ce4fd9f60bdf483e6f31e1d096b6fe8bb29",
    "rootfs4.tar.gz": "25b754fa042a3dd9ba5c4fe567fadaaccd63068ff84e71096d7e847e023e160e",
    "pdj.tar.gz":     "2fa7cdca7f86ec28a0002d51033989d51507d83d3c70333f5adab7e972f2654e",
    "lib.sfs":        "ff1ce0822c38193890928b890a4bc023970dcd6e2fe3e5c765bc984879edbfa9",
    "bin.sfs":        "55e650753dc31539b12325ed55f7ab97722d7a2059f4f98e5aea40b42f361bc0",
    "share.sfs":      "1622ac26bb402e369c336761d3586cb862921f100c70f2db596c2309f3523069",
}
BACKLIGHT_CALL = 0x800089a8
GPU_INIT = 0x8002394c
SRC_SBMR1 = 0x020d8004

# --- Synthetic disk layout (final research recipe) -----------------------------
MIB = 1024 * 1024
DISK_BYTES = 512 * MIB
P1_START, P1_SECTORS = 2048, 32768          # FAT16 "internal" at 1 MiB, 16 MiB
P2_START, P2_SECTORS = 34816, 1013760       # ext4 rootfs at 17 MiB, 495 MiB
ENV_OFFSET, ENV_SIZE = 0xC0000, 0x2000      # U-Boot env record: CRC32 + payload
ENV_FIELDS = {  # constructed values, NOT a snapshot of any real unit
    "rootfs": "sd", "mmcdev": "/dev/mmcblk1p1", "ubifs_formatted": "true",
    "ubifs_data_update": "false", "usb_versionup": "off", "kernel_bank": "A",
    "boot_type": "normal", "update_status": "success", "aplstart": "on",
    "netdev": "lo", "ipaddr": "127.0.0.1", "netmask": "255.0.0.0", "release": "VM-ONLY",
}

BUILD_DONE = "VM-ONLY ORIGINAL PACKAGE SD BASELINE CONSTRUCTION COMPLETE"
CHECKPOINT = "Listening on port 2345"
MARKERS = {  # strings looked for in the guest serial log after a control/cold boot
    "original_MMC_bootmode": "BOOTMODE=MMC",
    "switch_root": "### switch_root ###",
    "rootfs_services": "Starting the hotplug events dispatcher udevd",
    "apl_start": "#### apl_start script ###",
    "application_launch": "#### Application Start!! ###",
    "missing_audio": "No such device (-19)",
    "app_SIGSEGV": "received SIGSEGV",
    "missing_mtd12": "ERROR:not exist device file dev=/dev/mtd12",
    "checkpoint": CHECKPOINT,
}

# Runs inside the guest during install-rootfs (original busybox/mkfs/tar/squashfs).
VM_BUILD = r'''#!/bin/sh
set -e
export PATH=/bin:/sbin:/usr/bin:/usr/sbin
echo 'VM-ONLY baseline builder entered'
mount -t proc proc /proc
mount -t sysfs sys /sys
ln -s /proc/mounts /etc/mtab
mkdir -p /vm/staging /vm/library /vm/rootfs
for i in 1 2 3 4; do tar xzf /vm/rootfs$i.tar.gz -C /vm/staging; done
mount -t squashfs -o loop /vm/lib.sfs /vm/library
export LD_LIBRARY_PATH=/vm/staging/lib:/vm/library
dev=`cat /sys/class/block/mmcblk0p2/dev`
major=${dev%:*}
minor=${dev#*:}
mknod /dev/mmcblk0p2 b "$major" "$minor"
echo "VM-ONLY actual kernel partition node mmcblk0p2=$dev"
n=0
while [ ! -e /dev/mmcblk0p2 ]; do
 n=$((n+1)); [ $n -lt 20 ]; sleep 1
done
/vm/staging/sbin/mkfs.ext4 -F /dev/mmcblk0p2
mount -t ext4 /dev/mmcblk0p2 /vm/rootfs
for i in 1 2 3 4; do tar xzf /vm/rootfs$i.tar.gz -C /vm/rootfs; done
mkdir -p /vm/rootfs/root /vm/rootfs/usr/lib /vm/rootfs/usr/bin /vm/rootfs/usr/share
tar xzf /vm/pdj.tar.gz -C /vm/rootfs/root
cp -a /vm/library/. /vm/rootfs/usr/lib/
umount /vm/library
mount -t squashfs -o loop /vm/bin.sfs /vm/library
cp -a /vm/library/. /vm/rootfs/usr/bin/
umount /vm/library
mount -t squashfs -o loop /vm/share.sfs /vm/library
cp -a /vm/library/. /vm/rootfs/usr/share/
umount /vm/library
mkdir -p /vm/rootfs/root/data /vm/rootfs/proc /vm/rootfs/sys /vm/rootfs/tmp /vm/rootfs/media
mkdir -p /vm/rootfs/etc/udev/rules.d
printf '%s\n' 'KERNEL=="mmcblk0p2", SYMLINK+="mmcblk1p1"' 'KERNEL=="mmcblk0", SYMLINK+="mmcblk1"' > /vm/rootfs/etc/udev/rules.d/99-vm-storage.rules
ln -s mmcblk0p2 /vm/rootfs/dev/mmcblk1p1
ln -s mmcblk0 /vm/rootfs/dev/mmcblk1
sync
umount /vm/rootfs
echo 'VM-ONLY ORIGINAL PACKAGE SD BASELINE CONSTRUCTION COMPLETE'
while :; do sleep 60; done
'''

# Runs inside the guest before the stock /init on control/cold boots.
VM_BOOTSTRAP = r'''#!/bin/sh
export PATH=/bin:/sbin:/usr/bin:/usr/sbin
mount -n -t proc proc /proc
mount -n -t sysfs sys /sys
n=0
while [ ! -e /sys/class/block/mmcblk0p2/dev ]; do
 n=$((n+1)); [ $n -lt 20 ] || exit 2; sleep 1
done
ln -sf mmcblk0 /dev/mmcblk1
ln -sf mmcblk0p2 /dev/mmcblk1p1
dev=`cat /sys/class/block/mmcblk0p2/dev`
mknod /dev/mmcblk0p2 b "${dev%:*}" "${dev#*:}"
request=`fw_printenv -n usb_versionup`; result=$?
echo "VM-ONLY original reader: request=$request status=$result"
[ $result -eq 0 -a -n "$request" ] || exit 2
bootmod
for f in /sys/class/graphics/fb0/name /sys/class/graphics/fb0/virtual_size /sys/class/graphics/fb0/bits_per_pixel /sys/class/graphics/fb0/stride; do echo "VM-ONLY FRAME CONTRACT $f"; cat "$f"; done
echo "$request" > /usb_versionup
exec /init
'''


# --- helpers -----------------------------------------------------------------
def die(msg):
    sys.exit("error: " + msg)


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(MIB), b""):
            h.update(chunk)
    return h.hexdigest()


def load_config(path):
    cfg_path = Path(path).resolve()
    if not cfg_path.is_file():
        die(f"config not found: {cfg_path} (copy config.example.json to config.json and edit it)")
    cfg = json.loads(cfg_path.read_text())
    base = cfg_path.parent
    for key in ("qemu_binary", "images_dir", "work_dir"):
        if key not in cfg:
            die(f"config is missing '{key}'")
        cfg[key] = (base / os.path.expanduser(cfg[key])).resolve()
    cfg.setdefault("qemu_env", {})
    cfg.setdefault("boot_seconds", 300)
    return cfg


def cpio_member(name, data, mode, ino):
    """One 'newc' cpio member (no host mknod/mount needed)."""
    n = name.encode() + b"\0"
    fields = [ino, mode, 0, 0, 1, 0, len(data), 0, 0, 0, 0, len(n), 0]
    h = b"070701" + b"".join(f"{v:08x}".encode() for v in fields) + n
    h += bytes((-len(h)) % 4)
    return h + data + bytes((-len(data)) % 4)


def cpio_archive(members):
    out = b""
    for ino, (name, data, mode) in enumerate(members, 1):
        out += cpio_member(name, data, mode, ino)
    out += cpio_member("TRAILER!!!", b"", 0, len(members) + 1)
    return out + bytes((-len(out)) % 512)


def env_record(fields):
    payload = (b"\0".join(f"{k}={v}".encode() for k, v in fields.items()) + b"\0\0").ljust(ENV_SIZE - 4, b"\0")
    return struct.pack("<I", zlib.crc32(payload) & 0xFFFFFFFF) + payload


def mbr(parts):
    m = bytearray(512)
    for i, (ptype, start, count) in enumerate(parts):
        m[446 + 16 * i:462 + 16 * i] = struct.pack("<B3sB3sII", 0, b"\xfe\xff\xff", ptype, b"\xfe\xff\xff", start, count)
    m[510:512] = b"\x55\xaa"
    return bytes(m)


# --- GDB remote-serial-protocol client (QEMU gdbstub on a private Unix socket) --
class Gdb:
    def __init__(self, sock):
        self.s = sock

    def packet(self, cmd):
        data = cmd.encode()
        self.s.sendall(b"$" + data + b"#" + f"{sum(data) % 256:02x}".encode())
        while True:
            x = self.s.recv(1)
            if not x:
                raise EOFError("GDB disconnected")
            if x == b"$":
                break
        body = bytearray()
        while True:
            x = self.s.recv(1)
            if not x:
                raise EOFError("GDB EOF")
            if x == b"#":
                break
            body += x
        if int(self.s.recv(2), 16) != sum(body) % 256:
            raise IOError("GDB checksum mismatch")
        self.s.sendall(b"+")
        return body.decode()

    def ok(self, cmd):
        r = self.packet(cmd)
        if r != "OK":
            raise RuntimeError(f"GDB {cmd!r} -> {r!r}")

    def reg(self, n):
        return struct.unpack("<I", bytes.fromhex(self.packet(f"p{n:x}")))[0]


def le32hex(v):
    return struct.pack("<I", v & 0xFFFFFFFF).hex()


# --- the board run (shared by install-rootfs / control / cold) ----------------
def run_board(cfg, name, disk, initrd, append, stop_text, set_mmc_bootmode, extra=()):
    work = cfg["work_dir"]
    out = work / "logs" / name
    if out.exists():
        die(f"{out} already exists; pick a new run name")
    out.mkdir(parents=True)
    sockname = f"{name}.gdb.sock"            # relative: keeps the Unix path short (macOS limit)
    if (work / sockname).exists():
        die(f"stale socket {work / sockname}; remove it")
    kernel = cfg["images_dir"] / "uImage"
    argv = [str(cfg["qemu_binary"]), "-M", "sabrelite", "-smp", "1", "-m", "1G",
            "-display", "none", "-serial", "stdio", "-monitor", "none", "-parallel", "none",
            "-nic", "none", "-nodefaults", "-no-reboot",
            "-kernel", str(kernel), "-append", append,
            "-gdb", f"unix:{sockname},server=on,wait=off", "-S",
            "-d", "guest_errors,unimp", "-D", str(out / "mmio.log"),
            "-drive", f"if=none,id=sd,format=raw,file={disk}", "-device", "sd-card,drive=sd",
            "-initrd", str(initrd), *extra]
    env = os.environ.copy()
    env.update({k: str(v) for k, v in cfg["qemu_env"].items()})
    events, start = [], time.monotonic()

    def event(kind, **kv):
        events.append({"t": round(time.monotonic() - start, 3), "kind": kind, **kv})
        (out / "events.json").write_text(json.dumps(events, indent=2) + "\n")
        print(json.dumps(events[-1]), flush=True)

    (out / "command.json").write_text(json.dumps({"argv": argv, "env_overrides": cfg["qemu_env"]}, indent=2) + "\n")
    child, sock, checkpoint = None, None, "deadline"
    with (out / "serial.txt").open("wb") as so, (out / "stderr.txt").open("wb") as se:
        try:
            child = subprocess.Popen(argv, cwd=work, env=env, stdout=so, stderr=se)
            event("launch", pid=child.pid)
            deadline = time.monotonic() + 10
            while not (work / sockname).exists():
                if child.poll() is not None:
                    raise RuntimeError("QEMU exited before its GDB socket appeared; see stderr.txt")
                if time.monotonic() > deadline:
                    raise TimeoutError("GDB socket did not appear")
                time.sleep(0.05)
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(120)
            sock.connect(str(work / sockname))
            g = Gdb(sock)
            g.packet("?")
            g.ok(f"Z0,{BACKLIGHT_CALL:x},4")
            g.ok(f"Z0,{GPU_INIT:x},4")
            # 1. backlight call: skip it
            g.packet("c")
            pc = g.reg(15)
            if pc != BACKLIGHT_CALL:
                raise RuntimeError(f"expected stop at backlight call 0x{BACKLIGHT_CALL:x}, got 0x{pc:x}")
            g.ok(f"z0,{BACKLIGHT_CALL:x},4")
            g.ok(f"P0f={le32hex(BACKLIGHT_CALL + 4)}")
            g.ok(f"P00={le32hex(0)}")
            event("backlight_call_skipped", pc=hex(pc))
            # 2. gpu_init: return -ENODEV (-19) to the caller without running it
            g.packet("c")
            pc, lr = g.reg(15), g.reg(14)
            if pc != GPU_INIT:
                raise RuntimeError(f"expected stop at gpu_init 0x{GPU_INIT:x}, got 0x{pc:x}")
            g.ok(f"z0,{GPU_INIT:x},4")
            g.ok(f"P0f={le32hex(lr)}")
            g.ok(f"P00={le32hex(-19)}")
            event("gpu_init_returned_ENODEV", pc=hex(pc), lr=hex(lr))
            # 3. boot-mode register -> MMC (so the stock 'bootmod' helper selects the SD/MMC branch)
            if set_mmc_bootmode:
                g.ok("Qqemu.PhyMemMode:1")
                g.ok(f"M{SRC_SBMR1:x},4:{le32hex(0x60)}")
                after = g.packet(f"m{SRC_SBMR1:x},4")
                g.ok("Qqemu.PhyMemMode:0")
                if after != le32hex(0x60):
                    raise RuntimeError(f"SRC_SBMR1 readback {after}")
                event("SRC_SBMR1_set_MMC", readback=after)
            g.ok("D")
            sock.close()
            sock = None
            while time.monotonic() - start < cfg["boot_seconds"]:
                text = (out / "serial.txt").read_bytes().decode(errors="replace")
                if "Kernel panic" in text:
                    checkpoint = "kernel_panic"
                    break
                if stop_text in text:
                    checkpoint = stop_text
                    break
                if child.poll() is not None:
                    checkpoint = "qemu_exit"
                    break
                time.sleep(0.2)
            event("observation_end", checkpoint=checkpoint)
        finally:
            if sock:
                sock.close()
            if child is not None and child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait(timeout=2)
            if child is not None:
                event("qemu_stopped", exit=child.returncode)
            if (work / sockname).exists():
                (work / sockname).unlink()
    return checkpoint, out


# --- subcommands ---------------------------------------------------------------
def cmd_check(cfg, args):
    ok = True
    q = cfg["qemu_binary"]
    try:
        env = os.environ.copy(); env.update({k: str(v) for k, v in cfg["qemu_env"].items()})
        ver = subprocess.run([str(q), "--version"], capture_output=True, text=True, env=env, timeout=20).stdout.splitlines()[0]
        machines = subprocess.run([str(q), "-M", "help"], capture_output=True, text=True, env=env, timeout=20).stdout
        print(f"qemu      {ver}")
        if "sabrelite" not in machines:
            print("FAIL      this QEMU has no 'sabrelite' machine (build with --target-list=arm-softmmu)"); ok = False
    except Exception as e:
        print(f"FAIL      cannot run {q}: {e}"); ok = False
    k = cfg["images_dir"] / "uImage"
    if not k.is_file():
        print(f"FAIL      kernel missing: {k}"); ok = False
    elif sha256_file(k) != KERNEL_SHA256:
        print("FAIL      uImage is not the firmware 1.50 kernel; the GDB hook addresses are only valid for 1.50"); ok = False
    else:
        print("kernel    1.50 uImage OK")
    for n, want in ASSETS.items():
        p = cfg["images_dir"] / n
        if not p.is_file():
            print(f"FAIL      missing {p}"); ok = False
        elif sha256_file(p) != want:
            print(f"FAIL      {n} hash differs from firmware 1.50"); ok = False
        else:
            print(f"asset     {n} OK")
    try:
        import pyfatfs  # noqa: F401
        print("python    pyfatfs available")
    except ImportError:
        print("FAIL      python package 'pyfatfs' missing (pip install pyfatfs)"); ok = False
    print("READY" if ok else "NOT READY")
    return 0 if ok else 1


def cmd_build_disk(cfg, args):
    from pyfatfs.PyFat import PyFat
    work = cfg["work_dir"]; work.mkdir(parents=True, exist_ok=True)
    disk = work / "builder.raw"
    if disk.exists():
        die(f"{disk} exists; delete it to rebuild")
    with disk.open("xb") as f:
        f.truncate(DISK_BYTES)
        f.write(mbr([(0x0E, P1_START, P1_SECTORS), (0x83, P2_START, P2_SECTORS)]))
        f.seek(ENV_OFFSET)
        f.write(env_record(ENV_FIELDS))
    fat = work / "p1-fat16.tmp"
    with fat.open("xb") as f:
        f.truncate(P1_SECTORS * 512)
    pf = PyFat(); pf.mkfs(str(fat), PyFat.FAT_TYPE_FAT16, size=P1_SECTORS * 512, label="VM_ONLY_EMMC"); pf.close()
    with disk.open("r+b") as f:
        f.seek(P1_START * 512)
        f.write(fat.read_bytes())
    fat.unlink()
    members = [("vm", b"", 0o40755), ("vm_build", VM_BUILD.encode(), 0o100755)]
    for n in ASSETS:
        members.append((f"vm/{n}", (cfg["images_dir"] / n).read_bytes(), 0o100644))
    (work / "builder.cpio").write_bytes(cpio_archive(members))
    print(json.dumps({"disk": str(disk), "bytes": DISK_BYTES, "initrd": str(work / "builder.cpio")}))
    return 0


def cmd_install_rootfs(cfg, args):
    work = cfg["work_dir"]
    disk, initrd = work / "builder.raw", work / "builder.cpio"
    if not disk.is_file() or not initrd.is_file():
        die("run build-disk first")
    checkpoint, out = run_board(cfg, "install", disk, initrd,
                                "console=ttymxc0,115200 earlyprintk rdinit=/vm_build", BUILD_DONE, False,
                                extra=("-device", f"loader,addr=0x{SRC_SBMR1:x},data=0x60,data-len=4"))
    if checkpoint != BUILD_DONE:
        die(f"rootfs install did not finish (checkpoint={checkpoint}); see {out}/serial.txt")
    baseline = work / "baseline.raw"
    shutil.copyfile(disk, baseline); baseline.chmod(0o444)
    print(json.dumps({"baseline": str(baseline), "sha256": sha256_file(baseline)}))
    return 0


def boot_arm(cfg, name, disk):
    work = cfg["work_dir"]
    initrd = work / "states" / name / "bootstrap.cpio"
    initrd.write_bytes(cpio_archive([("vm_bootstrap", VM_BOOTSTRAP.encode(), 0o100755)]))
    checkpoint, out = run_board(cfg, name, disk, initrd,
                                "console=ttymxc0,115200 earlyprintk rdinit=/vm_bootstrap", CHECKPOINT, True,
                                extra=("-rtc", "base=2026-10-11T00:00:00,clock=vm"))
    return report(out)


def cmd_control(cfg, args):
    work = cfg["work_dir"]; base = work / "baseline.raw"
    if not base.is_file():
        die("run install-rootfs first")
    st = work / "states" / args.name
    st.mkdir(parents=True, exist_ok=False)
    disk = st / "internal.raw"
    shutil.copyfile(base, disk); disk.chmod(0o600)
    return boot_arm(cfg, args.name, disk)


def cmd_cold(cfg, args):
    work = cfg["work_dir"]
    src = work / "states" / args.from_ / "internal.raw"
    if not src.is_file():
        die(f"no retained disk {src}")
    (work / "states" / args.name).mkdir(parents=True, exist_ok=False)
    return boot_arm(cfg, args.name, src)   # same file: boots the retained state as-is


def report(out):
    text = (Path(out) / "serial.txt").read_bytes().decode(errors="replace")
    flags = {k: (v in text) for k, v in MARKERS.items()}
    for k, v in flags.items():
        print(f"{'yes' if v else ' no'}  {k}")
    reached = all(flags[k] for k in ("switch_root", "apl_start", "application_launch", "checkpoint"))
    print("REPRODUCED the research checkpoint" if reached else "did NOT reach the research checkpoint")
    (Path(out) / "markers.json").write_text(json.dumps(flags, indent=2) + "\n")
    return 0 if reached else 1


def cmd_report(cfg, args):
    return report(cfg["work_dir"] / "logs" / args.name)


def main():
    ap = argparse.ArgumentParser(description="SP-16 1.50 partial board emulator (stock QEMU sabrelite)")
    ap.add_argument("--config", default=str(Path(__file__).with_name("config.json")))
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    sub.add_parser("build-disk")
    sub.add_parser("install-rootfs")
    c = sub.add_parser("control"); c.add_argument("name")
    c = sub.add_parser("cold"); c.add_argument("name"); c.add_argument("--from", dest="from_", required=True)
    c = sub.add_parser("report"); c.add_argument("name")
    args = ap.parse_args()
    cfg = load_config(args.config)
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    fn = {"check": cmd_check, "build-disk": cmd_build_disk, "install-rootfs": cmd_install_rootfs,
          "control": cmd_control, "cold": cmd_cold, "report": cmd_report}[args.cmd]
    sys.exit(fn(cfg, args))


if __name__ == "__main__":
    main()
