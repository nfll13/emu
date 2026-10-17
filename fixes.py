# fixes.py - source fixes applied by the workflow before the build.
# Upload a new version of this file to the repo root to change what gets fixed;
# the workflow file itself does not need to change.
import pathlib

SRC = pathlib.Path("gpl-source/qemu/src")


def patch_file(path, fn):
    s = path.read_text()
    s2 = fn(s)
    if s2 != s:
        path.write_text(s2)
        print("patched", path)
    else:
        print("already patched", path)


# ---- Fix 1 -----------------------------------------------------------------
# guest_tls.c handles reads of the ARM32 "kuser" TLS slot (0xffff0ff0) and calls
# cpu_get_tls(), which only exists for the 32-bit ARM target (link error on
# aarch64). AArch64 guests have no such slot, so on aarch64 the handler simply
# never handles anything and the guest gets a normal SIGSEGV.
def fix_tls(s):
    if "AEMU_FIX_TLS" in s:
        return s
    marker = '#include "guest_tls.h"\n'
    assert s.count(marker) == 1, "guest_tls.h include not found exactly once"
    stub = (
        marker
        + "\n/* AEMU_FIX_TLS: AArch64 has no legacy ARM32 TLS slot. */\n"
        + "#ifdef TARGET_AARCH64\n"
        + "bool guest_tls_fault(CPUState *cs, uint64_t addr, int is_load, uintptr_t ra)\n"
        + "{\n"
        + "    return false;\n"
        + "}\n"
        + "#else\n"
    )
    return s.replace(marker, stub) + "\n#endif /* TARGET_AARCH64 */\n"


patch_file(SRC / "guest_tls.c", fix_tls)
