"""
Patch sdlayer.cpp for performance optimizations on PSP2 (PS Vita).

Optimizations:
1. Reduce internal rendering resolution from 960x544 to 480x272
   (GPU does bilinear upscaling to native res for free)
2. Use vita2d_draw_texture_scale for GPU upscaling
3. Keep memcpy (only ~130KB at half-res vs ~500KB at full-res)
4. Keep vita2d_wait_rendering_done() for correct synchronization

NOTE: The resolution variables (xres, yres, xdim, ydim) are set
by patch_videomode.py in the setvideomode_sdlcommon bypass.
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
    # PATCH 1: Reduce texture creation from 960x544 to 480x272
    # =========================================================================
    # In psp2_main, the textures are created at 960x544:
    #   gpu_texture = vita2d_create_empty_texture_format(960, 544, ...)
    #   fb_texture  = vita2d_create_empty_texture_format(960, 544, ...)
    #
    # We change these to 480x272 so the Build engine renders at 1/4 pixels.
    # The GPU will upscale via bilinear filtering when drawing to 960x544 screen.

    old_gpu = 'gpu_texture = vita2d_create_empty_texture_format(960, 544, SCE_GXM_TEXTURE_FORMAT_P8_1BGR);'
    new_gpu = 'gpu_texture = vita2d_create_empty_texture_format(480, 272, SCE_GXM_TEXTURE_FORMAT_P8_1BGR); // DNF_VITA_PERFORMANCE: half-res for speed'

    if old_gpu in content:
        content = content.replace(old_gpu, new_gpu)
        changes += 1
        print("    [OK] Patched gpu_texture creation -> 480x272")
    else:
        print("    [WARN] Could not find gpu_texture creation pattern")

    old_fb = 'fb_texture = vita2d_create_empty_texture_format(960, 544, SCE_GXM_TEXTURE_FORMAT_P8_1BGR);'
    new_fb = 'fb_texture = vita2d_create_empty_texture_format(480, 272, SCE_GXM_TEXTURE_FORMAT_P8_1BGR); // DNF_VITA_PERFORMANCE: half-res for speed'

    if old_fb in content:
        content = content.replace(old_fb, new_fb)
        changes += 1
        print("    [OK] Patched fb_texture creation -> 480x272")
    else:
        print("    [WARN] Could not find fb_texture creation pattern")

    # =========================================================================
    # PATCH 2: Use vita2d_draw_texture_scale for upscaling in videoShowFrame
    # =========================================================================
    # Replace vita2d_draw_texture(gpu_texture, 0, 0) with scaled version.
    # This scales the 480x272 texture to fill the 960x544 screen.
    # Only replace the one in videoShowFrame (after memcpy with gpu_texture).

    old_draw = 'vita2d_draw_texture(gpu_texture, 0, 0);'
    new_draw = 'vita2d_draw_texture_scale(gpu_texture, 0, 0, 2.0f, 2.0f); // DNF_VITA_PERFORMANCE: upscale 480x272 -> 960x544'

    if old_draw in content:
        content = content.replace(old_draw, new_draw)
        changes += 1
        print("    [OK] Patched videoShowFrame draw -> scaled 2x")
    else:
        print("    [WARN] Could not find vita2d_draw_texture pattern")

    # =========================================================================
    # PATCH 3: Patch videoBeginDrawing to use texture stride (safety)
    # =========================================================================
    # The original code sets bytesperline = xres. This is usually correct
    # for P8 textures, but to be safe on Vita, use the actual texture stride.
    # This ensures correct rendering even if vita2d pads the texture rows.

    old_bytesperline = 'bytesperline = xres;'
    new_bytesperline = (
        '#ifdef __PSP2__\n'
        '        bytesperline = vita2d_texture_get_stride(fb_texture); // DNF_VITA_PERFORMANCE: use actual texture stride\n'
        '#else\n'
        '        bytesperline = xres;\n'
        '#endif'
    )

    if old_bytesperline in content:
        content = content.replace(old_bytesperline, new_bytesperline, 1)
        changes += 1
        print("    [OK] Patched videoBeginDrawing bytesperline -> texture stride")
    else:
        print("    [WARN] Could not find bytesperline = xres pattern")

    # =========================================================================
    # Summary
    # =========================================================================
    if changes == 0:
        print(f"  WARNING: No changes were made to {filepath}!")
        sys.exit(1)

    with open(filepath, 'w') as f:
        f.write(content)
    print(f"  {filepath} performance patched successfully ({changes} patches applied)")
    print(f"    - Textures: 480x272 (GPU upscales to 960x544)")
    print(f"    - videoShowFrame: draw_texture_scale for 2x upscaling")
    print(f"    - videoBeginDrawing: uses texture stride for safety")
    print(f"    - memcpy kept (only ~130KB at half-res)")
    print(f"    - vita2d_wait_rendering_done() kept (correct sync)")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <path_to_sdlayer.cpp>")
        sys.exit(1)

    patch_performance(sys.argv[1])
