# 製作指令與輸入契約

## 執行環境

需要 Python 3 與 Pillow。本版本以 Pillow 13.0.0 驗證。從技能根目錄執行。指令中的大寫參數代表使用者提供的位置或數值。

```text
python scripts/sticker_export.py index CATALOG_CSV [--sources SOURCE_DIR]
python scripts/sticker_export.py master SOURCE OUT_DIR [--size PIXELS] [--smooth]
python scripts/sticker_export.py atlas SOURCE OUT_DIR
python scripts/sticker_export.py build CATALOG_CSV_OR_PLAN_JSON OUT_DIR [--targets TARGET ...] [--alphabet SET_TYPE]
```

- index 建立素材索引；可只建立表頭，也可收錄指定目錄及子目錄的單格 PNG。請選擇專門放代表靜圖的來源資料夾。來源範圍由使用者決定。
- master 對完整原畫布等比縮入正方形透明母稿，不放大低解析來源。預設邊長 600px，可用 --size 設定。一般插畫可用 --smooth，像素圖預設用最近鄰。
- atlas 將動畫解碼為完整 RGBA 畫格，產生 sheet.png 與 sheet.json，並驗證由圖集切回的影像和時間。每格欄位為 x、y、w、h、duration_ms。自備 PNG 序列則用時間表的 frames 陣列，以 file 和 duration_ms 指定畫格。
- build 依選定平台編碼。輸出含平台素材、輸出索引 output-index.csv、每平台的機械驗證報告，以及適用的 LINE ZIP。索引欄位見 [索引表契約](index.md)。使用新的輸出目錄，全部選定項目完成後才交付。
- 既有 JSON 計畫仍可使用。根層含 items、targets 和選用的 alphabet；items 按列序排列，欄位同素材索引，targets 使用字串陣列，options 使用物件。CSV 與 JSON 的素材路徑均相對於清單位置。
- 平台代號為 yt、dc_emoji、dc_sticker、line_static、line_animated、line_custom、line_message、line_big、line_popup、line_effect、line_emoji、line_emoji_animated。

## 平台專用設定

- options 使用平台代號為鍵。單款靜圖可用 source 替換。crop 與 motion_crop 分別指定靜圖、全動作共有的裁切框，依序為左、上、右、下；右、下為開區間。未指定時，以 alpha 可見外接框或全序列聯集為準。
- YouTube 可用 size 指定方圖邊長，預設 48px。Discord 的 animate 可明確選擇靜圖；有動圖時預設保留格時間，retime 可啟用取格與整秒計時。Discord 小表情 GIF 循環播放。
- LINE 動畫以 seconds、plays、indices、duration_ms 控制單輪秒數、播放次數、來源格索引及各格時間。索引從 0 開始，格時間合計等於單輪秒數。預設單輪 2 秒、播放一次，按原時間最多採 12 格。全螢幕／特效動畫可另以 size 設定合法舞台寬高。
- LINE 上傳順序依每個目標實際選入的列序，第一款提供主要圖片與標籤圖；表情貼的四張代表圖片在後台選取。字母組須先按官方字形對照排序。
