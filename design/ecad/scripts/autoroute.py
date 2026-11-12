"""Route the Rev0.5 board with Freerouting and keep the session (issue #6 P4; CLAUDE.md 5.3).

Run with KiCad's own Python from the repository root:

    "<KiCad 9.0>/bin/python.exe" -I -B design/ecad/scripts/autoroute.py --java <java.exe> --jar <freerouting-2.5.0.jar>

1. make_pcb.py --dsn writes the router input: the placed board with the In1 plane, the
   hand-drawn tracks and the GND fanout of ROUTING_Rev0.5.md, and its router classes and
   keepouts.
2. Freerouting routes it, headless, with the optimizer off (in every trial on this board it
   made the result worse) and the net class USB_HS ignored (the pairs are drawn by hand).
3. The session as the router wrote it goes to design/ecad/routing/usb-power-hub.ses, and
   routing/autoroute.json records the SHA-256 of the router input, of the session, of the jar
   and of the Java runtime, the arguments and the router's own count of what it left unrouted.
Then make_pcb.py builds the board and imports the session; it refuses a session whose router
input differs from the one it computes.

The jar and the runtime are pinned (JAR_SHA256, JAVA_SHA256): another build routes
differently, so a different file is refused. They are not in the repository; the user's copies
are named on the command line.

What it CANNOT see: whether the routing is good. The router's own unrouted count is reported,
but check_routing.py (DRC, the pairs, the Kelvin taps, the analog layer rule, the port path's
copper) is what decides.
The router counts what it leaves unrouted differently from DRC (on this board 18 against DRC's
2), so its count is recorded, not judged: make_pcb.py applies the routing document's patch
table after the session, and check_routing.py's DRC decides.
Exit status: 0 = the session is written; 1 = the router failed and no session was written.
"""
import argparse
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / "design" / "ecad" / "routing"
SESSION = OUT / "usb-power-hub.ses"
RECORD = OUT / "autoroute.json"
JAR_SHA256 = "f6f51bb02245e8e717f9359bd260cc9c5c0b1bc0acc8b7cb2cd5b8ffeb5de3c7"    # freerouting-2.5.0.jar
JAVA_SHA256 = "f961fb8db73c7c546821bc6d30fdaa8ce2458da460a5e75e2c39189cd107e6ba"   # Temurin 25.0.5+8 JRE java.exe
ROUTER_ARGS = ["--gui.enabled=false", "--router.optimizer.enabled=false",
               "--router.autorouter.ignore_net_classes=USB_HS",
               # the router still necks a wire down where it enters a pin with neck-down off
               # (0.10-0.12 mm seen on this board); neck_width_um holds such a neck at the
               # board's 0.15 mm minimum (make_project.py), so DRC's track width rule holds
               "--router.automatic_neckdown=false", "--router.neck_width_um=150",
               # no analytics, and no log file in the user's profile: the log is captured here
               "--usage_and_diagnostic_data.disable_analytics=true", "--logging.file.enabled=false"]
DONE_RE = re.compile(r"Auto-routing stage completed:.*\((\d+) unrouted and (\d+) violations\)")
PASS_RE = re.compile(r"Auto-routing pass #(\d+) .*\((\d+) unrouted and (\d+) violations\)")


def sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def main(argv):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--java", required=True, type=pathlib.Path)
    ap.add_argument("--jar", required=True, type=pathlib.Path)
    ap.add_argument("--passes", type=int, default=60, help="the router's pass limit (default 60)")
    ap.add_argument("--timeout", type=int, default=5400, help="seconds before the router is stopped")
    a = ap.parse_args(argv[1:])
    for path, want in ((a.jar, JAR_SHA256), (a.java, JAVA_SHA256)):
        if not path.exists() or sha256(path) != want:
            raise SystemExit(f"{path}: not the pinned file (SHA-256 {want[:12]}...)")
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        dsn, ses, log = tmp / "router.dsn", tmp / "router.ses", tmp / "router.log"
        r = subprocess.run([sys.executable, "-I", "-B", str(HERE / "make_pcb.py"), "--dsn", str(dsn)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        m = re.search(r"router input ([0-9a-f]{64})", r.stdout)
        if r.returncode or m is None:
            raise SystemExit(f"make_pcb.py --dsn failed (exit {r.returncode}): {(r.stdout + r.stderr)[-600:]}")
        digest = m.group(1)
        args = ROUTER_ARGS + [f"--router.autorouter.max_passes={a.passes}"]
        # the JVM's NIO selector binds an AF_UNIX socket under its temp directory; under the
        # user's %TEMP% on this box that bind fails (~/.claude/notes/jvm-loopback-windows.md)
        unix_tmp = pathlib.Path(os.environ.get("SystemRoot", r"C:\Windows")) / "Temp"
        # the router runs in the temporary directory (below), so its two paths are made absolute
        cmd = [str(a.java.resolve()), f"-Djdk.net.unixdomain.tmpdir={unix_tmp}", "-jar", str(a.jar.resolve()),
               "-de", str(dsn), "-do", str(ses), "-l", "en", *args]
        print(f"routing {digest[:12]} with {a.jar.name}, at most {a.passes} passes")
        sys.stdout.flush()
        with log.open("w", encoding="utf-8") as f:
            try:
                # Freerouting creates an empty "en/" folder in its working directory: the
                # temporary one, so that none is left in the repository (issue #8)
                rc = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, timeout=a.timeout,
                                    cwd=tmp).returncode
            except subprocess.TimeoutExpired:
                raise SystemExit(f"the router ran past {a.timeout} s and was stopped; no session")
        text = log.read_text(encoding="utf-8", errors="replace")
        passes = [tuple(map(int, p)) for p in PASS_RE.findall(text)]
        done = DONE_RE.search(text)
        if rc or not ses.exists() or done is None:
            raise SystemExit(f"the router failed (exit {rc}); no session. Log tail: {text[-800:]}")
        unrouted, violations = map(int, done.groups())
        OUT.mkdir(exist_ok=True)
        data = ses.read_bytes()
        SESSION.write_bytes(data)
    record = {
        "dsn_sha256": digest,
        "ses_sha256": hashlib.sha256(data).hexdigest(),
        "jar": a.jar.name, "jar_sha256": JAR_SHA256, "java_sha256": JAVA_SHA256,
        "args": args,
        "passes": len(passes),
        "router_unrouted": unrouted,
        "router_violations": violations,
        "note": "router_violations is the router's own count, fixed items included; DRC decides",
    }
    RECORD.write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {SESSION.relative_to(ROOT).as_posix()} and {RECORD.name}: {len(passes)} passes,"
          f" {unrouted} unrouted by the router's count")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
