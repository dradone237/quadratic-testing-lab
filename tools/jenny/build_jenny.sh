#!/bin/sh
# Compile Jenny avec GCC (Ubuntu / Linux, MSYS2, macOS).
# Usage : sh tools/jenny/build_jenny.sh
#   CC=clang sh tools/jenny/build_jenny.sh       autre compilateur
#   JENNY_RAW_SOURCE=1 sh tools/jenny/build_jenny.sh   compiler la source brute
#
# Portabilite : jenny.c (2003) declare « typedef unsigned long ub4; » ou ub4
# signifie « 4 octets ». Sous Linux 64 bits, unsigned long fait 8 octets : le
# generateur pseudo-aleatoire de Jenny change et les combinaisons different de
# celles de Windows (constate : 29 cas Pairwise au lieu de 28). Dans ce cas, le
# script compile une COPIE (tools/jenny/build/jenny_portable.c) ou seules les
# deux definitions ub4/sb4 passent sur 32 bits. La source officielle n'est pas
# modifiee ; son SHA-256 est verifie avant toute compilation.
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
EXPECTED=b93222086d8c5e778210f145b730547805662cbb207ace490a373eeb5f7dcb23
CC=${CC:-gcc}

if ! command -v "$CC" >/dev/null 2>&1; then
    echo "Compilateur $CC introuvable. Ubuntu : sudo apt install -y gcc" >&2
    exit 1
fi

ACTUAL=$(sha256sum "$HERE/src/jenny.c" | cut -d' ' -f1)
if [ "$ACTUAL" != "$EXPECTED" ]; then
    echo "Empreinte SHA-256 inattendue pour jenny.c : $ACTUAL" >&2
    exit 1
fi
echo "Source verifiee   : $HERE/src/jenny.c (SHA-256 $ACTUAL)"

mkdir -p "$HERE/bin" "$HERE/build"
# Taille de unsigned long pour CE compilateur.
printf '#include <stdio.h>\nint main(void){printf("%%u\\n",(unsigned)(8*sizeof(unsigned long)));return 0;}\n' \
    > "$HERE/build/long_bits.c"
"$CC" "$HERE/build/long_bits.c" -o "$HERE/build/long_bits"
LONG_BITS=$("$HERE/build/long_bits")
echo "unsigned long     : $LONG_BITS bits"

SOURCE="$HERE/src/jenny.c"
if [ "$LONG_BITS" != "32" ] && [ "${JENNY_RAW_SOURCE:-0}" != "1" ]; then
    SOURCE="$HERE/build/jenny_portable.c"
    sed -e 's/^typedef  unsigned long      ub4;/typedef  unsigned int       ub4;/' \
        -e 's/^typedef  signed   long      sb4;/typedef  signed   int       sb4;/' \
        "$HERE/src/jenny.c" > "$SOURCE"
    CHANGED=$(diff "$HERE/src/jenny.c" "$SOURCE" | grep -c '^>' || true)
    if [ "$CHANGED" != "2" ]; then
        echo "Correctif de portabilite non applique correctement ($CHANGED lignes)." >&2
        exit 1
    fi
    echo "Portabilite       : copie compilee avec ub4/sb4 sur 32 bits (2 lignes, voir tools/jenny/SOURCE.md)"
fi

"$CC" -O3 -std=c99 -w "$SOURCE" -o "$HERE/bin/jenny"
JENNY="$HERE/bin/jenny"
[ -f "$JENNY" ] || JENNY="$HERE/bin/jenny.exe"

OUT=$("$JENNY" -n1 2 | tr -d ' \r' | tr '\n' ',')
if [ "$OUT" != "1a,1b," ]; then
    echo "Auto-test echoue : $OUT" >&2
    exit 1
fi
echo "Auto-test         : jenny -n1 2 => 1a, 1b : OK"

# Reproductibilite : memes combinaisons que la reference Windows (samples/).
UNI=$("$JENNY" -n1 5 5 5 | tr -d ' \r' | tr '\n' ',')
PAIRS=$("$JENNY" -n2 5 5 5 | grep -c .)
if [ "$UNI" = "1a2d3a,1b2b3e,1c2e3b,1d2c3c,1e2a3d," ] && [ "$PAIRS" = "28" ]; then
    echo "Reproductibilite  : identique a la reference Windows (5 cas Uniwise, 28 cas Pairwise)"
else
    echo "ATTENTION : combinaisons differentes de la reference Windows ($PAIRS cas Pairwise)." >&2
    echo "            La couverture reste garantie, mais les chiffres des docs ne correspondront pas." >&2
fi
echo "Jenny operationnel : $JENNY"
