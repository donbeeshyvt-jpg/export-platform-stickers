---
name: export-platform-stickers
description: 從透明原圖、PNG 序列、GIF 或精靈圖製作跨平台貼圖。適用於透明母稿、YouTube 會員表情、Discord 表情與貼圖，以及 LINE 各類貼圖和表情貼的裁切、轉檔、驗證及送審打包。
---

# 跨平台貼圖製作

1. 記下輸入來源、交件目標、每款排序、靜態代表格和希望保留的輪廓。依專案設定透明母稿尺寸；程式預設 600×600；保留原始高解析檔。需要大貼圖最高解析度時，另用足高的直式來源。
2. 依平台讀規則，依個別目標決定留白、像素尺寸、單檔上限及是否打包。
   - [YouTube 會員表情](references/youtube.md)
   - [Discord 小表情與大貼圖](references/discord.md)
   - [LINE 七種貼圖、兩種表情貼與 ZIP](references/line.md)
3. 依[裁切、分層與動圖流程](references/production.md)製備透明來源。靜圖依用途可選獨立近景；動畫採所有畫格的共同框與同一錨點。
4. 依[操作與清單欄位](references/export.md)執行 scripts/sticker_export.py。先依[索引契約](references/index.md)建立[空白素材表](templates/asset-index.csv)，或掃描使用者指定的素材目錄。交件時另提供含檔名、平台規格與雜湊的[輸出索引](templates/output-index.csv)。指定目標時可用 --targets。
5. 檢查實際解碼尺寸、幀數、播放時間與容量，再在淺深底按使用尺寸預覽。LINE 壓縮檔與平台別檢查報告分開。交件時區分「本地通過」、「後台預覽」及「已送審」。
