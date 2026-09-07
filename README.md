# AP Monitor System (V0.0.6)

這是一個用於空氣污染擴散模擬數據的視覺化監測系統。能夠在網頁端動態讀取、計算並展示擴散軌跡、最佳路徑 (Optimal Trace) 以及影響範圍 (Impact Area)。

**本版本 (V0.0.6) 重大更新：核心運算邏輯全面移植至前端 JavaScript，支援 GitHub Pages 等靜態網頁託管服務，並新增小時級別的模擬選擇功能。**

## ✨ 主要功能

*   **動態數據加載 (Dynamic Data Loading)**：
    *   **即時讀取**：根據使用者選擇的日期、小時與方向，透過 `fetch` API 動態載入 `database/` 資料夾中的 `tdump` 檔案。
    *   **前端運算**：所有數據處理 (插值 Interpolation、凸包 Convex Hull、最佳路徑 Optimal Trace) 皆在瀏覽器端使用 JavaScript 執行，無需依賴後端 Python 伺服器。

*   **2D 影響範圍監測 (Impact Analysis Area)**：
    *   OpenStreetMap 風格底圖 (WebGL 加速)。
    *   **Convex Hull 演算法**：前端即時計算擴散點的凸包，精確呈現最大影響範圍。
    *   動態時間軸播放器 (支援 0 ~ 12 小時預報)。
    *   **HUD 圖例**：整合式抬頭顯示圖例，明確標示影響區域、軌跡與原點。

*   **3D 軌跡分析 (Trajectory Analysis)**：
    *   互動式 3D 儀表板，支援雙視圖 (平面軌跡 + 高度剖面)。
    *   **成員控制面板**：可單獨切換或全選/取消全選 27 個成員的軌跡顯示。
    *   **最佳路徑與不確定範圍切換**：新增專屬按鈕，可分別獨立顯示/隱藏最佳路徑 (Optimal Trace) 及其不確定性區間 (Uncertainty Bands)。
    *   **視覺優化**：軌跡線條與資料點放大顯示以提升辨識度；軌跡與高度剖面圖皆提供詳細懸停資訊 (經度、緯度、高度、時間)；高度剖面圖 Y 軸自動隨數據動態調整範圍。

*   **儀表板控制 (Dashboard Controls)**：
    *   **模擬時間選擇**：新增 **日期 (Date)** 與 **小時 (Hour)** 選擇器 (00-23)，分鐘固定為 00。
    *   **軌跡方向 (Direction)**：支援 **前向 (Forward)** 與 **後向 (Backward)** 軌跡模擬切換。
    *   **即時狀態列**：顯示目前系統時間與日期。

## 🛠️ 安裝與部署

由於 V0.0.6 已將邏輯移至前端，本系統可作為靜態網頁直接部署。

### 本地執行
1.  確保已安裝 Python (僅用於生成初始 HTML 結構)。
2.  安裝依賴：
    ```bash
    pip install numpy scipy plotly
    ```
3.  執行生成腳本：
    ```bash
    python TSMC_AP_Monitor_V0.0.6.py
    ```
4.  腳本執行完畢後會自動開啟 `index.html`。

### GitHub Pages 部署
1.  將專案推送到 GitHub Repository。
2.  在 Repository Settings -> Pages 中，將 Source 設定為 `main` branch (或您的主分支)。
3.  部署完成後，即可透過 `<username>.github.io/<repo>` 訪問。

## 📂 檔案結構與命名規範

*   `TSMC_AP_Monitor_V0.0.6.py`: 生成 HTML 結構的 Python 腳本 (Build Tool)。
*   `index.html`: 主儀表板入口。
*   `sub_plotly_2d.html`: 2D 分析子頁面 (包含前端運算邏輯)。
*   `sub_plotly_3d.html`: 3D 分析子頁面 (包含前端運算邏輯)。
*   `database/`: **(新增) 存放模擬數據檔案的目錄**。
    *   檔案命名規則：`tdump.{YYYY}-{MM}-{DD}-{HH}00.{Direction}.txt`
    *   範例：`tdump.2026-01-09-1500.Backward.txt`

## 📝 版本紀錄

*   **V0.0.6**:
    *   **架構重構**：移除 Python 後端依賴，實現純靜態網頁架構 (Static Web App)。
    *   **前端邏輯移植**：將 Python 的 `scipy.interpolate`、`scipy.spatial.ConvexHull` 等邏輯移植為 JavaScript 實現 (Monotone Chain Algorithm)。
    *   **功能增強**：
        *   新增 **小時選擇器** (00-23)。
        *   新增 **前向/後向** 模擬切換。
        *   數據源改為讀取 `database/` 目錄下的標準化命名檔案。
        *   **控制面板增強**：將「最佳路徑 (Optimal Trace)」與「不確定範圍 (Uncertainty Band)」拆分為兩個獨立的切換按鈕，提升使用者在 3D 分析時顯示控制的靈活度。
        *   **視覺增強**：軌跡圖與高度剖面圖全面放大線條寬度與資料點大小，高度圖 Y 軸範圍解除固定限制、改為隨數據自動調整 (Auto-range)，並皆新增詳細 Hover 資訊 (含時間、經緯高)。
    *   **Bug 修復**：修正 Impact Analysis 中原點 (Origin) 標記在動態更新後消失的問題。

*   **V0.0.5**:
    *   地圖引擎升級為 WebGL，優化載入速度。
    *   新增整合式動態比例尺 (Dynamic Scale Bar)。
    *   介面視覺優化 (暗色系高科技主題)。
