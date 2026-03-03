"""
Patch sdlayer.cpp to bypass SDL_SetVideoMode on PSP2.

On Vita, rendering goes entirely through vita2d (videoShowFrame uses
vita2d_draw_texture). SDL_SetVideoMode tries to reinitialize vita2d
internally, which conflicts with the vita2d already initialized in
psp2_main. This patch makes videoSetMode on PSP2 set the necessary
variables (xres, yres, bpp, etc.) directly without calling SDL_SetVideoMode.

Resolution is set to 480x272 for performance. bytesperline matches xres
exactly because we use a separate software framebuffer (no texture stride
issues).
"""
import sys

def patch_videosetmode(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    if 'DNF_VITA_SKIP_SDL_SETVIDEOMODE' in content:
        print(f"  {filepath} videoSetMode already patched, skipping.")
        return
    
    marker = 'int32_t setvideomode_sdlcommon(int32_t *x, int32_t *y, int32_t c, int32_t fs, int32_t *regrab)'
    marker_pos = content.find(marker)
    
    if marker_pos == -1:
        marker = 'setvideomode_sdlcommon'
        marker_pos = content.find(marker)
        if marker_pos == -1:
            print(f"  ERROR: Could not find setvideomode_sdlcommon in {filepath}")
            sys.exit(1)
        brace_pos = content.find('{', marker_pos)
    else:
        brace_pos = content.find('{', marker_pos)
    
    if brace_pos == -1:
        print(f"  ERROR: Could not find opening brace of setvideomode_sdlcommon")
        sys.exit(1)
    
    # DNF_VITA_PERFORMANCE: 480x272 with software framebuffer
    # bytesperline = 480 (exact match to xres, no texture stride)
    # because patch_performance.py sets framebuffer to sw_framebuffer[480*272]
    psp2_block = """
#ifdef __PSP2__
    // DNF_VITA_SKIP_SDL_SETVIDEOMODE: bypass SDL, set all engine globals directly.
    // DNF_VITA_PERFORMANCE: 480x272 internal, GPU upscales to 960x544.
    // bytesperline = 480 matches sw_framebuffer layout (no texture stride issues).
    {
        xres  = *x = 480;
        yres  = *y = 272;
        xdim  = 480;
        ydim  = 272;
        bpp   = c;
        fullscreen = fs;
        bytesperline = 480;
        numpages   = 1;
        frameplace = 0;
        lockcount  = 0;
        modechange = 1;
        videomodereset = 0;
        *regrab = 0;
        return 0;
    }
#endif
"""
    
    content = content[:brace_pos + 1] + psp2_block + content[brace_pos + 1:]
    
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"  {filepath} videoSetMode patched (480x272, all globals set)")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <path_to_sdlayer.cpp>")
        sys.exit(1)
    
    patch_videosetmode(sys.argv[1])
