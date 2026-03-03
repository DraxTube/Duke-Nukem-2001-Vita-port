"""
Patch sdlayer.cpp to bypass SDL_SetVideoMode on PSP2.

On Vita, rendering goes entirely through vita2d (videoShowFrame uses
vita2d_draw_texture). SDL_SetVideoMode tries to reinitialize vita2d
internally, which conflicts with the vita2d already initialized in
psp2_main. This patch makes videoSetMode on PSP2 set the necessary
variables (xres, yres, bpp, etc.) directly without calling SDL_SetVideoMode.
"""
import sys

def patch_videosetmode(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    if 'DNF_VITA_SKIP_SDL_SETVIDEOMODE' in content:
        print(f"  {filepath} videoSetMode already patched, skipping.")
        return
    
    # For SDL 1.2, the videoSetMode function calls SDL_SetVideoMode().
    # We need to find the setvideomode_sdlcommon function and add a PSP2-specific
    # early return that sets up variables without calling SDL_SetVideoMode.
    
    # Strategy: Find "int32_t setvideomode_sdlcommon" and insert a PSP2 block
    # at the beginning that sets xres/yres/bpp and returns success
    
    marker = 'int32_t setvideomode_sdlcommon(int32_t *x, int32_t *y, int32_t c, int32_t fs, int32_t *regrab)'
    marker_pos = content.find(marker)
    
    if marker_pos == -1:
        # Try shorter match
        marker = 'setvideomode_sdlcommon'
        marker_pos = content.find(marker)
        if marker_pos == -1:
            print(f"  ERROR: Could not find setvideomode_sdlcommon in {filepath}")
            sys.exit(1)
        # Find the opening brace
        brace_pos = content.find('{', marker_pos)
    else:
        brace_pos = content.find('{', marker_pos)
    
    if brace_pos == -1:
        print(f"  ERROR: Could not find opening brace of setvideomode_sdlcommon")
        sys.exit(1)
    
    # Insert PSP2-specific early return right after the opening brace
    # Keep native 960x544 resolution - do NOT change resolution here
    psp2_block = """
#ifdef __PSP2__
    // DNF_VITA_SKIP_SDL_SETVIDEOMODE: On Vita, rendering goes through vita2d.
    // SDL_SetVideoMode conflicts with the already-initialized vita2d context.
    // Set engine variables directly and return 0 (skip SDL setup).
    {
        xres  = *x = 960;
        yres  = *y = 544;
        xdim  = 960;
        ydim  = 544;
        bpp   = c;
        fullscreen = fs;
        bytesperline = 960;
        numpages   = 1;
        frameplace = 0;
        lockcount  = 0;
        modechange = 1;   // triggers calc_ylookup in videoBeginDrawing
        videomodereset = 0;
        *regrab = 0;
        return 0;
    }
#endif
"""
    
    content = content[:brace_pos + 1] + psp2_block + content[brace_pos + 1:]
    
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"  {filepath} videoSetMode patched for PSP2 (bypassing SDL_SetVideoMode)")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <path_to_sdlayer.cpp>")
        sys.exit(1)
    
    patch_videosetmode(sys.argv[1])
