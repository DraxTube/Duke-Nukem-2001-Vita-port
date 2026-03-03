"""
Patch sdlayer.cpp for performance optimizations on PSP2 (PS Vita).

Strategy: keep native 960x544 resolution (changing it breaks the Build engine)
and focus on optimizations that are safe and impactful:

1. Remove vita2d_wait_rendering_done() in videoShowFrame
   - vita2d_start_drawing() on the NEXT frame implicitly waits via sceGxmBeginScene()
   - This lets CPU prepare the next frame while GPU draws the current one (pipelining)
   - Estimated gain: 15-25% FPS improvement

2. Compiler flags (-O3, remove -g) are handled in build.yml / build_vita.sh
"""
import sys


def patch_performance(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    if 'DNF_VITA_PERFORMANCE' in content:
        print(f"  {filepath} performance already patched, skipping.")
        return

    original = content
    changes = 0

    # =========================================================================
    # PATCH 1: Remove vita2d_wait_rendering_done() in videoShowFrame
    # =========================================================================
    # Original videoShowFrame flow:
    #   memcpy(gpu_data, fb_data, stride*height);  // CPU copies framebuffer
    #   vita2d_start_drawing();                     // begin GPU scene
    #   vita2d_draw_texture(gpu_texture, 0, 0);     // submit draw command
    #   vita2d_end_drawing();                        // end GPU scene
    #   vita2d_wait_rendering_done();  <-- BLOCKING: CPU waits for GPU to finish
    #   vita2d_swap_buffers();                       // swap display
    #
    # By removing vita2d_wait_rendering_done(), the CPU immediately returns
    # to the game loop and starts computing the NEXT frame while the GPU
    # is still drawing the CURRENT frame. Synchronization happens implicitly
    # when vita2d_start_drawing() calls sceGxmBeginScene() on the next frame.
    #
    # This is safe because:
    # - The memcpy already copied the data to gpu_texture before drawing
    # - The CPU writes to fb_texture (not gpu_texture) for the next frame
    # - sceGxmBeginScene waits for the previous scene to complete

    # Find videoShowFrame function and remove vita2d_wait_rendering_done within it
    showframe_func = content.find('void videoShowFrame(')
    if showframe_func == -1:
        print("    [WARN] Could not find videoShowFrame function")
    else:
        # Find vita2d_wait_rendering_done() after videoShowFrame
        wait_str = 'vita2d_wait_rendering_done();'
        wait_pos = content.find(wait_str, showframe_func)
        if wait_pos != -1:
            # Make sure it's within videoShowFrame (before next function)
            next_func = content.find('\nvoid ', showframe_func + 20)
            next_func2 = content.find('\nint32_t ', showframe_func + 20)
            # Use the closer boundary
            func_end = len(content)
            if next_func != -1:
                func_end = min(func_end, next_func)
            if next_func2 != -1:
                func_end = min(func_end, next_func2)

            if wait_pos < func_end:
                content = (content[:wait_pos] +
                          '// DNF_VITA_PERFORMANCE: removed blocking GPU wait for CPU/GPU pipelining\n'
                          '    // sync happens implicitly in next vita2d_start_drawing() -> sceGxmBeginScene()' +
                          content[wait_pos + len(wait_str):])
                changes += 1
                print("    [OK] Removed vita2d_wait_rendering_done() in videoShowFrame")
            else:
                print("    [WARN] vita2d_wait_rendering_done() found but outside videoShowFrame")
        else:
            print("    [WARN] Could not find vita2d_wait_rendering_done() in videoShowFrame")

    # =========================================================================
    # Summary
    # =========================================================================
    if changes == 0:
        print(f"  WARNING: No performance changes were made to {filepath}!")
        print(f"  The file may already be patched or patterns didn't match.")
        # Don't exit with error - the build can continue without this patch
        return

    with open(filepath, 'w') as f:
        f.write(content)
    print(f"  {filepath} performance patched successfully ({changes} patches applied)")
    print(f"    - Removed blocking GPU wait (CPU/GPU pipelining enabled)")
    print(f"    - Resolution kept at native 960x544")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <path_to_sdlayer.cpp>")
        sys.exit(1)

    patch_performance(sys.argv[1])
