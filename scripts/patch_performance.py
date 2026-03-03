"""
Patch sdlayer.cpp for PS Vita performance optimizations.

KEY INSIGHT: The double-screen bug was caused by vita2d texture stride
not matching the engine's bytesperline. vita2d may pad texture rows for
GPU alignment (e.g., 480 -> 512), but the engine assumed stride = xres.

SOLUTION: Use a SEPARATE software framebuffer (uint8_t[480*272]) that the
engine renders into. bytesperline = xres = 480 exactly. Then in videoShowFrame,
copy from sw_framebuffer to the vita2d texture with proper stride handling.

Optimizations applied:
1. Render at 480x272 (4x fewer pixels for software renderer) - ~3-4x speedup
2. GPU upscales to 960x544 via vita2d_draw_texture_scale (free)
3. -O3 + no debug symbols (handled in build system)
"""
import sys
import re


def patch_performance(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    if 'DNF_VITA_PERFORMANCE' in content:
        print(f"  {filepath} performance already patched, skipping.")
        return

    original = content
    changes = 0

    # =========================================================================
    # PATCH 1: Reduce vita2d texture size from 960x544 to 480x272
    # =========================================================================
    old_gpu = 'gpu_texture = vita2d_create_empty_texture_format(960, 544, SCE_GXM_TEXTURE_FORMAT_P8_1BGR);'
    new_gpu = 'gpu_texture = vita2d_create_empty_texture_format(480, 272, SCE_GXM_TEXTURE_FORMAT_P8_1BGR); // DNF_VITA_PERFORMANCE'

    if old_gpu in content:
        content = content.replace(old_gpu, new_gpu)
        changes += 1
        print("    [OK] gpu_texture -> 480x272")

    old_fb = 'fb_texture = vita2d_create_empty_texture_format(960, 544, SCE_GXM_TEXTURE_FORMAT_P8_1BGR);'
    new_fb = 'fb_texture = vita2d_create_empty_texture_format(480, 272, SCE_GXM_TEXTURE_FORMAT_P8_1BGR); // DNF_VITA_PERFORMANCE'

    if old_fb in content:
        content = content.replace(old_fb, new_fb)
        changes += 1
        print("    [OK] fb_texture -> 480x272")

    # =========================================================================
    # PATCH 2: Use separate software framebuffer instead of vita2d texture data
    # =========================================================================
    # The engine writes to framebuffer at stride = xres = 480.
    # But vita2d texture stride might be 512 or other aligned value.
    # Using a separate buffer eliminates this mismatch entirely.

    old_fb_assign = 'framebuffer = (uint8_t*)vita2d_texture_get_datap(fb_texture);'
    new_fb_assign = (
        '// DNF_VITA_PERFORMANCE: separate software framebuffer (stride = xres = 480 exactly)\n'
        '    // Eliminates vita2d texture stride mismatch that caused double-screen bug.\n'
        '    // videoShowFrame copies this to gpu_texture with proper stride handling.\n'
        '    static uint8_t dnf_sw_framebuffer[480 * 272];\n'
        '    memset(dnf_sw_framebuffer, 0, sizeof(dnf_sw_framebuffer));\n'
        '    framebuffer = dnf_sw_framebuffer;'
    )

    if old_fb_assign in content:
        content = content.replace(old_fb_assign, new_fb_assign)
        changes += 1
        print("    [OK] framebuffer -> separate sw_framebuffer[480*272]")

    # =========================================================================
    # PATCH 3: Replace videoShowFrame memcpy + draw with stride-aware copy
    # =========================================================================
    # Old: memcpy(gpu_data, fb_data, stride*height)  -- broken with different strides
    # New: row-by-row copy from sw_framebuffer to texture + scaled draw

    memcpy_pattern = re.compile(
        r'memcpy\s*\(\s*vita2d_texture_get_datap\s*\(\s*gpu_texture\s*\)\s*,\s*'
        r'vita2d_texture_get_datap\s*\(\s*fb_texture\s*\)\s*,\s*'
        r'vita2d_texture_get_stride\s*\(\s*gpu_texture\s*\)\s*\*\s*'
        r'vita2d_texture_get_height\s*\(\s*gpu_texture\s*\)\s*\)\s*;',
        re.DOTALL
    )

    new_copy = (
        '// DNF_VITA_PERFORMANCE: stride-aware copy from sw_framebuffer to GPU texture\n'
        '    {\n'
        '        uint8_t *dst = (uint8_t*)vita2d_texture_get_datap(gpu_texture);\n'
        '        unsigned int dst_stride = vita2d_texture_get_stride(gpu_texture);\n'
        '        if (dst_stride == 480) {\n'
        '            memcpy(dst, framebuffer, 480 * 272);\n'
        '        } else {\n'
        '            int row;\n'
        '            for (row = 0; row < 272; row++) {\n'
        '                memcpy(dst + row * dst_stride, framebuffer + row * 480, 480);\n'
        '            }\n'
        '        }\n'
        '    }'
    )

    match = memcpy_pattern.search(content)
    if match:
        content = content[:match.start()] + new_copy + content[match.end():]
        changes += 1
        print("    [OK] videoShowFrame memcpy -> stride-aware copy")
    else:
        # Fallback: simpler match
        if 'memcpy(vita2d_texture_get_datap(gpu_texture)' in content:
            idx = content.find('memcpy(vita2d_texture_get_datap(gpu_texture)')
            end = content.find(';', idx)
            if end != -1:
                content = content[:idx] + new_copy + content[end + 1:]
                changes += 1
                print("    [OK] videoShowFrame memcpy -> stride-aware copy (fallback)")
        else:
            print("    [WARN] Could not find videoShowFrame memcpy")

    # =========================================================================
    # PATCH 4: Replace vita2d_draw_texture with scaled version
    # =========================================================================
    old_draw = 'vita2d_draw_texture(gpu_texture, 0, 0);'
    new_draw = 'vita2d_draw_texture_scale(gpu_texture, 0, 0, 2.0f, 2.0f); // DNF_VITA_PERFORMANCE: 480x272 -> 960x544'

    if old_draw in content:
        content = content.replace(old_draw, new_draw)
        changes += 1
        print("    [OK] draw_texture -> draw_texture_scale(2x)")

    # =========================================================================
    # PATCH 5: Fix videoBeginDrawing to use 480 as bytesperline on PSP2
    # =========================================================================
    # The engine does: bytesperline = xres; which is 480. This matches our
    # sw_framebuffer exactly. But to be extra safe, force it on PSP2.

    old_bpl = 'bytesperline = xres;'
    new_bpl = (
        '#ifdef __PSP2__\n'
        '        bytesperline = 480; // DNF_VITA_PERFORMANCE: matches sw_framebuffer stride\n'
        '#else\n'
        '        bytesperline = xres;\n'
        '#endif'
    )

    if old_bpl in content:
        content = content.replace(old_bpl, new_bpl, 1)  # only first occurrence
        changes += 1
        print("    [OK] videoBeginDrawing bytesperline = 480")

    # =========================================================================
    # Summary
    # =========================================================================
    if changes == 0:
        print(f"  WARNING: No changes made to {filepath}!")
        sys.exit(1)

    with open(filepath, 'w') as f:
        f.write(content)

    print(f"\n  Performance patched: {changes} changes applied")
    print(f"    Resolution: 480x272 (4x fewer pixels for software renderer)")
    print(f"    Framebuffer: separate sw_framebuffer (stride = 480 exactly)")
    print(f"    Display: GPU upscales to 960x544 via bilinear filtering")
    print(f"    vita2d_wait_rendering_done: KEPT (safe)")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <path_to_sdlayer.cpp>")
        sys.exit(1)

    patch_performance(sys.argv[1])
