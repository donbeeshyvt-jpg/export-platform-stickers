# export-platform-stickers

**繁體中文** | [English](README.en.md)

跨平台貼圖製作工具。從透明原圖、PNG 序列、GIF 或精靈圖，依 YouTube、Discord、LINE 的官方規格輸出、驗證並打包貼圖。

可作為 AI 技能（`SKILL.md`）使用，也可直接以 Python 指令執行。

---

## 功能

- **透明母稿**：將原圖等比縮入正方形透明畫布，預設邊長 600px，不放大低解析來源。
- **動畫拆解**：將 GIF／APNG 解碼為完整畫格，產生圖集與每格時間；亦支援自備 PNG 序列。
- **平台輸出**：依素材表逐款裁切、縮放與編碼，動畫依各平台限制調整格數與播放時間。
- **規格驗證**：每個平台產生一份檢查報告，核對尺寸、格數、播放時間與檔案大小。
- **LINE 打包**：依官方檔名規則產生送審用 ZIP。
- **輸出索引**：記錄每個成品的尺寸、格數、位元組數與 SHA-256，便於版本核對。

## 支援平台

| 平台 | 類型 | 代號 |
|---|---|---|
| YouTube | 會員自訂表情 | `yt` |
| Discord | 自訂表情 | `dc_emoji` |
| Discord | 自訂貼圖 | `dc_sticker` |
| LINE | 一般貼圖 | `line_static` |
| LINE | 動態貼圖 | `line_animated` |
| LINE | 隨你填貼圖 | `line_custom` |
| LINE | 訊息貼圖 | `line_message` |
| LINE | 大貼圖 | `line_big` |
| LINE | 全螢幕貼圖 | `line_popup` |
| LINE | 特效貼圖 | `line_effect` |
| LINE | 靜態表情貼 | `line_emoji` |
| LINE | 動態表情貼 | `line_emoji_animated` |

各平台的尺寸、容量、格數與官方來源連結，見 [`references/`](references/)。

## 系統需求

- Python 3
- Pillow 13.0.0 以上（本版以 13.0.0 驗證）

## 安裝

```powershell
git clone https://github.com/donbeeshyvt-jpg/export-platform-stickers.git
cd export-platform-stickers
pip install -r requirements.txt
```

## 使用方式

### 方式一：作為 AI 技能

1. 將整個資料夾複製到 AI 工具的技能目錄。以 Claude Code 為例：

   ```powershell
   Copy-Item -Recurse . "$HOME\.claude\skills\export-platform-stickers"
   ```

2. 在對話中說明需求，例如「把這批透明 PNG 做成 Discord 表情與 LINE 動態貼圖」。
3. AI 會依 `SKILL.md` 的五個步驟執行：確認需求 → 讀取平台規格 → 製備透明來源 → 輸出 → 檢查與交件。

### 方式二：直接執行指令

所有指令皆在倉庫根目錄執行。

1. **建立素材索引**：收錄指定資料夾中的單格 PNG，產生 CSV。

   ```powershell
   python scripts/sticker_export.py index my-stickers/index.csv --sources my-stickers/png
   ```

2. **編輯素材索引**：以 Excel 或試算表開啟 `index.csv`，依需要填寫動態檔、適用平台等欄位。欄位說明見 [`references/index.md`](references/index.md)。

3. **（選用）製作母稿或拆解動畫**：

   ```powershell
   python scripts/sticker_export.py master source.png masters --size 600
   python scripts/sticker_export.py atlas motion.gif atlas-out
   ```

4. **輸出指定平台**：以 `--targets` 選擇平台代號，輸出至新的資料夾。

   ```powershell
   python scripts/sticker_export.py build my-stickers/index.csv out --targets yt dc_emoji
   ```

5. **檢查結果**：確認各平台報告與 `output-index.csv`，再到各平台後台預覽並上傳。

## 指令一覽

| 指令 | 說明 | 主要參數 |
|---|---|---|
| `index` | 建立素材索引 CSV | `--sources`：收錄的 PNG 資料夾 |
| `master` | 製作正方形透明母稿 | `--size`：邊長；`--smooth`：改用 Lanczos 縮放 |
| `atlas` | 將動畫拆為 `sheet.png` 與 `sheet.json` | — |
| `build` | 依平台輸出成品、報告與 ZIP | `--targets`：平台代號；`--alphabet`：LINE 表情貼字母組 |

進階設定（裁切框、動畫秒數、播放次數等）見 [`references/export.md`](references/export.md)。

## 輸出內容

執行 `build` 後，輸出資料夾包含：

- 各平台子資料夾中的成品圖
- 各平台的檢查報告（`<平台代號>-report.json`）
- LINE 送審用 ZIP（選擇 LINE 平台時）
- `output-index.csv`：所有成品的規格與 SHA-256

## 注意事項

- 工具僅驗證本地檔案。交件狀態分為「本地通過」「後台預覽」「已送審」，後兩者需至各平台後台確認。
- 平台規格可能變動，上架前請以 `references/` 內的官方連結核對。
- 每次 `build` 請使用新的輸出資料夾。

## 檔案結構

```text
export-platform-stickers/
├─ SKILL.md          技能本體
├─ agents/           Codex 介面設定
├─ references/       平台規格、製作流程、指令與索引說明
├─ scripts/          sticker_export.py、sticker_index.py
├─ templates/        空白素材索引與輸出索引
├─ requirements.txt
└─ LICENSE
```

各檔案用途詳見 [目錄.md](目錄.md)。

## 授權

[MIT License](LICENSE)
