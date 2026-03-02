"""
Patch sdlayer.cpp to skip the EDuke32 Vita GRP launcher UI
and directly load DNF 2001 mod files.
"""
import re
import sys

def patch_sdlayer(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    if 'DNF_VITA_STANDALONE' in content:
        print(f"  {filepath} already patched, skipping.")
        return
    
    # Strategy 1: Find psp2_main function body and replace it
    # The function is: int psp2_main(SceSize args, void *argp)
    # We want to replace its body to directly call app_main with DNF args
    
    # Look for the psp2_main function 
    pattern = r'(int\s+psp2_main\s*\([^)]*\)\s*\{)'
    match = re.search(pattern, content)
    
    if match:
        # Insert our early return right after the opening brace
        insertion = """
    // DNF_VITA_STANDALONE: Skip GRP selector, auto-load DNF 2001
    {
        const char *dnf_argv[] = {
            "",                    // argv[0] placeholder
            "-gDNF.GRP",          // Load DNF game resource pack  
            "-xDNFGAME.con",      // Use DNF game CON script
            "-game_dir",           // Set game directory
            "ux0:data/DNF/"        // DNF data path on Vita
        };
        return app_main(5, dnf_argv);
    }
    // Original launcher code below (unreachable):
"""
        content = content[:match.end()] + insertion + content[match.end():]
        
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"  {filepath} patched successfully (Strategy 1: early return)")
        return
    
    # Strategy 2: If psp2_main is not found, look for where app_main is called
    # with int_argv and patch those call sites
    pattern2 = r'return\s+app_main\s*\(\s*3\s*,\s*\(const\s+char\s*\*\*\)\s*int_argv\s*\)'
    match2 = re.search(pattern2, content)
    
    if match2:
        replacement = """return app_main(5, (const char *[]){
            "", "-gDNF.GRP", "-xDNFGAME.con", "-game_dir", "ux0:data/DNF/"
        }) /* DNF_VITA_STANDALONE */"""
        content = content[:match2.start()] + replacement + content[match2.end():]
        
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"  {filepath} patched successfully (Strategy 2: replace app_main call)")
        return
    
    print(f"  ERROR: Could not find suitable patch point in {filepath}")
    print("  Please check the source code structure manually.")
    sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <path_to_sdlayer.cpp>")
        sys.exit(1)
    
    patch_sdlayer(sys.argv[1])
