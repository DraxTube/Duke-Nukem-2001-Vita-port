"""
Patch sdlayer.cpp to skip the EDuke32 Vita GRP launcher UI
and directly load DNF 2001 mod files.

The original psp2_main does:
1. Initialize SceAppUtil, power clocks, vita2d, textures, framebuffer
2. Show a GUI to select GRP files (launcher loop)
3. Call app_main with selected arguments

We keep step 1 (critical for video/rendering) and replace steps 2-3
with a direct app_main call using DNF arguments.
"""
import sys

def patch_sdlayer(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    if 'DNF_VITA_STANDALONE' in content:
        print(f"  {filepath} already patched, skipping.")
        return
    
    # Strategy: Find the line "baselayer_init();" which is the last critical
    # initialization call before the launcher GUI code begins.
    # Insert our direct app_main call right after it, and close the function.
    
    marker = 'baselayer_init();'
    marker_pos = content.find(marker)
    
    if marker_pos == -1:
        # Try alternate: look in psp2_main context
        print(f"  WARNING: Could not find '{marker}' in {filepath}")
        print(f"  Trying alternate strategy...")
        
        # Alternate: find scanForGRPFiles and replace from there
        alt_marker = 'scanForGRPFiles'
        alt_pos = content.find(alt_marker)
        if alt_pos == -1:
            print(f"  ERROR: Could not find patch point in {filepath}")
            sys.exit(1)
        
        # Go back to find a good insertion point (before variable declarations)
        # Find "int j, z, k" or "char *int_argv"
        search_area = content[:alt_pos]
        for m in ['int j, z, k', 'char *int_argv', 'vita2d_pgf *font']:
            idx = search_area.rfind(m)
            if idx != -1:
                # Go to start of this line
                line_start = content.rfind('\n', 0, idx) + 1
                marker_pos = line_start - len(marker) - 1  # Will be adjusted below
                break
        
        if marker_pos == -1:
            print(f"  ERROR: Could not find suitable patch point")
            sys.exit(1)
    
    # Find the end of the baselayer_init(); line
    insert_pos = marker_pos + len(marker)
    
    # Now find the end of psp2_main function.
    # Look for the pattern where psp2_main's closing brace is,
    # followed by the #ifdef _WIN32 or main() function.
    # The function ends with "return app_main(3, ..." then "}" then "}"
    
    # Find the next function definition after psp2_main
    # Look for "# ifdef _WIN32" or "#ifdef _WIN32" after our insert point
    end_markers = [
        '\n# ifdef _WIN32\nint WINAPI',
        '\n#ifdef _WIN32\nint WINAPI', 
        '\n# ifdef _WIN32\n',
        '\nint main(',
        '\n# else\nint main(',
    ]
    
    end_pos = -1
    for em in end_markers:
        idx = content.find(em, insert_pos)
        if idx != -1:
            if end_pos == -1 or idx < end_pos:
                end_pos = idx
    
    if end_pos == -1:
        print(f"  ERROR: Could not find end of psp2_main in {filepath}")
        sys.exit(1)
    
    # The replacement: close initialization, call app_main with DNF args, close function
    replacement = """

    // DNF_VITA_STANDALONE: Skip GRP selector launcher, auto-load DNF 2001
    // All vita2d + power initialization above is preserved
    // NOTE: Do NOT call vita2d_fini() here - the engine uses gpu_texture,
    // fb_texture and framebuffer globals for rendering every frame
    
    const char *dnf_argv[] = {
        "",                    // argv[0] placeholder
        "-gDNF.GRP",          // Load DNF game resource pack  
        "-xDNFGAME.con",      // Use DNF game CON script
        "-game_dir",           // Set game directory
        "ux0:data/DNF/"        // DNF data path on Vita
    };
    return app_main(5, dnf_argv);
}

#endif  // __PSP2__

"""
    
    content = content[:insert_pos] + replacement + content[end_pos:]
    
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"  {filepath} patched successfully (preserving vita2d init)")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <path_to_sdlayer.cpp>")
        sys.exit(1)
    
    patch_sdlayer(sys.argv[1])
