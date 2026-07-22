#!/usr/bin/env bash
# check_corpus.sh — corpus integrity gate for the Northstar knowledge base.
# Asserts the corpus is complete (30 docs, expected per-category counts),
# every doc has frontmatter, and shared canonical facts appear where expected
# and are not contradicted. Exit 0 = intact; non-zero = a check failed.
set -uo pipefail

# Resolve repo root relative to this script so it runs from anywhere.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CORPUS="$ROOT/data/northstar"

fail=0
pass() { printf '  \033[32mok\033[0m   %s\n' "$1"; }
bad()  { printf '  \033[31mFAIL\033[0m %s\n' "$1"; fail=$((fail+1)); }

echo "Northstar corpus check — $CORPUS"
echo

# --- 1. per-category counts ---------------------------------------------------
# (bash 3.2 compatible — no associative arrays)
echo "[1] document counts"
expected_count() {
  case "$1" in
    product)      echo 7 ;;
    sales)        echo 10 ;;
    case-studies) echo 4 ;;
    marketing)    echo 5 ;;
    company)      echo 4 ;;
    *)            echo 0 ;;
  esac
}
total=0
for cat in product sales case-studies marketing company; do
  n=$(find "$CORPUS/$cat" -maxdepth 1 -name '*.md' 2>/dev/null | wc -l | tr -d ' ')
  exp=$(expected_count "$cat")
  total=$((total+n))
  if [ "$n" = "$exp" ]; then pass "$cat: $n"; else bad "$cat: expected $exp, found $n"; fi
done
# README at data/northstar/README.md is reference, not counted in the 30.
corpus_total=$(find "$CORPUS" -mindepth 2 -name '*.md' | wc -l | tr -d ' ')
if [ "$corpus_total" = "30" ]; then pass "total corpus docs: 30"; else bad "total corpus docs: expected 30, found $corpus_total"; fi
echo

# --- 2. every doc has frontmatter --------------------------------------------
echo "[2] frontmatter present"
missing_fm=0
while IFS= read -r f; do
  if [ "$(head -n1 "$f")" != "---" ]; then bad "no frontmatter: ${f#$ROOT/}"; missing_fm=$((missing_fm+1)); fi
done < <(find "$CORPUS" -mindepth 2 -name '*.md')
[ "$missing_fm" = "0" ] && pass "all 30 docs start with '---'"
echo

# --- 3. shared canonical facts present where expected ------------------------
echo "[3] canonical facts consistency"

# helper: assert a regex appears in a file
has() { grep -Eq "$2" "$CORPUS/$1" 2>/dev/null && pass "$3" || bad "$3 (missing in $1)"; }

# ICP bounds
has sales/icp-definition.md '200.?2000'            "ICP employee band 200-2000 in icp-definition"
has sales/icp-definition.md 'Series B'             "ICP Series B-D in icp-definition"
has sales/icp-definition.md '20M.*200M' "ICP ARR band \$20M-\$200M in icp-definition"

# Competitor set: one battlecard each, and all four named in positioning
for c in clari gong mosaic pigment; do
  [ -f "$CORPUS/sales/battlecard-$c.md" ] && pass "battlecard present: $c" || bad "battlecard missing: $c"
done
has sales/positioning.md 'Clari'   "competitor Clari in positioning"
has sales/positioning.md 'Gong'    "competitor Gong in positioning"
has sales/positioning.md 'Mosaic'  "competitor Mosaic in positioning"
has sales/positioning.md 'Pigment' "competitor Pigment in positioning"

# Pricing figures consistent across pricing + faq
has product/pricing.md '2,?500'  "Core \$2,500 in pricing"
has product/pricing.md '6,?000'  "Growth \$6,000 in pricing"
has sales/faq.md        '2,?500' "Core \$2,500 echoed in faq"
has sales/faq.md        '6,?000' "Growth \$6,000 echoed in faq"

# Locked metrics appear in positioning
has sales/positioning.md '90%\+'          "metric 90%+ accuracy in positioning"
has sales/positioning.md '6 hours.*30 min|six hours.*thirty' "metric 6h->30min in positioning"
has sales/positioning.md '4.?6 week'      "metric 4-6 week deploy in positioning"
has sales/positioning.md '12%'            "metric +12% quota in positioning"
echo

# --- 4. contradiction guard: no stray competitor / wrong price ---------------
echo "[4] contradiction guard"
# Flag common wrong-fact drift. These competitors are NOT ours.
stray=$(grep -rEl 'Salesforce Einstein Forecast|Aviso|BoostUp|Anaplan' "$CORPUS" 2>/dev/null | wc -l | tr -d ' ')
[ "$stray" = "0" ] && pass "no out-of-scope competitor names" || bad "found $stray docs naming out-of-scope competitors"
# Core price must not appear as a contradictory value.
badprice=$(grep -rEho 'Core[^.]*\$[0-9,]+/mo' "$CORPUS" 2>/dev/null | grep -Ev '2,?500' | wc -l | tr -d ' ')
[ "$badprice" = "0" ] && pass "no contradictory Core price" || bad "found $badprice contradictory Core price mentions"
echo

# --- verdict -----------------------------------------------------------------
if [ "$fail" = "0" ]; then
  printf '\033[32mCORPUS OK\033[0m — all checks passed (30 docs, frontmatter, facts consistent)\n'
  exit 0
else
  printf '\033[31mCORPUS CHECK FAILED\033[0m — %d check(s) failed\n' "$fail"
  exit 1
fi
