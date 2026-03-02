"""
Generate a 128x128 PNG icon for DNF 2001 Vita (icon0.png)
Uses pure Python with minimal dependencies (PIL or raw PNG).
"""
import sys
import struct
import zlib

def create_png(width, height, pixels):
    """Create a PNG file from raw pixel data."""
    def chunk(chunk_type, data):
        c = chunk_type + data
        checksum = struct.pack('>I', zlib.crc32(c) & 0xffffffff)
        return struct.pack('>I', len(data)) + c + checksum

    header = b'\x89PNG\r\n\x1a\n'
    ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))

    raw_data = b''
    for y in range(height):
        raw_data += b'\x00'  # filter: none
        for x in range(width):
            idx = (y * width + x) * 3
            raw_data += bytes(pixels[idx:idx+3])

    idat = chunk(b'IDAT', zlib.compress(raw_data, 9))
    iend = chunk(b'IEND', b'')

    return header + ihdr + idat + iend

def gen_icon(output_path):
    W, H = 128, 128
    pixels = [0] * (W * H * 3)

    for y in range(H):
        for x in range(W):
            idx = (y * W + x) * 3
            # Dark gradient background: #0a0a1a to #1a1a3e
            bg_r = int(10 + (y / H) * 16)
            bg_g = int(10 + (y / H) * 16)
            bg_b = int(26 + (y / H) * 36)

            # Red accent bar at top
            if y < 6:
                pixels[idx] = 233    # #e94560
                pixels[idx+1] = 69
                pixels[idx+2] = 96
            # Red accent bar at bottom
            elif y >= H - 6:
                pixels[idx] = 233
                pixels[idx+1] = 69
                pixels[idx+2] = 96
            # Left/right border
            elif x < 3 or x >= W - 3:
                pixels[idx] = 180
                pixels[idx+1] = 40
                pixels[idx+2] = 70
            else:
                pixels[idx] = bg_r
                pixels[idx+1] = bg_g
                pixels[idx+2] = bg_b

    # Draw "DNF" text (simple pixel font, centered)
    # D
    draw_letter_D(pixels, W, 22, 30, (233, 69, 96))
    # N
    draw_letter_N(pixels, W, 48, 30, (233, 69, 96))
    # F
    draw_letter_F(pixels, W, 78, 30, (233, 69, 96))

    # Draw "2001" smaller below
    draw_text_2001(pixels, W, 34, 72, (200, 200, 220))

    png_data = create_png(W, H, pixels)
    with open(output_path, 'wb') as f:
        f.write(png_data)
    print(f"  Generated icon: {output_path}")

def set_pixel(pixels, W, x, y, color):
    if 0 <= x < 128 and 0 <= y < 128:
        idx = (y * W + x) * 3
        pixels[idx] = color[0]
        pixels[idx+1] = color[1]
        pixels[idx+2] = color[2]

def draw_rect(pixels, W, x0, y0, w, h, color):
    for dy in range(h):
        for dx in range(w):
            set_pixel(pixels, W, x0+dx, y0+dy, color)

def draw_letter_D(pixels, W, x, y, color):
    s = 3  # stroke width
    h = 32
    w = 24
    draw_rect(pixels, W, x, y, s, h, color)       # left vertical
    draw_rect(pixels, W, x, y, w-4, s, color)      # top
    draw_rect(pixels, W, x, y+h-s, w-4, s, color)  # bottom
    draw_rect(pixels, W, x+w-s-1, y+s, s, h-s*2, color)  # right vertical (shorter)
    # Rounded corners (just fill)
    draw_rect(pixels, W, x+w-6, y, 3, s, color)
    draw_rect(pixels, W, x+w-6, y+h-s, 3, s, color)

def draw_letter_N(pixels, W, x, y, color):
    s = 3
    h = 32
    draw_rect(pixels, W, x, y, s, h, color)        # left vertical
    draw_rect(pixels, W, x+22, y, s, h, color)     # right vertical
    # Diagonal
    for i in range(h):
        dx = int(i * 19 / h)
        draw_rect(pixels, W, x+s+dx, y+i, s, 1, color)

def draw_letter_F(pixels, W, x, y, color):
    s = 3
    h = 32
    w = 22
    draw_rect(pixels, W, x, y, s, h, color)        # left vertical
    draw_rect(pixels, W, x, y, w, s, color)         # top horizontal
    draw_rect(pixels, W, x, y+14, w-5, s, color)   # middle horizontal

def draw_text_2001(pixels, W, x, y, color):
    s = 2
    # "2"
    draw_rect(pixels, W, x, y, 12, s, color)         # top
    draw_rect(pixels, W, x+10, y, s, 10, color)      # right top
    draw_rect(pixels, W, x, y+9, 12, s, color)       # middle
    draw_rect(pixels, W, x, y+9, s, 10, color)       # left bottom
    draw_rect(pixels, W, x, y+17, 12, s, color)      # bottom

    # "0"
    ox = x + 16
    draw_rect(pixels, W, ox, y, 12, s, color)        # top
    draw_rect(pixels, W, ox, y+17, 12, s, color)     # bottom
    draw_rect(pixels, W, ox, y, s, 19, color)        # left
    draw_rect(pixels, W, ox+10, y, s, 19, color)     # right

    # "0"
    ox = x + 32
    draw_rect(pixels, W, ox, y, 12, s, color)
    draw_rect(pixels, W, ox, y+17, 12, s, color)
    draw_rect(pixels, W, ox, y, s, 19, color)
    draw_rect(pixels, W, ox+10, y, s, 19, color)

    # "1"
    ox = x + 48
    draw_rect(pixels, W, ox+5, y, s, 19, color)      # vertical
    draw_rect(pixels, W, ox+1, y+17, 12, s, color)   # bottom serif

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <output.png>")
        sys.exit(1)
    gen_icon(sys.argv[1])
