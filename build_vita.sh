#!/bin/bash
set -e

###############################################################################
# DNF 2001 - PS Vita Standalone Build Script
# 
# This script:
# 1. Clones EDuke32-Vita by Rinnegatamante
# 2. Patches the source for standalone DNF 2001 mod loading
# 3. Builds the VPK using VitaSDK
#
# Requirements: VitaSDK installed with $VITASDK set
###############################################################################

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="${SCRIPT_DIR}/build_eduke32"
EDUKE32_REPO="https://github.com/Rinnegatamante/EDuke32-Vita.git"

TITLE_ID="DNF200100"
APP_TITLE="DNF 2001 Vita"
APP_VER="01.00"

echo "============================================="
echo "  DNF 2001 - PS Vita Standalone Build"
echo "============================================="

# ── Step 1: Clone EDuke32-Vita ──────────────────────────────────────────────
if [ ! -d "${BUILD_DIR}" ]; then
    echo "[1/5] Cloning EDuke32-Vita..."
    git clone --depth 1 "${EDUKE32_REPO}" "${BUILD_DIR}"
else
    echo "[1/5] EDuke32-Vita already cloned, using existing..."
fi

cd "${BUILD_DIR}"

# ── Step 2: Patch the source for standalone DNF loading ─────────────────────
echo "[2/5] Patching source for standalone DNF 2001..."

# ── Patch sdlayer.cpp: Replace psp2_main to skip launcher UI ────────────────
SDLAYER_FILE="source/build/src/sdlayer.cpp"

if ! grep -q "DNF_VITA_STANDALONE" "${SDLAYER_FILE}"; then
    echo "  Patching ${SDLAYER_FILE}..."

    # We replace the psp2_main function to skip the GRP file selector
    # and directly call app_main with DNF arguments
    cat > /tmp/dnf_psp2_patch.py << 'PYEOF'
import re
import sys

filepath = sys.argv[1]
with open(filepath, 'r') as f:
    content = f.read()

# Find psp2_main function and replace it entirely
# The function starts with "int psp2_main(" and ends before the next
# platform-specific main (WinMain / SDL_main / main)

old_psp2_pattern = r'(int psp2_main\(.*?\{)(.*?)(#\s*ifdef\s+_WIN32\s*\n\s*int\s+WINAPI\s+WinMain)'
match = re.search(old_psp2_pattern, content, re.DOTALL)

if match:
    new_psp2_body = r'''\1
// DNF_VITA_STANDALONE: Patched to auto-load DNF 2001 mod
    // Skip the GRP selector UI and directly launch with DNF arguments
    const char *dnf_argv[] = {
        "",
        "-gDNF.GRP",
        "-xDNFGAME.con",
        "-game_dir",
        "ux0:data/DNF/"
    };
    int dnf_argc = 5;
    return app_main(dnf_argc, dnf_argv);
}

\3'''
    content = re.sub(old_psp2_pattern, new_psp2_body, content, flags=re.DOTALL)
else:
    print("WARNING: Could not find psp2_main pattern, trying alternative patch...")
    # Alternative: find just the function signature and add our code right after
    alt_pattern = r'(int psp2_main\([^)]*\)\s*\{)'
    if re.search(alt_pattern, content):
        # Insert a return at the very start of the function body
        replacement = r'''\1
// DNF_VITA_STANDALONE: Auto-load DNF 2001
    {
        const char *dnf_argv[] = {
            "",
            "-gDNF.GRP",
            "-xDNFGAME.con",
            "-game_dir",
            "ux0:data/DNF/"
        };
        return app_main(5, dnf_argv);
    }
    // Original code below (unreachable):
'''
        content = re.sub(alt_pattern, replacement, content, flags=re.DOTALL)
    else:
        print("ERROR: Cannot find psp2_main function!")
        sys.exit(1)

with open(filepath, 'w') as f:
    f.write(content)

print("  sdlayer.cpp patched successfully")
PYEOF

    python3 /tmp/dnf_psp2_patch.py "${SDLAYER_FILE}"
fi

# ── Patch game.cpp: Change log path and data directory ──────────────────────
GAME_FILE="source/duke3d/src/game.cpp"

