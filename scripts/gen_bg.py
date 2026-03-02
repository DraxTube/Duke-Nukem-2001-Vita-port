"""
Generate a 840x500 PNG background for DNF 2001 Vita LiveArea (bg.png)
"""
import sys
import struct
import zlib

def create_png(width, height, pixels):
    def chunk(chunk_type, data):
        c = chunk_type + data
        checksum = struct.pack('>I', zlib.crc32(c) & 0xffffffff)
        return struct.pack('>I', len(data)) + c + checksum

    header = b'\x89PNG\r\n\x1a\n'
    ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))

    raw_data = b''
    for y in range(height):
        raw_data += b'\x00'
        for x in range(width):
            idx = (y * width + x) * 3
            raw_data += bytes(pixels[idx:idx+3])

    idat = chunk(b'IDAT', zlib.compress(raw_data, 9))
    iend = chunk(b'IEND', b'')
    return header + ihdr + idat + iend

def gen_bg(output_path):
    W, H = 840, 500
    pixels = [0] * (W * H * 3)

    for y in range(H):
        for x in range(W):
            idx = (y * W + x) * 3
            # Dark moody gradient: deep blue/black
            t_y = y / H
            t_x = x / W
            r = int(8 + t_y * 20 + t_x * 5)
            g = int(8 + t_y * 15 + t_x * 3)
            b = int(20 + t_y * 30 + t_x * 10)

            # Subtle grid lines for cyberpunk feel
            if x % 60 == 0 or y % 60 == 0:
                r = min(r + 8, 255)
                g = min(g + 8, 255)
                b = min(b + 12, 255)

            # Red accent stripe at top
            if y < 4:
                r, g, b = 200, 40, 60

            # Red accent stripe at bottom
            if y >= H - 4:
                r, g, b = 200, 40, 60

            pixels[idx] = r
            pixels[idx+1] = g
            pixels[idx+2] = b

    png_data = create_png(W, H, pixels)
    with open(output_path, 'wb') as f:
        f.write(png_data)
    print(f"  Generated bg: {output_path}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <output.png>")
        sys.exit(1)
    gen_bg(sys.argv[1])
