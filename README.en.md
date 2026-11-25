# export-platform-stickers

[繁體中文](README.md) | **English**

A cross-platform sticker production tool. Turn transparent source images, PNG sequences, GIFs, or sprite sheets into stickers and emotes that meet the official specs of YouTube, Discord, and LINE — exported, validated, and packaged.

Use it as an AI skill (`SKILL.md`), or run it directly as Python commands.

> The skill instructions and the reference docs under `references/` are written in Traditional Chinese.

---

## Features

- **Transparent master**: Fits the source proportionally into a square transparent canvas (600px by default). Low-resolution sources are never upscaled.
- **Animation decoding**: Decodes GIF/APNG into full frames and produces a sprite sheet with per-frame timing. Custom PNG sequences are also supported.
- **Per-platform export**: Crops, scales, and encodes each item from the asset index; animations are adjusted to each platform's frame and duration limits.
- **Spec validation**: Writes one check report per platform, covering dimensions, frame count, playback time, and file size.
- **LINE packaging**: Builds the submission ZIP using LINE's official file naming rules.
- **Output index**: Records dimensions, frame count, byte size, and SHA-256 for every output file, making version tracking easy.

## Supported Platforms

| Platform | Type | Code |
|---|---|---|
| YouTube | Channel membership emoji | `yt` |
| Discord | Custom emoji | `dc_emoji` |
| Discord | Custom sticker | `dc_sticker` |
| LINE | Static stickers | `line_static` |
| LINE | Animated stickers | `line_animated` |
| LINE | Custom stickers | `line_custom` |
| LINE | Message stickers | `line_message` |
| LINE | Big stickers | `line_big` |
| LINE | Pop-up stickers | `line_popup` |
| LINE | Effect stickers | `line_effect` |
| LINE | Emoji | `line_emoji` |
| LINE | Animated emoji | `line_emoji_animated` |

Dimensions, size limits, frame rules, and official source links for each platform are in [`references/`](references/).

## Requirements

- Python 3
- Pillow 13.0.0 or later (this version was verified with 13.0.0)

## Installation

```powershell
git clone https://github.com/donbeeshyvt-jpg/export-platform-stickers.git
cd export-platform-stickers
pip install -r requirements.txt
```

## Usage

### Option 1: As an AI skill

1. Copy the whole folder into your AI tool's skills directory. For Claude Code:

   ```powershell
   Copy-Item -Recurse . "$HOME\.claude\skills\export-platform-stickers"
   ```

2. Describe what you need, e.g. "Turn these transparent PNGs into Discord emoji and LINE animated stickers."
3. The AI follows the five steps in `SKILL.md`: confirm requirements → read platform specs → prepare transparent sources → export → validate and deliver.

### Option 2: Run the commands directly

Run all commands from the repository root.

1. **Create the asset index**: Collect single-frame PNGs from a folder into a CSV.

   ```powershell
   python scripts/sticker_export.py index my-stickers/index.csv --sources my-stickers/png
   ```

2. **Edit the asset index**: Open `index.csv` in Excel or any spreadsheet app and fill in motion files, target platforms, and other columns as needed. See [`references/index.md`](references/index.md) for the column reference.

3. **(Optional) Make masters or decode animations**:

   ```powershell
   python scripts/sticker_export.py master source.png masters --size 600
   python scripts/sticker_export.py atlas motion.gif atlas-out
   ```

4. **Export for selected platforms**: Choose platform codes with `--targets` and write to a new folder.

   ```powershell
   python scripts/sticker_export.py build my-stickers/index.csv out --targets yt dc_emoji
   ```

5. **Review the results**: Check each platform report and `output-index.csv`, then preview and upload in each platform's dashboard.

## Commands

| Command | Description | Main options |
|---|---|---|
| `index` | Create the asset index CSV | `--sources`: folder of PNGs to collect |
| `master` | Make a square transparent master | `--size`: edge length; `--smooth`: use Lanczos resampling |
| `atlas` | Split an animation into `sheet.png` and `sheet.json` | — |
| `build` | Export outputs, reports, and ZIPs per platform | `--targets`: platform codes; `--alphabet`: LINE emoji alphabet set |

For advanced options (crop boxes, animation length, loop count, etc.), see [`references/export.md`](references/export.md).

## Output

After `build`, the output folder contains:

- Output images in one subfolder per platform
- A check report per platform (`<platform-code>-report.json`)
- LINE submission ZIPs (when a LINE target is selected)
- `output-index.csv`: specs and SHA-256 for every output file

## Notes

- The tool only validates local files. Delivery status is split into "local pass", "dashboard preview", and "submitted"; the last two must be confirmed in each platform's dashboard.
- Platform specs may change. Check the official links in `references/` before publishing.
- Use a new output folder for every `build`.

## File Structure

```text
export-platform-stickers/
├─ SKILL.md          Skill definition
├─ agents/           Codex interface config
├─ references/       Platform specs, production workflow, command and index docs
├─ scripts/          sticker_export.py, sticker_index.py
├─ templates/        Blank asset index and output index
├─ requirements.txt
└─ LICENSE
```

See [目錄.md](目錄.md) (Traditional Chinese) for details on each file.

## License

[MIT License](LICENSE)