if ! grep -q "DNF_VITA_STANDALONE" "${GAME_FILE}"; then
    echo "  Patching ${GAME_FILE}..."
    
    # Change the log file path
    sed -i 's|OSD_SetLogFile("ux0:data/EDuke32/eduke32.log");|OSD_SetLogFile("ux0:data/DNF/dnf2001.log"); // DNF_VITA_STANDALONE|g' "${GAME_FILE}"
    
    echo "  game.cpp patched successfully"
fi

# ── Patch common.cpp: Change default search paths ──────────────────────────
COMMON_FILE="source/duke3d/src/common.cpp"

if [ -f "${COMMON_FILE}" ] && ! grep -q "DNF_VITA_STANDALONE" "${COMMON_FILE}"; then
    echo "  Patching ${COMMON_FILE}..."
    
    # Replace EDuke32 data path with DNF data path
    sed -i 's|ux0:data/EDuke32|ux0:data/DNF|g' "${COMMON_FILE}"
    # Add marker
    sed -i '1s/^/\/\/ DNF_VITA_STANDALONE patched\n/' "${COMMON_FILE}"
    
    echo "  common.cpp patched successfully"
fi

# ── Also patch any other files that reference the EDuke32 data path ─────────
echo "  Patching remaining data path references..."
find source/ -name "*.cpp" -o -name "*.c" -o -name "*.h" | while read f; do
    if grep -q "ux0:data/EDuke32" "$f" && ! grep -q "DNF_VITA_STANDALONE" "$f"; then
        sed -i 's|ux0:data/EDuke32|ux0:data/DNF|g' "$f"
    fi
done

# ── Patch the thread name ───────────────────────────────────────────────────
sed -i 's|sceKernelCreateThread("EDuke32"|sceKernelCreateThread("DNF2001"|g' "${SDLAYER_FILE}"

# ── Apply performance optimizations ────────────────────────────────────────
echo "  Applying performance optimizations..."
python3 "${SCRIPT_DIR}/scripts/patch_performance.py" "${SDLAYER_FILE}"

# Also patch videoSetMode for correct resolution
python3 "${SCRIPT_DIR}/scripts/patch_videomode.py" "${SDLAYER_FILE}"

# ── Step 3: Copy custom LiveArea assets ─────────────────────────────────────
echo "[3/5] Setting up VPK assets..."

# Create/copy icon and LiveArea if they exist in our project
if [ -d "${SCRIPT_DIR}/vita_assets" ]; then
    echo "  Copying custom vita_assets..."
    if [ -f "${SCRIPT_DIR}/vita_assets/icon0.png" ]; then
        # Find where the original icon is and replace it
        find . -name "icon0.png" -exec cp "${SCRIPT_DIR}/vita_assets/icon0.png" {} \;
    fi
    if [ -d "${SCRIPT_DIR}/vita_assets/livearea" ]; then
        find . -path "*/livearea/contents" -type d -exec cp -r "${SCRIPT_DIR}/vita_assets/livearea/contents/"* {} \;
    fi
fi

# ── Step 4: Build ───────────────────────────────────────────────────────────
echo "[4/5] Building EDuke32 for PS Vita (PLATFORM=PSP2)..."

# Clean previous build
make clean PLATFORM=PSP2 2>/dev/null || true

# DNF_VITA_PERFORMANCE: Remove debug symbols for release performance
sed -i 's/-mcpu=cortex-a9 -g -ffast-math/-mcpu=cortex-a9 -ffast-math/g' Common.mak

# Build with PSP2 target (OPTLEVEL=3 for max optimization)
make -j$(nproc) PLATFORM=PSP2 RELEASE=1 USE_OPENGL=0 POLYMER=0 NETCODE=0 HAVE_GTK2=0 \
    STARTUP_WINDOW=0 USE_LIBVPX=0 LUNATIC=0 SIMPLE_MENU=1 \
    OPTLEVEL=3

echo "  Build completed!"

# ── Step 5: Package VPK ─────────────────────────────────────────────────────
echo "[5/5] Packaging VPK..."

ELF_FILE=""
# Find the built ELF file
for f in eduke32.elf duke3d.elf *.elf; do
    if [ -f "$f" ]; then
        ELF_FILE="$f"
        break
    fi
done

if [ -z "${ELF_FILE}" ]; then
    echo "ERROR: No ELF file found! Build may have failed."
    exit 1
fi

