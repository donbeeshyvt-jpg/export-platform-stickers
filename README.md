# export-platform-stickers 跨平台貼圖製作

嗨，大家好。今天來聊一張角色圖，要怎麼變成三個平台都收的貼圖。YouTube 會員表情最佳是 48×48，Discord 大貼圖固定 320×320，LINE 動態貼圖最大 320×270。三個數字擺在一起，看了真的會頭痛，每次上架都等於重做三遍。

這個資料夾就是為了這件事做的。它是一份給 AI 讀的技能包，裡面整理了三個平台的規格、裁切和動畫的做法，還有兩支 Python 小程式負責真正的轉檔。你把透明原圖、PNG 序列、GIF 或精靈圖交給它，它照你選的平台輸出成品，再幫你檢查一遍。

會需要檢查，是因為每家的容量上限都不一樣。Discord 小表情每張要小於 256 KB，大貼圖放寬到 512 KB，LINE 動態表情貼卻只給 300 KB，格數還要落在 5 到 20 格之間。同一張動圖在 Discord 過得去，換到 LINE 就可能超標。

LINE 又是三家裡規則最細的。光是貼圖就有一般、動態、隨你填、訊息、大貼圖、全螢幕、特效七種，表情貼再分靜態和動態兩種。動態貼圖單輪要 1 到 4 整秒，單輪秒數乘上播放次數不能超過 4 秒，壓縮檔裡的檔名還要照 main、tab、01 這樣排。這一段整個讀下來，看到這裡是有點傻眼。

規則這麼多，工具就把流程拆成四個指令。index 先建一張素材表，每款貼圖一列，代號、來源圖、動態檔、要送哪些平台都填在這裡。master 把原圖等比縮成正方形的透明母稿，預設邊長 600 像素，解析度不夠的圖不會被硬放大。

母稿有了，動畫要另外處理。atlas 會把 GIF 一格一格完整拆開，排成一張圖集，順便記下每一格停幾毫秒，切回來的畫格和時間也會再核對一次。如果你手上本來就是一張一張的 PNG，寫一份時間表也能直接用。

最後一步是 build。它照素材表一列一列輸出，你可以用平台代號只挑想要的，yt 是 YouTube，dc_sticker 是 Discord 大貼圖，line_animated 是 LINE 動態貼圖，一共 12 個。跑完會拿到成品圖、每個平台一份檢查報告、LINE 要上傳的壓縮檔，還有一張輸出索引。

輸出索引是我覺得最實用的地方。每個成品檔一列，記下實際寬高、格數、單輪毫秒、檔案大小，還有一串 SHA-256 雜湊。之後有人問你送審的是哪一版，對照這串雜湊就知道，不用再一張一張比。

這邊要注意，工具能確認的只有你電腦裡的檔案。它把狀態分成本地通過、後台預覽、已送審三種，後面兩種要你自己進 YouTube Studio、Discord 伺服器設定和 LINE Creators Market 後台去看。平台規格也會改，每一條規則都附了官方連結，上架前點進去對一次比較安心。

要開始用，電腦裡要有 Python 3 和 Pillow，這一版是用 Pillow 13.0.0 測過的。把整個資料夾放進你的 AI 工具讀技能的地方，接著跟它說要做哪個平台的貼圖，它會照 SKILL.md 的五個步驟走。不靠 AI 也行，在這個資料夾裡直接下指令就好。

```powershell
pip install -r requirements.txt
```

```powershell
python scripts/sticker_export.py index my-stickers/index.csv --sources my-stickers/png
```

```powershell
python scripts/sticker_export.py build my-stickers/index.csv out --targets yt dc_emoji
```

Claude Code 讀技能的資料夾在使用者目錄底下，複製過去就會自動載入。

```powershell
Copy-Item -Recurse . "$HOME\.claude\skills\export-platform-stickers"
```

每個檔案放在哪、各自負責什麼，都整理在[目錄](目錄.md)那份文件裡。第一次用的話，可以先拿一張你最常用的表情，只跑 yt 和 dc_emoji 兩個代號，看看縮到 48 像素以後，那張臉還認不認得出來。
