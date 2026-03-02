"""
Generate a 280x158 PNG startup button for DNF 2001 Vita LiveArea (startup.png)
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

def set_pixel(pixels, W, x, y, color):
    if 0 <= x < W and 0 <= y < 158:
        idx = (y * W + x) * 3
        pixels[idx] = color[0]
        pixels[idx+1] = color[1]
        pixels[idx+2] = color[2]

def draw_rect(pixels, W, x0, y0, w, h, color):
    for dy in range(h):
        for dx in range(w):
            set_pixel(pixels, W, x0+dx, y0+dy, color)

def gen_startup(output_path):
    W, H = 280, 158
    pixels = [0] * (W * H * 3)

    for y in range(H):
        for x in range(W):
            idx = (y * W + x) * 3
            # Red gradient button
            t = y / H
            r = int(200 - t * 50)
            g = int(30 + t * 15)
            b = int(50 + t * 20)

            # Border
            if x < 2 or x >= W-2 or y < 2 or y >= H-2:
                r, g, b = 255, 80, 100

            pixels[idx] = r
            pixels[idx+1] = g
            pixels[idx+2] = b

    # Simple "START" text in center
    text_color = (255, 255, 255)
    # S
    draw_rect(pixels, W, 90, 65, 12, 2, text_color)
    draw_rect(pixels, W, 90, 65, 2, 12, text_color)
    draw_rect(pixels, W, 90, 75, 12, 2, text_color)
    draw_rect(pixels, W, 100, 75, 2, 12, text_color)
    draw_rect(pixels, W, 90, 85, 12, 2, text_color)

    # T
    draw_rect(pixels, W, 106, 65, 14, 2, text_color)
    draw_rect(pixels, W, 112, 65, 2, 22, text_color)

    # A
    draw_rect(pixels, W, 124, 67, 2, 20, text_color)
    draw_rect(pixels, W, 136, 67, 2, 20, text_color)
    draw_rect(pixels, W, 124, 65, 14, 2, text_color)
    draw_rect(pixels, W, 124, 76, 14, 2, text_color)

    # R
    draw_rect(pixels, W, 142, 65, 2, 22, text_color)
    draw_rect(pixels, W, 142, 65, 14, 2, text_color)
    draw_rect(pixels, W, 154, 65, 2, 12, text_color)
    draw_rect(pixels, W, 142, 75, 14, 2, text_color)
    for i in range(10):
        draw_rect(pixels, W, 148+i, 77+i, 2, 2, text_color)

    # T
    draw_rect(pixels, W, 162, 65, 14, 2, text_color)
    draw_rect(pixels, W, 168, 65, 2, 22, text_color)

    png_data = create_png(W, H, pixels)
    with open(output_path, 'wb') as f:
        f.write(png_data)
    print(f"  Generated startup: {output_path}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <output.png>")
        sys.exit(1)
    gen_startup(sys.argv[1])
