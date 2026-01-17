# New Display Support Checklist

This document outlines all code and documentation changes needed to support the following additional Waveshare e-ink displays.

## Requested Displays

| Display | Resolution | Color Mode | Status |
|---------|------------|------------|--------|
| 2.13" B&W | 250x122 | B&W only | Likely supported (verify) |
| 2.66" B&W | 296x152 | B&W only | Likely supported (verify) |
| 2.7" Grayscale | 264x176 | 4-level gray | **New firmware + server changes** |
| 2.9" B&W | 296x128 | B&W only | Likely supported (verify) |
| 2.9" B&W (frame) | 296x128 | B&W only | Same as above |
| 3.7" Grayscale | 480x280 | 4-level gray | **Update existing firmware** |
| 4.2" Grayscale | 400x300 | 4-level gray | **New firmware + server changes** |
| 7.5" B&W | 800x480 | B&W only | Likely supported (verify) |

---

## Summary

The existing firmware auto-detects B&W vs tri-color based on data size. **B&W only displays should already work** with the current system if you set `tricolor: False` in the config. However, verification is needed.

The **4-level grayscale displays (2.7", 3.7", and 4.2") require significant changes** - new/updated firmware, server modifications, and documentation updates.

**Important:** The existing `waveshare-screens/display_480x280.py` (3.7") is incorrectly configured as B&W but the hardware is actually 4-level grayscale. This firmware needs to be updated.

**Auto-detection:** Like tri-color displays that auto-detect B&W vs BWR based on data size, grayscale firmware should auto-detect B&W vs grayscale data, allowing users to send simple B&W content when grayscale isn't needed.

---

## Part 1: B&W Only Displays (Verification)

The following displays use the same resolution as existing firmware but are B&W only (no red). They should work with existing firmware when `tricolor: False` is set.

### 2.13" B&W (250x122)

- [ ] **Verify** existing `waveshare-screens/display_250x122.py` works with B&W-only hardware
- [ ] **Test** by setting `tricolor: False` in config and sending B&W data
- [ ] **Verify** init commands are compatible (may differ from tri-color "B" model)
- [ ] **Document** any differences in behavior

### 2.66" B&W (296x152)

- [ ] **Verify** existing `waveshare-screens/display_296x152.py` works with B&W-only hardware
- [ ] **Test** by setting `tricolor: False` in config
- [ ] **Verify** init commands are compatible
- [ ] **Document** any differences

### 2.9" B&W (296x128)

- [ ] **Verify** existing `waveshare-screens/display_296x128.py` works with B&W-only hardware
- [ ] **Test** by setting `tricolor: False` in config
- [ ] **Verify** init commands are compatible
- [ ] **Document** any differences

### 2.9" B&W with Frame (296x128)

- [ ] **Same as 2.9" B&W above** - "with frame" is physical form factor only
- [ ] **Verify** pin connections are identical

### 7.5" B&W (800x480)

- [ ] **Verify** existing `waveshare-screens/display_800x480.py` works with B&W-only hardware
- [ ] **Test** by setting `tricolor: False` in config
- [ ] **Verify** init commands are compatible (may differ from "B" tri-color model)
- [ ] **Document** any differences

---

## Part 2: 4-Level Grayscale Displays (New Feature)

These displays require significant new functionality. Grayscale displays use 2 bits per pixel (4 levels: white, light gray, dark gray, black).

### Auto-Detection Requirement (All Grayscale Firmware)

Like the existing tri-color firmware that auto-detects B&W vs BWR based on data size, **all grayscale firmware must support both B&W and grayscale modes**:

| Mode | Data Size | Description |
|------|-----------|-------------|
| B&W | `(width * height) / 8` bytes | 1 bit per pixel |
| Grayscale | `(width * height) / 4` bytes | 2 bits per pixel (4 levels) |

#### Auto-Detection Logic

- [ ] **Implement** size-based auto-detection in all grayscale firmware:

```python
EXPECTED_BYTES_BW = (DISPLAY_WIDTH * DISPLAY_HEIGHT) // 8
EXPECTED_BYTES_GRAY = (DISPLAY_WIDTH * DISPLAY_HEIGHT) // 4

def epd_display(img_data):
    is_bw = len(img_data) == EXPECTED_BYTES_BW
    is_gray = len(img_data) == EXPECTED_BYTES_GRAY

    if is_bw:
        epd_display_bw(img_data)
    elif is_gray:
        epd_display_gray(img_data)
    else:
        print(f"Invalid size: {len(img_data)}")
```

- [x] **Implement** `epd_display_bw()` for simple black/white content ✅ Done
- [x] **Implement** `epd_display_gray()` for 4-level grayscale content ✅ Done
- [ ] **Test** both modes work correctly on each grayscale display ⏳ Requires hardware

---

### 2.7" Grayscale (264x176)

#### Pico Firmware (`waveshare-screens/display_264x176.py`)

- [x] **Create** new firmware file `waveshare-screens/display_264x176.py` ✅ Done
- [x] **Set** display dimensions: `DISPLAY_WIDTH = 264`, `DISPLAY_HEIGHT = 176` ✅ Done
- [x] **Calculate** expected bytes: ✅ Done
  - B&W: `(264 * 176) / 8 = 5,808 bytes`
  - Grayscale: `(264 * 176) / 4 = 11,616 bytes`
- [x] **Add** auto-detection for B&W vs grayscale (see Auto-Detection section above) ✅ Done
- [x] **Implement** grayscale-specific init sequence from Waveshare datasheet ✅ Placeholder (needs verification)
- [x] **Implement** `epd_display_bw()` function for B&W mode ✅ Done
- [x] **Implement** `epd_display_gray()` function for 4-level grayscale ✅ Done
- [ ] **Test** B&W mode ⏳ Requires hardware
- [ ] **Test** grayscale mode with sample images ⏳ Requires hardware
- [ ] **Verify** refresh behavior and timing for both modes ⏳ Requires hardware

#### Init Commands (from Waveshare 2.7" grayscale datasheet)

- [ ] **Research** correct init commands for 2.7" grayscale display ⏳ Needs verification
- [ ] **Implement** LUT (look-up table) for grayscale levels ⏳ May need adjustment
- [ ] **Configure** proper voltage settings for grayscale ⏳ May need adjustment

### 3.7" Grayscale (480x280) - UPDATE EXISTING

**Note:** The existing `waveshare-screens/display_480x280.py` was incorrectly configured as B&W only. It has been updated to support grayscale with B&W auto-detection.

#### Pico Firmware (`waveshare-screens/display_480x280.py` - Update)

- [x] **Backup** existing `waveshare-screens/display_480x280.py` ✅ Original preserved in git
- [x] **Update** expected bytes calculations: ✅ Done
  - B&W: `(480 * 280) / 8 = 16,800 bytes`
  - Grayscale: `(480 * 280) / 4 = 33,600 bytes`
- [x] **Add** auto-detection for B&W vs grayscale (see Auto-Detection section above) ✅ Done
- [x] **Implement** grayscale-specific init sequence from Waveshare datasheet ✅ Placeholder (needs verification)
- [x] **Implement** `epd_display_bw()` function for B&W mode ✅ Done
- [x] **Implement** `epd_display_gray()` function for 4-level grayscale ✅ Done
- [ ] **Test** B&W mode (should work like before) ⏳ Requires hardware
- [ ] **Test** grayscale mode with sample images ⏳ Requires hardware
- [ ] **Verify** refresh behavior and timing for both modes ⏳ Requires hardware

#### Init Commands (from Waveshare 3.7" grayscale datasheet)

- [ ] **Research** correct init commands for 3.7" grayscale display ⏳ Needs verification
- [ ] **Implement** LUT (look-up table) for grayscale levels ⏳ May need adjustment
- [ ] **Configure** proper voltage settings for grayscale ⏳ May need adjustment
- [ ] **Determine** if separate init is needed for B&W vs grayscale modes ⏳ Needs testing

---

### 4.2" Grayscale (400x300)

#### Pico Firmware (`waveshare-screens/display_400x300_gray.py`)

- [x] **Create** new firmware file `waveshare-screens/display_400x300_gray.py` ✅ Done
- [x] **Set** display dimensions: `DISPLAY_WIDTH = 400`, `DISPLAY_HEIGHT = 300` ✅ Done
- [x] **Calculate** expected bytes: ✅ Done
  - B&W: `(400 * 300) / 8 = 15,000 bytes`
  - Grayscale: `(400 * 300) / 4 = 30,000 bytes`
- [x] **Add** auto-detection for B&W vs grayscale (see Auto-Detection section above) ✅ Done
- [x] **Implement** grayscale-specific init sequence from Waveshare datasheet ✅ Placeholder (needs verification)
- [x] **Implement** `epd_display_bw()` function for B&W mode ✅ Done
- [x] **Implement** `epd_display_gray()` function for 4-level grayscale ✅ Done
- [ ] **Test** B&W mode ⏳ Requires hardware
- [ ] **Test** grayscale mode with sample images ⏳ Requires hardware
- [ ] **Verify** refresh behavior and timing for both modes

#### Init Commands (from Waveshare 4.2" grayscale datasheet)

- [ ] **Research** correct init commands for 4.2" grayscale display
- [ ] **Implement** LUT for grayscale levels
- [ ] **Configure** proper voltage settings

---

## Part 3: Server Changes for Grayscale

### Display Server (`display_server.py`)

#### New Conversion Method

- [x] **Add** `convert_to_grayscale()` method to `DisplayServer` class ✅ Done
- [x] **Implement** RGB to 4-level grayscale conversion: ✅ Done
  - White: brightness > 192
  - Light gray: brightness > 128
  - Dark gray: brightness > 64
  - Black: brightness <= 64
- [x] **Pack** 4 pixels per byte (2 bits each) ✅ Done
- [x] **Return** binary data in correct byte order for display ✅ Done

```python
# Example implementation outline
def convert_to_grayscale(self, image: Image.Image) -> bytes:
    """
    Convert PIL image to 4-level grayscale binary format

    Args:
        image: PIL Image (RGB mode)

    Returns:
        Binary data with 2 bits per pixel (4 pixels per byte)
    """
    # Convert to grayscale
    gray = image.convert('L')
    width, height = gray.size
    pixels = gray.load()

    buffer = []
    for y in range(height):
        for x in range(0, width, 4):  # 4 pixels per byte
            byte = 0
            for i in range(4):
                if x + i < width:
                    brightness = pixels[x + i, y]
                    # Map to 4 levels (2 bits)
                    if brightness > 192:
                        level = 0b00  # White
                    elif brightness > 128:
                        level = 0b01  # Light gray
                    elif brightness > 64:
                        level = 0b10  # Dark gray
                    else:
                        level = 0b11  # Black
                    byte |= (level << (6 - i * 2))
            buffer.append(byte)

    return bytes(buffer)
```

#### Display Class Updates

- [x] **Add** `grayscale` attribute to `Display` class ✅ Done
- [x] **Update** `__init__` to accept `grayscale: bool = False` ✅ Done
- [x] **Update** `__repr__` to show "GRAY" for grayscale displays ✅ Done

#### Update Display Method

- [x] **Modify** `update_display()` to check for grayscale displays ✅ Done
- [x] **Call** `convert_to_grayscale()` when `display.grayscale == True` ✅ Done
- [x] **Call** `convert_to_binary()` (B&W) when `display.grayscale == False` (even on grayscale-capable hardware) ✅ Done
- [x] **Ensure** tricolor and grayscale are mutually exclusive ✅ Done (raises ValueError)

### Config Updates (`config_example.py`)

- [x] **Add** `grayscale` option to display configuration ✅ Done
- [x] **Add** example configurations for grayscale displays ✅ Done
- [x] **Document** that `tricolor` and `grayscale` are mutually exclusive ✅ Done
- [x] **Document** that grayscale displays can receive B&W data when `grayscale: False` ✅ Done

```python
# Example config for grayscale display (using grayscale mode)
displays = {
    'office': {
        'ip': '192.168.1.105',
        'port': 8080,
        'width': 480,
        'height': 280,
        'tricolor': False,
        'grayscale': True  # Send 4-level grayscale data
    }
}

# Example config for grayscale display (using B&W mode for simpler content)
displays = {
    'hallway': {
        'ip': '192.168.1.106',
        'port': 8080,
        'width': 480,
        'height': 280,
        'tricolor': False,
        'grayscale': False  # Send B&W data (firmware auto-detects)
    }
}
```

---

## Part 4: Plugin Updates (Optional)

### Base Plugin (`plugins/base.py`)

- [x] **Update** `generate()` signature documentation to mention grayscale ✅ Done
- [x] **Consider** adding `grayscale` parameter to `generate()` method ✅ Added to all plugins

### Existing Plugins

- [x] **Review** each plugin for grayscale compatibility ✅ All updated with grayscale parameter
- [x] **Weather plugin**: Should work (uses black/white primarily) ✅ grayscale param added
- [x] **Newspaper plugin**: May benefit from grayscale for photos ✅ grayscale param added
- [x] **Photo plugin**: Should leverage grayscale for better image quality ✅ grayscale param added
- [x] **Calendar plugin**: Should work (uses black/white) ✅ grayscale param added
- [x] **Stocks plugin**: Should work (uses black/white) ✅ grayscale param added

### Photo Plugin Enhancement (Recommended)

- [ ] **Update** `plugins/photo.py` to detect grayscale displays ⏳ Future enhancement
- [ ] **Implement** better dithering for grayscale output ⏳ Future enhancement
- [ ] **Test** photo quality on grayscale displays ⏳ Requires hardware

---

## Part 5: Documentation Updates

### README.md

- [x] **Update** "Supported Displays" table with new displays ✅ Done
- [x] **Add** note about grayscale display support ✅ Done
- [x] **Add** grayscale configuration example ✅ Done

### docs/FILE_INDEX.md

- [x] **Update** file count after adding new firmware files ✅ Done (27 total)
- [x] **Add** new firmware files to Pico Firmware table ✅ Done
- [x] **Update** directory structure diagram ✅ Done

### docs/SETUP.md

- [x] **Update** "Supported Displays" table ✅ Done
- [x] **Add** grayscale display configuration section ✅ Done
- [x] **Add** grayscale-specific setup instructions ✅ Done

### waveshare-screens/DISPLAY_FIRMWARE_GUIDE.md

- [x] **Add** new firmware files to table ✅ Done
- [x] **Add** section explaining grayscale displays ✅ Done
- [x] **Document** grayscale data format ✅ Done
- [ ] **Add** grayscale troubleshooting tips ⏳ Future enhancement

### plugins/PLUGIN_GUIDE.md

- [x] **Add** section on grayscale support in plugins ✅ Done (in Colors section)
- [x] **Update** color examples to include grayscale ✅ Done
- [ ] **Add** grayscale plugin example ⏳ Future enhancement

---

## Part 6: Testing

### Hardware Testing

- [ ] **Test** each B&W display with existing firmware (`tricolor: False`)
- [ ] **Test** 2.7" grayscale display with new firmware (both B&W and grayscale modes)
- [ ] **Test** 3.7" grayscale display with updated firmware (both B&W and grayscale modes)
- [ ] **Test** 4.2" grayscale display with new firmware (both B&W and grayscale modes)
- [ ] **Verify** all pin connections match documentation

### Software Testing

- [ ] **Test** server grayscale conversion with test images
- [ ] **Test** server B&W conversion sent to grayscale displays
- [ ] **Verify** correct byte count for grayscale displays (both modes)
- [ ] **Test** all plugins on grayscale displays (both modes)
- [ ] **Test** mixed setup (B&W, tri-color, and grayscale displays)

### Integration Testing

- [ ] **Test** full workflow: plugin → server → display (grayscale mode)
- [ ] **Test** full workflow: plugin → server → display (B&W mode on grayscale hardware)
- [ ] **Test** scheduled updates on grayscale displays
- [ ] **Verify** debug images saved correctly
- [ ] **Test** switching between B&W and grayscale modes via config change

---

## Implementation Order (Recommended)

1. **Verify B&W displays** - Quick wins, may already work
2. **Research grayscale datasheets** - Get correct init commands for 2.7", 3.7", 4.2"
3. **Implement server grayscale conversion** - Can test with saved images
4. **Update 3.7" firmware first** - Already exists, just needs grayscale support added
5. **Test 3.7" end-to-end** (both B&W and grayscale modes)
6. **Create 2.7" grayscale firmware**
7. **Test 2.7" end-to-end** (both B&W and grayscale modes)
8. **Create 4.2" grayscale firmware**
9. **Test 4.2" end-to-end** (both B&W and grayscale modes)
10. **Update documentation**
11. **Update plugins for grayscale optimization**

---

## Resources

### Waveshare Documentation

- [2.7" e-Paper Wiki](https://www.waveshare.com/wiki/2.7inch_e-Paper_HAT)
- [3.7" e-Paper Wiki](https://www.waveshare.com/wiki/3.7inch_e-Paper_HAT)
- [4.2" e-Paper Wiki](https://www.waveshare.com/wiki/4.2inch_e-Paper_Module)
- [Waveshare GitHub (Python/C examples)](https://github.com/waveshare/e-Paper)

### Grayscale Technical Notes

- Grayscale displays use partial refresh LUTs for gray levels
- Data format: 2 bits per pixel, MSB first
- Typical gray levels: 0x00 (white), 0x01 (light gray), 0x02 (dark gray), 0x03 (black)
- May require multiple refresh passes for stable gray levels

---

## Notes

- B&W-only versions of displays may have different part numbers than "B" (tri-color) versions
- Grayscale displays are different from tri-color - they cannot show red
- Some displays support both B&W and grayscale modes via different LUTs
- Memory constraints on Pico may limit grayscale support on larger displays
- The existing 3.7" firmware (`waveshare-screens/display_480x280.py`) was incorrectly implemented as B&W-only
- All grayscale firmware should support receiving B&W data for simpler content (auto-detection)
