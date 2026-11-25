# 素材索引與輸出索引

兩表皆為帶 BOM 的 UTF-8 CSV，逗號分欄，可在 Excel 或其他試算表工具開啟。空白模板各只有一列表頭。複製模板至專案或用 index 指令產生素材索引。將填好的 CSV 直接交給 build。

## 素材索引：每款一列

| 欄位 | 必填 | 填寫規則 |
|---|---|---|
| key | 是 | 使用者指定的唯一識別碼，跨平台共用。英數或底線，不分大小寫判重。含 YouTube 時採 3～10 個英數字元 |
| name | 否 | 顯示名稱，供 Discord 貼圖上傳清單使用 |
| source | 是 | 代表靜圖路徑，建議使用相對路徑。圖內須同時有透明背景及可見像素 |
| motion | 依目標 | 動態內容。可填 GIF、APNG、圖集描述 JSON 或 PNG 序列時間表 |
| effect | 依目標 | LINE 全螢幕／特效動畫的來源，與本列靜圖配對 |
| targets | 條件式 | 適用的平台代號，使用直線符號或空白分隔。留空表示沿用本次選定的平台；全部留空須在 build 加 --targets |
| sampling | 否 | nearest 或 lanczos，預設 nearest |
| unicode | 否 | Discord 對應表情；上傳 Discord 大貼圖時需填妥 |
| description | 否 | Discord 替代文字，由使用者自行填寫 |
| options | 否 | JSON 物件，以平台代號對應進階輸出設定；留空採預設。試算表以標準 CSV 引號規則保存 |

- 自動收錄只產生新清單，key 依該次排序配發；原檔名保留在 source。定案後請在既有表中新增或調整列，保留已使用的 key。
- 來源路徑相對於索引檔所在資料夾。圖集或序列描述內的檔案則相對於該描述檔。自動收錄使用相對路徑；清單檔與素材應位於同一磁碟區。
- 每個平台的套組順序為素材表依該平台篩選後的列序。若提供 --targets，僅輸出指定的平台。空表可作模板，開始製作至少要有一列有效素材。

## 輸出索引：每個成品圖檔一列

| 欄位 | 意義 |
|---|---|
| key | 回連素材表，主圖及標籤記錄其來源款式 |
| target、position | 平台代號與該套組內自 1 起算的款式位置 |
| role | content 為內容、tab 為標籤、main 為主圖、overlay 為專屬演出、main_overlay 為演出主圖 |
| output_path | 圖檔相對於本次輸出資料夾的路徑 |
| archive_path、archive_member | 適用時記錄 LINE ZIP 相對路徑及其中的成員檔名；其他平台留空 |
| format、width、height | 實際編碼格式及像素寬高；依內容辨識 APNG |
| frames、cycle_ms、plays | 解碼後格數、單輪毫秒、播放次數；無限循環記 infinite，靜圖為 1 格、0 毫秒、播放次數留空 |
| bytes、sha256 | 成品實際位元組數與 SHA-256 內容雜湊，用於辨識檔案與核對封裝內容 |

build 在選定項目全部完成後寫入 output-index.csv。使用 key 串聯兩表，以 target 和 role 篩選交件，透過 archive_member 定位 ZIP 內的檔案。本地檔案通過驗證，平台預覽與審核狀態由使用者在後台確認。