echo "  Found ELF: ${ELF_FILE}"

# Create VELF
vita-elf-create "${ELF_FILE}" dnf2001.velf

# Create EBOOT
vita-make-fself -s dnf2001.velf eboot.bin

# Create param.sfo
vita-mksfoex -s TITLE_ID="${TITLE_ID}" -d ATTRIBUTE2=12 "${APP_TITLE}" param.sfo

# Prepare VPK directory structure
VPK_DIR="${SCRIPT_DIR}/vpk_contents"
rm -rf "${VPK_DIR}"
mkdir -p "${VPK_DIR}/sce_sys/livearea/contents"

cp eboot.bin "${VPK_DIR}/eboot.bin"
cp param.sfo "${VPK_DIR}/sce_sys/param.sfo"

# Copy LiveArea assets
if [ -f "${SCRIPT_DIR}/vita_assets/icon0.png" ]; then
    cp "${SCRIPT_DIR}/vita_assets/icon0.png" "${VPK_DIR}/sce_sys/icon0.png"
elif [ -f "sce_sys/icon0.png" ]; then
    cp "sce_sys/icon0.png" "${VPK_DIR}/sce_sys/icon0.png"
else
    # Generate a simple icon using ImageMagick if available
    if command -v convert &> /dev/null; then
        convert -size 128x128 xc:'#1a1a2e' \
            -fill '#e94560' -font Helvetica-Bold -pointsize 20 \
            -gravity center -annotate 0 "DNF\n2001" \
            "${VPK_DIR}/sce_sys/icon0.png"
    else
        echo "  WARNING: No icon0.png found and ImageMagick not available."
        echo "  Creating minimal placeholder icon..."
        python3 "${SCRIPT_DIR}/scripts/gen_icon.py" "${VPK_DIR}/sce_sys/icon0.png"
    fi
fi

if [ -f "${SCRIPT_DIR}/vita_assets/livearea/contents/template.xml" ]; then
    cp "${SCRIPT_DIR}/vita_assets/livearea/contents/template.xml" "${VPK_DIR}/sce_sys/livearea/contents/"
else
    cp "${SCRIPT_DIR}/vita_livearea/template.xml" "${VPK_DIR}/sce_sys/livearea/contents/" 2>/dev/null || true
fi

if [ -f "${SCRIPT_DIR}/vita_assets/livearea/contents/bg.png" ]; then
    cp "${SCRIPT_DIR}/vita_assets/livearea/contents/bg.png" "${VPK_DIR}/sce_sys/livearea/contents/"
fi
if [ -f "${SCRIPT_DIR}/vita_assets/livearea/contents/startup.png" ]; then
    cp "${SCRIPT_DIR}/vita_assets/livearea/contents/startup.png" "${VPK_DIR}/sce_sys/livearea/contents/"
fi

# Pack VPK
cd "${VPK_DIR}"
vita-pack-vpk -s sce_sys/param.sfo -b eboot.bin \
    -a sce_sys/icon0.png=sce_sys/icon0.png \
    -a sce_sys/livearea/contents/template.xml=sce_sys/livearea/contents/template.xml \
    -a sce_sys/livearea/contents/bg.png=sce_sys/livearea/contents/bg.png \
    -a sce_sys/livearea/contents/startup.png=sce_sys/livearea/contents/startup.png \
    "${SCRIPT_DIR}/DNF2001_Vita.vpk" 2>/dev/null || \
vita-pack-vpk -s sce_sys/param.sfo -b eboot.bin \
    "${SCRIPT_DIR}/DNF2001_Vita.vpk"

echo ""
echo "============================================="
echo "  BUILD COMPLETE!"
echo "  VPK: ${SCRIPT_DIR}/DNF2001_Vita.vpk"
echo "============================================="
echo ""
echo "Installation:"
echo "  1. Transfer DNF2001_Vita.vpk to your Vita and install"
echo "  2. Copy the following files to ux0:data/DNF/ on your Vita:"
echo "     - DUKE3D.GRP (from original Duke Nukem 3D)"
echo "     - DNF.GRP"
echo "     - DNFGAME.CON"
echo "     - DNF.CON"
echo "     - DEFS.CON"
echo "     - USER.CON"
echo "     - EBIKE.CON"
echo "     - All .CFG and .MAP files"
echo "============================================="
