[README.md](https://github.com/user-attachments/files/25684217/README.md)
# DNF 2001 - PS Vita Port

Standalone PS Vita port of the **Duke Nukem Forever 2001** total conversion mod for Duke Nukem 3D, built on top of [EDuke32-Vita](https://github.com/Rinnegatamante/EDuke32-Vita) by Rinnegatamante.

## How It Works

This project takes the EDuke32-Vita source port and patches it to create a **standalone VPK** that automatically loads the DNF 2001 mod without requiring the EDuke32 launcher UI. The engine is hardcoded to load `DNF.GRP` and `DNFGAME.con` from `ux0:data/DNF/`.

## Building

### Automatic (GitHub Actions)

1. Push this repo to GitHub
2. Go to **Actions** → **Build DNF 2001 Vita VPK**
3. Click **Run workflow** (or push to `main`/`master`)
4. Download `DNF2001_Vita.vpk` from the workflow artifacts

### Manual (Local Build)

Requires [VitaSDK](https://vitasdk.org/) installed:

```bash
chmod +x build_vita.sh
./build_vita.sh
```

## Installation on PS Vita

### Step 1: Install VPK
Transfer `DNF2001_Vita.vpk` to your Vita via VitaShell and install it.

### Step 2: Copy Game Data
Create the folder `ux0:data/DNF/` on your Vita and copy these files into it:

| File | Source | Required |
|------|--------|----------|
| `DUKE3D.GRP` | Original Duke Nukem 3D (retail) | ✅ Yes |
| `DNF.GRP` | DNF 2001 mod (55 MB) | ✅ Yes |
| `DNFGAME.CON` | DNF 2001 mod | ✅ Yes |
| `DNF.CON` | DNF 2001 mod | ✅ Yes |
| `DEFS.CON` | DNF 2001 mod | ✅ Yes |
| `USER.CON` | DNF 2001 mod | ✅ Yes |
| `EBIKE.CON` | DNF 2001 mod | ✅ Yes |
| `*.CFG` | DNF 2001 mod | ✅ Yes |
| `_CLIPSHAPE0.MAP` | DNF 2001 mod | ✅ Yes |

> **Note**: You need the original `DUKE3D.GRP` from a legitimate Duke Nukem 3D installation. The DNF mod is a total conversion that requires the base game resources.

### Step 3: Launch
Open the **DNF 2001 Vita** bubble on your home screen.

## Controls

| Vita Button | Action |
|-------------|--------|
| Left Stick | Move |
| Right Stick | Look |
| × (Cross) | Open / Use |
| □ (Square) | Jump |
| △ (Triangle) | Toggle Map |
| ○ (Circle) | Crouch |
| R Trigger | Fire |
| L Trigger | Alt Fire / Open |
| D-Pad | Weapon select |
| Start | Menu / Pause |
| Select | Inventory |

## Project Structure

```
DNF/
├── .github/
│   └── workflows/
│       └── build.yml          # GitHub Actions CI workflow
├── scripts/
│   ├── patch_sdlayer.py       # Patches EDuke32 for standalone DNF loading
│   ├── gen_icon.py            # Generates 128x128 icon0.png
│   ├── gen_bg.py              # Generates 840x500 LiveArea bg.png
│   └── gen_startup.py         # Generates 280x158 LiveArea startup.png
├── vita_livearea/
│   └── template.xml           # LiveArea template
├── vita_assets/               # (Optional) Custom PNG assets
│   ├── icon0.png
│   └── livearea/contents/
│       ├── bg.png
│       ├── startup.png
│       └── template.xml
├── build_vita.sh              # Local build script
└── README.md                  # This file
```

## Custom Assets (Optional)

To use your own custom artwork instead of the generated placeholders:

1. Create `vita_assets/` folder
2. Add `icon0.png` (128×128 PNG)
3. Add `livearea/contents/bg.png` (840×500 PNG)
4. Add `livearea/contents/startup.png` (280×158 PNG)
5. Rebuild

## Technical Details

- **Engine**: EDuke32 (Build engine source port)
- **Platform**: PS Vita (ARM Cortex-A9, 512MB RAM)
- **Renderer**: Software rendering (no OpenGL on Vita)
- **Title ID**: `DNF200100`
- **Data Path**: `ux0:data/DNF/`

## Credits

- **DNF 2001 Mod**: Original mod authors  
- **EDuke32**: EDuke32 team (eduke32.com)
- **EDuke32-Vita Port**: [Rinnegatamante](https://github.com/Rinnegatamante)
- **Duke Nukem 3D**: 3D Realms / Apogee Software
- **VitaSDK**: vitasdk.org

## License

This project adapts the EDuke32-Vita port which is licensed under the GNU GPL v2. See `LICENCES/` for details. The DNF mod and Duke Nukem 3D game data are copyrighted by their respective owners.
