# ATTEMPTING:
# 
# 
# - eventually might want tile counts? iono...
import tkinter as tk
from tkinter import filedialog
import json

class PaletteManager:
    def __init__(self):
        # NES palette (without duplicates)
        self.nes_palette = {
            "$00": "#656565", "$01": "#002D69", "$02": "#131F7F", "$03": "#3C137C",
            "$04": "#600B62", "$05": "#730A37", "$06": "#710F07", "$07": "#5A1A00",
            "$08": "#342800", "$09": "#0B3400", "$0A": "#003C00", "$0B": "#003D10",
            "$0C": "#003840", "$0F": "#000000",
            "$10": "#AEAEAE", "$11": "#0F63B3", "$12": "#4051D0", "$13": "#7841CC",
            "$14": "#A736A9", "$15": "#C03470", "$16": "#BD3C30", "$17": "#9F4A00",
            "$18": "#6D5C00", "$19": "#366D00", "$1A": "#077704", "$1B": "#00793D",
            "$1C": "#00727D",
            "$20": "#FFFFFF", "$21": "#5DB3FF", "$22": "#8FA1FF", "$23": "#C890FF",
            "$24": "#F785FA", "$25": "#FF83C0", "$26": "#FF8B7F", "$27": "#EF9A49",
            "$28": "#BDAC2C", "$29": "#85BC2F", "$2A": "#55C753", "$2B": "#3CC98C",
            "$2C": "#3EC2CD", "$2D": "#4E4E4E",
            "$30": "#FFFFFF", "$31": "#BCDFFF", "$32": "#D1D8FF", "$33": "#E1D8FF",
            "$34": "#FBCDFD", "$35": "#FFCCE5", "$36": "#FFCFCA", "$37": "#F8D5B4",
            "$38": "#E4DCA8", "$39": "#CCE3A9", "$3A": "#B9E8B8", "$3B": "#AEE8D0",
            "$3C": "#AFE5EA", "$3D": "#B6B6B6"
        }
        
        # Future palettes can be added here
        self.palettes = {
            "NES": self.nes_palette
        }
        self.current_palette = "NES"

    def hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def get_palette(self, palette_name):
        return self.palettes.get(palette_name, self.nes_palette)

class NESEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("NES Tile Editor")
        self.tile_size = 8
        self.pixel_size = 20
        self.palette_manager = PaletteManager()  # Add this line
        self.colors = [(0, 0, 0), (85, 85, 85), (170, 170, 170), (255, 255, 255)]  # Default grayscale palette
        self.current_color = 0
        self.tiles = [[[0 for _ in range(8)] for _ in range(8)]]  # List of 8x8 tiles
        self.grid_rows = 2
        self.grid_cols = 2

        # Grid size controls
        self.grid_frame = tk.Frame(root)
        self.grid_frame.pack()
        tk.Label(self.grid_frame, text="Rows:").pack(side=tk.LEFT)
        self.rows_entry = tk.Entry(self.grid_frame, width=5)
        self.rows_entry.insert(0, "2")
        self.rows_entry.pack(side=tk.LEFT)
        tk.Label(self.grid_frame, text="Cols:").pack(side=tk.LEFT)
        self.cols_entry = tk.Entry(self.grid_frame, width=5)
        self.cols_entry.insert(0, "2")
        self.cols_entry.pack(side=tk.LEFT)
        tk.Button(self.grid_frame, text="Update Grid", command=self.update_grid_size).pack(side=tk.LEFT)

        # Canvas frame for tiles
        self.canvas_frame = tk.Frame(root)
        self.canvas_frame.pack(pady=10)
        self.canvases = []
        self.update_canvas_grid()

        # Palette display
        self.palette_frame = tk.Frame(root)
        self.palette_frame.pack()
        self.palette_buttons = []
        self.update_palette_display()

        # Tile controls
        self.tile_nav_frame = tk.Frame(root)
        self.tile_nav_frame.pack()
        tk.Button(self.tile_nav_frame, text="Add Tile", command=self.add_tile).pack(side=tk.LEFT)
        tk.Button(self.tile_nav_frame, text="Shift Up", command=self.shift_up).pack(side=tk.LEFT)
        tk.Button(self.tile_nav_frame, text="Shift Down", command=self.shift_down).pack(side=tk.LEFT)
        tk.Button(self.tile_nav_frame, text="Shift Left", command=self.shift_left).pack(side=tk.LEFT)
        tk.Button(self.tile_nav_frame, text="Shift Right", command=self.shift_right).pack(side=tk.LEFT)

        # ASM format option
        self.asm_dot = tk.BooleanVar(value=False)
        tk.Checkbutton(root, text="Use .db directive (check for ca65, uncheck for vasm)", variable=self.asm_dot).pack()

        # Modify the buttons section to add the new palette selection button
        tk.Button(root, text="Load Palette", command=self.load_palette).pack()
        tk.Button(root, text="Select Palette Colors", command=self.open_palette_selector).pack()  # Add this line
        tk.Button(root, text="Save Tiles (JSON)", command=self.save_json).pack()
        tk.Button(root, text="Load Tiles (JSON)", command=self.load_json).pack()
        tk.Button(root, text="Export to ASM", command=self.export_asm).pack()
        tk.Button(root, text="Import ASM to JSON", command=self.import_asm_to_json).pack()
        tk.Button(root, text="Clear All Tiles", command=self.clear_tiles).pack()
        
    def update_grid_size(self):
        try:
            self.grid_rows = int(self.rows_entry.get())
            self.grid_cols = int(self.cols_entry.get())
            if self.grid_rows < 1 or self.grid_cols < 1:
                raise ValueError
            self.update_canvas_grid()
        except ValueError:
            self.grid_rows = 2
            self.grid_cols = 2
            self.rows_entry.delete(0, tk.END)
            self.rows_entry.insert(0, "2")
            self.cols_entry.delete(0, tk.END)
            self.cols_entry.insert(0, "2")
            self.update_canvas_grid()

    def update_canvas_grid(self):
        for canvas in self.canvases:
            canvas.destroy()
        self.canvases = []

        min_tiles = self.grid_rows * self.grid_cols
        while len(self.tiles) < min_tiles:
            self.tiles.append([[0 for _ in range(8)] for _ in range(8)])

        for row in range(self.grid_rows):
            for col in range(self.grid_cols):
                canvas = tk.Canvas(
                    self.canvas_frame,
                    width=self.tile_size * self.pixel_size,
                    height=self.tile_size * self.pixel_size,
                    borderwidth=0,
                    highlightthickness=0
                )
                canvas.grid(row=row, column=col, padx=0, pady=0, sticky="nsew")
                canvas.bind("<Button-1>", lambda e, r=row, c=col: self.draw_pixel(e, r, c))
                canvas.bind("<B1-Motion>", lambda e, r=row, c=col: self.draw_pixel(e, r, c))
                self.canvases.append(canvas)

        self.draw_grid()

    def draw_grid(self):
        for i, canvas in enumerate(self.canvases):
            canvas.delete("all")
            if i < len(self.tiles):
                tile_data = self.tiles[i]
                for y in range(self.tile_size):
                    for x in range(self.tile_size):
                        color = self.colors[tile_data[y][x]]
                        canvas.create_rectangle(
                            x * self.pixel_size, y * self.pixel_size,
                            (x + 1) * self.pixel_size, (y + 1) * self.pixel_size,
                            fill=f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}",
                            outline="gray"
                        )

    def update_palette_display(self):
        for btn in self.palette_buttons:
            btn.destroy()
        self.palette_buttons = []
        for i, color in enumerate(self.colors):
            btn = tk.Button(
                self.palette_frame,
                bg=f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}",
                width=2, height=1,
                command=lambda idx=i: self.select_color(idx)
            )
            btn.pack(side=tk.LEFT)
            self.palette_buttons.append(btn)

    def select_color(self, index):
        self.current_color = index

    def draw_pixel(self, event, row, col):
        x = event.x // self.pixel_size
        y = event.y // self.pixel_size
        if 0 <= x < self.tile_size and 0 <= y < self.tile_size:
            tile_idx = row * self.grid_cols + col
            if tile_idx < len(self.tiles):
                self.tiles[tile_idx][y][x] = self.current_color
                self.draw_grid()

    def add_tile(self):
        self.tiles.append([[0 for _ in range(8)] for _ in range(8)])
        self.draw_grid()

    def shift_up(self):
        print("\n=== Shift Up ===")
        # Store top rows
        top_rows = [tile[0].copy() for tile in self.tiles]
        print("Stored top rows:")
        for i, row in enumerate(top_rows):
            print(f"Tile {i}: {row}")

        # Shift each tile up
        for tile in self.tiles:
            for y in range(self.tile_size - 1):
                tile[y] = tile[y + 1].copy()

        # Redistribute top rows (inner shift and wrap)
        for i in range(len(self.tiles)):
            below_idx = i + self.grid_cols
            if below_idx < len(self.tiles):
                tile[i][-1] = top_rows[below_idx]  # Inner shift
            else:
                # Wrap to top of same column
                col = i % self.grid_cols
                wrap_idx = col  # Top tile in this column
                self.tiles[i][-1] = top_rows[wrap_idx]

        print("Tiles after shift:")
        for i, tile in enumerate(self.tiles):
            print(f"Tile {i}:")
            for row in tile:
                print(f"  {row}")
        self.draw_grid()

    def shift_down(self):
        print("\n=== Shift Down ===")
        # Store bottom rows
        bottom_rows = [tile[-1].copy() for tile in self.tiles]
        print("Stored bottom rows:")
        for i, row in enumerate(bottom_rows):
            print(f"Tile {i}: {row}")

        # Shift each tile down
        for tile in self.tiles:
            for y in range(self.tile_size - 1, 0, -1):
                tile[y] = tile[y - 1].copy()

        # Redistribute bottom rows (inner shift and wrap)
        for i in range(len(self.tiles)):
            above_idx = i - self.grid_cols
            if above_idx >= 0:
                self.tiles[i][0] = bottom_rows[above_idx]  # Inner shift
            else:
                # Wrap to bottom of same column
                col = i % self.grid_cols
                wrap_idx = col + (self.grid_rows - 1) * self.grid_cols
                self.tiles[i][0] = bottom_rows[wrap_idx]

        print("Tiles after shift:")
        for i, tile in enumerate(self.tiles):
            print(f"Tile {i}:")
            for row in tile:
                print(f"  {row}")
        self.draw_grid()

    def shift_left(self):
        print("\n=== Shift Left ===")
        # Store left columns
        left_cols = [[tile[y][0] for y in range(8)] for tile in self.tiles]
        print("Stored left columns:")
        for i, col in enumerate(left_cols):
            print(f"Tile {i}: {col}")

        # Shift each tile left
        for tile in self.tiles:
            for y in range(self.tile_size):
                for x in range(self.tile_size - 1):
                    tile[y][x] = tile[y][x + 1]

        # Redistribute left columns (inner shift and wrap)
        for i in range(len(self.tiles)):
            right_idx = i + 1
            row = i // self.grid_cols
            if right_idx < len(self.tiles) and (right_idx % self.grid_cols) != 0:
                # Inner shift
                for y in range(self.tile_size):
                    self.tiles[i][y][-1] = left_cols[right_idx][y]
            else:
                # Wrap to leftmost tile in same row
                wrap_idx = row * self.grid_cols
                for y in range(self.tile_size):
                    self.tiles[i][y][-1] = left_cols[wrap_idx][y]

        print("Tiles after shift:")
        for i, tile in enumerate(self.tiles):
            print(f"Tile {i}:")
            for row in tile:
                print(f"  {row}")
        self.draw_grid()

    def shift_right(self):
        print("\n=== Shift Right ===")
        # Store right columns
        right_cols = [[tile[y][-1] for y in range(8)] for tile in self.tiles]
        print("Stored right columns:")
        for i, col in enumerate(right_cols):
            print(f"Tile {i}: {col}")

        # Shift each tile right
        for tile in self.tiles:
            for y in range(self.tile_size):
                for x in range(self.tile_size - 1, 0, -1):
                    tile[y][x] = tile[y][x - 1]

        # Redistribute right columns (inner shift and wrap)
        for i in range(len(self.tiles)):
            left_idx = i - 1
            row = i // self.grid_cols
            if left_idx >= 0 and (i % self.grid_cols) != 0:
                # Inner shift
                for y in range(self.tile_size):
                    self.tiles[i][y][0] = right_cols[left_idx][y]
            else:
                # Wrap to rightmost tile in same row
                wrap_idx = row * self.grid_cols + (self.grid_cols - 1)
                for y in range(self.tile_size):
                    self.tiles[i][y][0] = right_cols[wrap_idx][y]

        print("Tiles after shift:")
        for i, tile in enumerate(self.tiles):
            print(f"Tile {i}:")
            for row in tile:
                print(f"  {row}")
        self.draw_grid()

    def load_palette(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if file_path:
            with open(file_path, "r") as f:
                lines = f.readlines()
                self.colors = []
                for line in lines:
                    if line.strip():
                        r, g, b = map(int, line.strip().split(","))
                        self.colors.append((r, g, b))
                if len(self.colors) < 4:
                    self.colors.extend([(0, 0, 0)] * (4 - len(self.colors)))
                self.colors = self.colors[:4]
            self.update_palette_display()
            self.draw_grid()

    def save_json(self):
        def reshape_tile(tile):
            return [tile[i:i + 8] for i in range(0, 64, 8)]

        data = {
            "tiles": [reshape_tile(tile) for tile in self.tiles],
            "palette": {
                "colors": [
                    {
                        "rgb": color[0],
                        "hex": color[1],
                        "nes_code": color[2]
                    } for color in self.selected_colors
                ] if hasattr(self, 'selected_colors') and self.selected_colors else [
                    {
                        "rgb": self.palette_manager.hex_to_rgb(f"#{c[0]:02x}{c[1]:02x}{c[2]:02x}"),
                        "hex": f"#{c[0]:02x}{c[1]:02x}{c[2]:02x}",
                        "nes_code": "N/A"
                    } for c in self.colors
                ]
            }
        }
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, "w") as f:
                json.dump(data, f, indent=4)


    def load_json(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, "r") as f:
                data = json.load(f)
                self.tiles = data["tiles"]
                
                # Load palette information
                if "palette" in data and "colors" in data["palette"]:
                    self.selected_colors = []
                    for color_data in data["palette"]["colors"]:
                        self.selected_colors.append((
                            tuple(color_data["rgb"]),  # RGB tuple
                            color_data["hex"],        # Hex string
                            color_data["nes_code"]    # NES code
                        ))
                    self.colors = [color[0] for color in self.selected_colors]
                    self.update_palette_display()
                
                self.update_canvas_grid()

    def export_asm(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".asm", filetypes=[("Assembly files", "*.asm")])
        if file_path:
            with open(file_path, "w") as f:
                f.write("; NES Tile Data (8x8, 4-color)\n")
                
                # Write palette information
                f.write("; Palette Colors:\n")
                if hasattr(self, 'selected_colors') and self.selected_colors:
                    for i, color in enumerate(self.selected_colors):
                        rgb, hex_color, nes_code = color
                        f.write(f"; Color {i}: NES {nes_code}, HEX {hex_color}, RGB {rgb}\n")
                else:
                    for i, color in enumerate(self.colors):
                        hex_color = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
                        f.write(f"; Color {i}: HEX {hex_color}, RGB {color} (No NES code)\n")
                f.write("\n")
                
                directive = ".db " if self.asm_dot.get() else "db "
                for tile_idx, tile in enumerate(self.tiles):
                    bitplane0 = []
                    bitplane1 = []
                    for y in range(self.tile_size):
                        low_bits = high_bits = 0
                        for x in range(self.tile_size):
                            pixel = tile[y][x]
                            low_bits |= ((pixel & 1) << (7 - x))
                            high_bits |= (((pixel >> 1) & 1) << (7 - x))
                        bitplane0.append(low_bits)
                        bitplane1.append(high_bits)
                    chr_data = bitplane0 + bitplane1
                    f.write(f"; Tile {tile_idx + 1}\n")
                    f.write(directive + ", ".join(f"%{b:08b}" for b in chr_data[:8]) + "\n")
                    f.write(directive + ", ".join(f"%{b:08b}" for b in chr_data[8:]) + "\n")
                    
    def import_asm_to_json(self):
        asm_file = filedialog.askopenfilename(filetypes=[("Assembly files", "*.asm")])
        if asm_file:
            chr_data = []
            palette_info = []
            
            # First, parse the ASM file for palette information
            with open(asm_file, "r") as f:
                for line in f:
                    line = line.strip()
                    # Look for palette comments
                    if line.startswith("; Color"):
                        parts = line.split(":", 1)[1].strip()
                        if "NES" in parts:
                            # Extract NES code, HEX, and RGB
                            nes_code = parts.split("NES")[1].split(",")[0].strip()
                            hex_color = parts.split("HEX")[1].split(",")[0].strip()
                            rgb_str = parts.split("RGB")[1].strip()
                            rgb = tuple(map(int, rgb_str.strip("()").split(",")))
                            palette_info.append((rgb, hex_color, nes_code))
                        else:
                            # Extract HEX and RGB (no NES code)
                            hex_color = parts.split("HEX")[1].split(",")[0].strip()
                            rgb_str = parts.split("RGB")[1].strip()
                            rgb = tuple(map(int, rgb_str.strip("()").split(",")))
                            palette_info.append((rgb, hex_color, "N/A"))
                    
                    # Parse tile data
                    line = line.split(";")[0].strip()
                    if line.startswith(".db") or line.startswith("db"):
                        line = line.replace(".db", "").replace("db", "").strip()
                        for v in line.split(","):
                            v = v.strip()
                            if v.startswith("%"):
                                value = int(v[1:], 2)
                            elif v.startswith("$"):
                                value = int(v[1:], 16)
                            else:
                                continue
                            chr_data.append(value)

            tiles = []
            for i in range(0, len(chr_data), 16):
                tile_data = [[0 for _ in range(8)] for _ in range(8)]
                tile_bytes = chr_data[i:i+16]
                if len(tile_bytes) < 16:
                    tile_bytes.extend([0] * (16 - len(tile_bytes)))
                for y in range(8):
                    low_byte = tile_bytes[y]
                    high_byte = tile_bytes[y + 8]
                    for x in range(8):
                        low_bit = (low_byte >> (7 - x)) & 1
                        high_bit = (high_byte >> (7 - x)) & 1
                        pixel = (high_bit << 1) | low_bit
                        tile_data[y][x] = pixel
                tiles.append(tile_data)

            if not tiles:
                tiles = [[[0 for _ in range(8)] for _ in range(8)]]

            json_file = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
            if json_file:
                with open(json_file, "w") as f:
                    f.write('{\n  "tiles": [\n')
                    for i, tile in enumerate(tiles):
                        f.write('    [\n')
                        for j, row in enumerate(tile):
                            row_str = json.dumps(row)
                            f.write(f'      {row_str}' + (',' if j < len(tile) - 1 else '') + '\n')
                        f.write('    ]' + (',' if i < len(tiles) - 1 else '') + '\n')
                    f.write('  ],\n')
                    f.write('  "palette": {\n')
                    f.write('    "colors": [\n')
                    for i, (rgb, hex_color, nes_code) in enumerate(palette_info[:4]):  # Limit to 4 colors
                        f.write('      {\n')
                        f.write(f'        "rgb": {list(rgb)},\n')
                        f.write(f'        "hex": "{hex_color}",\n')
                        f.write(f'        "nes_code": "{nes_code}"\n')
                        f.write('      }' + (',' if i < min(len(palette_info), 4) - 1 else '') + '\n')
                    f.write('    ]\n')
                    f.write('  }\n')
                    f.write('}\n')
                
                self.tiles = tiles
                self.selected_colors = palette_info[:4]  # Limit to 4 colors
                self.colors = [color[0] for color in self.selected_colors]
                self.update_palette_display()
                self.update_canvas_grid()

    def clear_tiles(self):
        self.tiles = [[[0 for _ in range(8)] for _ in range(8)] for _ in range(self.grid_rows * self.grid_cols)]
        self.draw_grid()

    def open_palette_selector(self):
        selector = tk.Toplevel(self.root)
        selector.title("Select Palette Colors")
        selector.geometry("400x600")

        # Instructions
        tk.Label(selector, text="Click 4 colors to select your palette").pack(pady=5)
        
        # Selected colors display
        self.selected_colors = []
        self.selected_display = tk.Frame(selector)
        self.selected_display.pack(pady=5)
        self.selected_labels = []
        
        for i in range(4):
            frame = tk.Frame(self.selected_display)
            frame.pack(side=tk.LEFT, padx=5)
            label = tk.Label(frame, text="Empty", width=10, height=2, bg="#FFFFFF")
            label.pack()
            self.selected_labels.append(label)

        # Palette colors
        palette_frame = tk.Frame(selector)
        palette_frame.pack(pady=10)
        
        palette = self.palette_manager.get_palette("NES")
        colors_per_row = 8
        for idx, (nes_code, hex_color) in enumerate(palette.items()):
            row = idx // colors_per_row
            col = idx % colors_per_row
            rgb = self.palette_manager.hex_to_rgb(hex_color)
            btn = tk.Button(
                palette_frame,
                bg=hex_color,
                width=4,
                height=2,
                command=lambda c=rgb, h=hex_color, n=nes_code: self.select_palette_color(c, h, n)
            )
            btn.grid(row=row, column=col, padx=2, pady=2)
            btn.bind("<Enter>", lambda e, t=nes_code: self.show_color_code(e, t))
            btn.bind("<Leave>", lambda e: self.hide_color_code(e))

        # Color code display
        self.color_code_label = tk.Label(selector, text="")
        self.color_code_label.pack(pady=5)

        # Apply button
        tk.Button(selector, text="Apply Palette", command=lambda: self.apply_palette(selector)).pack(pady=10)

    def show_color_code(self, event, nes_code):
        self.color_code_label.config(text=f"NES Color: {nes_code}")

    def hide_color_code(self, event):
        self.color_code_label.config(text="")

    def select_palette_color(self, rgb, hex_color, nes_code):
        if len(self.selected_colors) < 4:
            self.selected_colors.append((rgb, hex_color, nes_code))
            self.selected_labels[len(self.selected_colors)-1].config(
                bg=hex_color,
                text=nes_code
            )
        elif len(self.selected_colors) == 4:
            # Replace the oldest selection
            self.selected_colors.pop(0)
            self.selected_colors.append((rgb, hex_color, nes_code))
            for i in range(4):
                self.selected_labels[i].config(
                    bg=self.selected_colors[i][1],
                    text=self.selected_colors[i][2]
                )

    def apply_palette(self, selector):
        if len(self.selected_colors) == 4:
            self.colors = [color[0] for color in self.selected_colors]
            self.update_palette_display()
            self.draw_grid()
            selector.destroy()
        else:
            tk.messagebox.showwarning("Warning", "Please select exactly 4 colors")

if __name__ == "__main__":
    root = tk.Tk()
    app = NESEditor(root)
    root.mainloop()
