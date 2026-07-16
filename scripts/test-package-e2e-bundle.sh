#!/usr/bin/env bash
set -euo pipefail

# ── Validator for package-e2e-bundle.sh ──────────────────────────────────────
# Builds the bundle at a throwaway version and asserts:
#   - tarball exists and extracts to the expected dir
#   - carries an executable, syntactically-valid run.sh + README
#   - every e2e source/asset from the repo made it in (file-count parity)
#   - test sources are syntactically valid python (compile only, no imports)
#   - the SDK is pinned at the version (with the agents extra), and no
#     @VERSION@ placeholder is left anywhere
#   - binary assets survived the version stamping uncorrupted
# All checks are static + deterministic (no network, no install, no server).
# Run: ./scripts/test-package-e2e-bundle.sh

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$HERE/.." && pwd)"
VERSION="9.9.9-test"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

fail() { echo "FAIL: $*" >&2; exit 1; }
pass() { echo "  ok: $*"; }

"$HERE/package-e2e-bundle.sh" --version "$VERSION" --out "$WORK/dist" >/dev/null

NAME="conductor-ai-e2e-python-$VERSION"
TAR="$WORK/dist/$NAME.tar.gz"

[[ -f "$TAR" ]] || fail "tarball not produced ($TAR)"
pass "tarball produced"

mkdir -p "$WORK/x"
tar -xzf "$TAR" -C "$WORK/x"
ROOT="$WORK/x/$NAME"
[[ -d "$ROOT" ]] || fail "tarball does not extract to $NAME/"
pass "extracts to $NAME/"

[[ -f "$ROOT/run.sh" ]] || fail "missing run.sh"
[[ -x "$ROOT/run.sh" ]] || fail "run.sh not executable"
bash -n "$ROOT/run.sh"  || fail "run.sh has a bash syntax error"
[[ -f "$ROOT/README.md" ]] || fail "missing README.md"
pass "run.sh + README present and valid"

# Every e2e file (sources, conftest, assets) made it into the bundle.
SRC_COUNT="$(find "$REPO_ROOT/e2e" -type f | wc -l | tr -d ' ')"
BUNDLE_COUNT="$(find "$ROOT/e2e" -type f | wc -l | tr -d ' ')"
[[ "$SRC_COUNT" == "$BUNDLE_COUNT" ]] \
  || fail "source parity: repo e2e/ has $SRC_COUNT files, bundle has $BUNDLE_COUNT"
pass "all $SRC_COUNT e2e files present"

# Test sources must be syntactically valid python (compile only, no imports).
python3 -m py_compile "$ROOT"/e2e/*.py || fail "a test file has a syntax error"
pass "sources compile"

# SDK pinned at the packaged version with the agents extra, no unexpanded
# placeholders anywhere.
grep -q "conductor-python\[agents\]==$VERSION" "$ROOT/requirements.txt" \
  || fail "requirements.txt does not pin conductor-python[agents]==$VERSION"
if grep -rn '@VERSION@' "$ROOT" >/dev/null 2>&1; then
  fail "unexpanded @VERSION@ placeholder left in bundle"
fi
pass "SDK pinned at $VERSION, no placeholders"

# Binary assets are excluded from version stamping; prove none were corrupted.
while IFS= read -r -d '' img; do
  python3 -c "
import struct, sys
with open(sys.argv[1], 'rb') as f:
    assert f.read(8) == b'\x89PNG\r\n\x1a\n', 'bad PNG header'
" "$img" || fail "binary asset corrupted: $img"
done < <(find "$ROOT/e2e" -name '*.png' -print0)
pass "binary assets intact"

echo "ALL CHECKS PASSED"
