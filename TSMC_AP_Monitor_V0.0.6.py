import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import json
import webbrowser
import base64
from scipy.interpolate import interp1d
from scipy.spatial import ConvexHull
from scipy.ndimage import gaussian_filter1d

# Constants
LAT_IDX, LON_IDX, ALT_IDX = 9, 10, 11
NUM_TIME_STEPS = 13
NUM_MEMBERS = 27
NUM_VARS = 20
INTERP_STEPS = 721

def load_and_process_data(file_path):
    # Kept for compatibility / reference
    try:
        data = np.loadtxt(file_path)
        data = data.reshape(NUM_TIME_STEPS, NUM_MEMBERS, NUM_VARS)
    except Exception as e:
        print(f"Error loading data: {e}")
        return None
    data[1:, :, ALT_IDX] /= 10.0 
    x_original = np.arange(NUM_TIME_STEPS)
    f_interp = interp1d(x_original, data, axis=0, kind='linear')
    x_new = np.linspace(0, NUM_TIME_STEPS - 1, num=INTERP_STEPS)
    return f_interp(x_new)

def calculate_optimal_trace(data):
    # Kept for compatibility / reference
    lons = data[:, :, LON_IDX]
    lats = data[:, :, LAT_IDX]
    alts = data[:, :, ALT_IDX]
    centroid_lon = np.nanmean(lons, axis=1, keepdims=True)
    centroid_lat = np.nanmean(lats, axis=1, keepdims=True)
    dists = np.sqrt((lats - centroid_lat)**2 + (lons - centroid_lon)**2)
    dists = np.nan_to_num(dists, nan=np.inf)
    valid_indices = np.argsort(dists, axis=1)[:, :25]
    row_indices = np.arange(dists.shape[0])[:, None]
    opt_lon = np.nanmean(lons[row_indices, valid_indices], axis=1)
    opt_lat = np.nanmean(lats[row_indices, valid_indices], axis=1)
    opt_alt = np.nanmean(alts[row_indices, valid_indices], axis=1)
    return opt_lon, opt_lat, opt_alt

def get_hull_path(lons, lats):
    points = np.column_stack((lons, lats))
    if len(points) < 3: return [], []
    try:
        hull = ConvexHull(points)
        closed_path = points[hull.vertices]
        closed_path = np.vstack([closed_path, closed_path[0]])
        return closed_path[:, 0].tolist(), closed_path[:, 1].tolist()
    except:
        return [], []

def generate_2d_html(data, origin):
    """Generates the 2D visualization HTML."""
    origin_lat, origin_lon = origin
    
    # Static data is no longer pre-calculated here.
    # Initial view is empty or just origin.
    
    # Initial Plot Shell
    fig = go.Figure()

    # Trace 0: Impact Area
    d = 0.0001
    fig.add_trace(go.Scattermap(
        lon=[origin_lon, origin_lon + d, origin_lon - d, origin_lon], 
        lat=[origin_lat + d, origin_lat - d, origin_lat - d, origin_lat + d], 
        fill="toself",
        mode="lines",
        fillcolor="rgba(255, 0, 0, 0.2)",
        line=dict(color="#ff0000", width=1),
        name="IMPACTED AREA"
    ))

    # Trace 1: Members (Empty initial)
    fig.add_trace(go.Scattermap(
        lon=[origin_lon], lat=[origin_lat],
        mode="markers",
        marker=dict(color="#ff0000", size=6, opacity=0.9),
        name="TRACES"
    ))

    # Trace 2: Origin
    fig.add_trace(go.Scattermap(
        lon=[origin_lon], lat=[origin_lat],
        mode="markers",
        marker=dict(size=10, color="black"),
        name="ORIGIN", hoverinfo="text", hovertext="Origin Point"
    ))

    # Trace 3: Target Zone 1
    fig.add_trace(go.Scattermap(
        lat=[24.218470, 24.218528, 24.218798, 24.218845, 24.218845, 24.218470, 24.218470],
        lon=[120.617588, 120.617480, 120.617480, 120.617588, 120.618074, 120.618074, 120.617588],
        fill="toself",
        mode="lines+markers",
        fillcolor="rgba(0, 255, 255, 0.4)",
        marker=dict(size=5, color="#00FFFF"),
        line=dict(color="#00FFFF", width=2),
        name="Target Zone 1",
        hoverinfo="skip"
    ))

    # Trace 4: Target Zone 2
    fig.add_trace(go.Scattermap(
        lat=[24.218247, 24.218247, 24.217954, 24.217815, 24.217815, 24.217954, 24.218247],
        lon=[120.619599, 120.620373, 120.620373, 120.620262, 120.619880, 120.619599, 120.619599],
        fill="toself",
        mode="lines+markers",
        fillcolor="rgba(0, 255, 255, 0.4)",
        marker=dict(size=5, color="#00FFFF"),
        line=dict(color="#00FFFF", width=2),
        name="Target Zone 2",
        hoverinfo="skip"
    ))

    fig.update_layout(
        map=dict(style="open-street-map", center=dict(lat=origin_lat, lon=origin_lon), zoom=10),
        template="plotly_dark", margin=dict(l=0, r=0, t=0, b=0),
        autosize=True, showlegend=False,
        shapes=[
            dict(type="line", xref="paper", yref="paper", x0=0.02, y0=0.03, x1=0.12, y1=0.03, line=dict(color="#000000", width=2), opacity=1),
        ],
        annotations=[
            dict(xref="paper", yref="paper", x=0.02, y=0.045, text="Scale", showarrow=False, font=dict(color="#000000", size=12, family="Consolas"), xanchor="left"),
        ]
    )

    plot_html = fig.to_html(include_plotlyjs='cdn', full_html=False)
    
    # Safe JSON dump for initial empty cache
    frame_data_json = "{}" 
    
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Impact Area Monitor</title>
    <style>
        :root {{ --accent: #00f3ff; --bg: #050505; --panel: #111; --text: #eee; --border: #333; }}
        body, html {{ margin: 0; padding: 0; height: 100vh; width: 100vw; overflow: hidden; background: var(--bg); font-family: 'Segoe UI', sans-serif; }}
        .layout-wrapper {{ display: flex; flex-direction: column; height: 100vh; width: 100vw; }}
        .chart-container {{ flex: 1; position: relative; overflow: hidden; background: #000; }}
        .chart-container > div {{ width: 100% !important; height: 100% !important; }}
        
        .bottom-panel {{ 
            height: 80px; background: var(--panel); border-top: 1px solid var(--border); 
            display: flex; align-items: center; padding: 0 30px; gap: 20px; 
            box-shadow: 0 -10px 30px rgba(0,0,0,0.8);
            position: relative;
        }}
        
        .bottom-panel::before {{
            content: ""; position: absolute; top: 0; left: 0; width: 100px; height: 2px; background: var(--accent);
            box-shadow: 0 0 10px var(--accent);
        }}

        .play-section {{ flex: 0 0 140px; }}
        .slider-section {{ flex: 1; display: flex; flex-direction: column; gap: 8px; }}
        
        .time-box {{ 
            flex: 0 0 180px; text-align: right; 
            background: #000; border: 1px solid var(--border); padding: 10px;
            font-family: 'Consolas', monospace; color: var(--accent); font-size: 18px; font-weight: bold; 
            display: flex; align-items: center; justify-content: center; gap: 10px;
        }}
        .time-box span {{ font-size: 10px; color: #666; }}

        .play-btn {{ 
            width: 100%; padding: 10px; background: transparent; border: 1px solid var(--accent); 
            color: var(--accent); font-family: 'Consolas', monospace; font-weight: bold; cursor: pointer; 
            transition: 0.2s; text-transform: uppercase; letter-spacing: 2px;
            position: relative; overflow: hidden;
        }}
        .play-btn:hover {{ background: rgba(0, 243, 255, 0.1); box-shadow: 0 0 15px rgba(0, 243, 255, 0.2); }}
        .play-btn.paused {{ border-color: #ff3333; color: #ff3333; }}
        
        input[type=range] {{ width: 100%; cursor: pointer; accent-color: var(--accent); height: 4px; background: #333; appearance: none; }}
        input[type=range]::-webkit-slider-thumb {{ appearance: none; width: 12px; height: 12px; background: var(--accent); border-radius: 0; box-shadow: 0 0 10px var(--accent); }}
        
        .label {{ color: #666; font-size: 10px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; font-family: 'Consolas', monospace; }}
        
        .chart-container .legend-bar {{
            position: absolute; bottom: 30px; left: 50%; transform: translateX(-50%);
            display: flex; gap: 40px;
            width: auto !important; height: auto !important; 
            background: rgba(10, 10, 10, 0.9);
            padding: 10px 40px;
            border: 1px solid #333; border-top: 2px solid var(--accent);
            border-radius: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.8);
            z-index: 1000;
            backdrop-filter: blur(10px);
        }}
        .legend-item {{ display: flex; align-items: center; cursor: default; transition: 0.2s; }}
        .legend-item:hover {{ transform: translateY(-2px); }}
        .legend-label {{ color: #fff; font-size: 12px; font-weight: bold; letter-spacing: 1px; font-family: 'Consolas', monospace; text-shadow: 0 0 10px rgba(0,0,0,0.5); }}
        .sym {{ width: 24px; height: 24px; margin-right: 12px; display: flex; align-items: center; justify-content: center; }}
        .sym-impact {{ background: rgba(255, 0, 0, 0.2); border: 2px solid #ff0000; width: 16px; height: 16px; box-shadow: 0 0 10px rgba(255,0,0,0.3); }}
        .sym-trace {{ width: 8px; height: 8px; background: #ff0000; border-radius: 50%; box-shadow: 0 0 8px #ff0000; }}
        .sym-origin {{ width: 10px; height: 10px; background: #000; border: 2px solid #fff; border-radius: 50%; box-shadow: 0 0 10px #fff; }}

    </style>
</head>
<body>
    <div class="layout-wrapper">
        <div class="chart-container">
            {plot_html}
            <div class="legend-bar">
                <div class="legend-item"><div class="sym"><div class="sym-impact"></div></div><div class="legend-label">IMPACT ZONE</div></div>
                <div class="legend-item"><div class="sym"><div class="sym-trace"></div></div><div class="legend-label">TRACES</div></div>
                <div class="legend-item"><div class="sym"><div class="sym-origin"></div></div><div class="legend-label">ORIGIN</div></div>
            </div>
        </div>
        <div class="bottom-panel">
            <div class="play-section"><button id="playBtn" class="play-btn" onclick="togglePlay()">▶ START</button></div>
            <div class="slider-section">
                <div style="display: flex; justify-content: space-between;"><span class="label">TIMELINE SEQUENCE</span><span class="label" id="minLabel">0 MIN</span></div>
                <input id="timeSlider" type="range" min="0" max="{INTERP_STEPS-1}" step="5" value="0" oninput="updateTime(this.value)">
            </div>
            <div class="time-box"><span>ELAPSED</span><div id="timeValue">T+000</div><span>MIN</span></div>
        </div>
    </div>
<script>
    let dataCache = {frame_data_json};
    let currentTime = 0;
    let timer = null;
    let gd = document.querySelector('.plotly-graph-div');
    const MAX_STEPS = {INTERP_STEPS-1};

    // Convex Hull Algorithm (Monotone Chain)
    function convexHull(points) {{
        points.sort((a, b) => a[0] == b[0] ? a[1] - b[1] : a[0] - b[0]);
        const lower = [];
        for (let p of points) {{
            while (lower.length >= 2 && cross(lower[lower.length - 2], lower[lower.length - 1], p) <= 0) lower.pop();
            lower.push(p);
        }}
        const upper = [];
        for (let i = points.length - 1; i >= 0; i--) {{
            const p = points[i];
            while (upper.length >= 2 && cross(upper[upper.length - 2], upper[upper.length - 1], p) <= 0) upper.pop();
            upper.push(p);
        }}
        upper.pop(); lower.pop();
        return lower.concat(upper);
    }}
    function cross(o, a, b) {{ return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]); }}

    function updateTime(v) {{
        currentTime = parseInt(v);
        document.getElementById('timeSlider').value = v;
        document.getElementById('minLabel').innerText = v + " MIN";
        document.getElementById('timeValue').innerText = "T+" + v.toString().padStart(3, '0');
        const frame = dataCache[v] || dataCache["0"];
        if(frame) Plotly.restyle(gd, {{ lon: [frame.h_lon, frame.lon], lat: [frame.h_lat, frame.lat] }}, [0, 1]);
    }}

    function togglePlay() {{
        const btn = document.getElementById('playBtn');
        if(!timer) {{
            timer = setInterval(() => {{
                currentTime = (currentTime >= MAX_STEPS) ? 0 : currentTime + 5;
                updateTime(currentTime);
            }}, 80);
            btn.innerText = "⏸ STOP"; btn.classList.add('paused');
        }} else {{
            clearInterval(timer); timer = null;
            btn.innerText = "▶ START"; btn.classList.remove('paused');
        }}
    }}
    
    window.addEventListener('resize', () => Plotly.Plots.resize(gd));
    
    function updateScale() {{
        try {{
            const mapLayout = gd._fullLayout.map;
            if(!mapLayout || !mapLayout.zoom) return;
            const zoom = mapLayout.zoom;
            const lat = mapLayout.center.lat;
            const width = gd._fullLayout.width;
            const metersPerPx = 156543.03392 * Math.cos(lat * Math.PI / 180) / Math.pow(2, zoom);
            let targetMeters = metersPerPx * 100;
            let unit = 'm';
            if(targetMeters >= 1000) {{ targetMeters/=1000; unit='km'; }}
            const magnitude = Math.pow(10, Math.floor(Math.log10(targetMeters)));
            let nice = 1;
            const residual = targetMeters / magnitude;
            if(residual >= 2) nice = 2;
            if(residual >= 5) nice = 5;
            if(residual >= 10) nice = 10;
            const finalVal = nice * magnitude;
            const finalMeters = finalVal * (unit==='km'?1000:1);
            const finalPx = finalMeters / metersPerPx;
            const paperFraction = finalPx / width;
            Plotly.relayout(gd, {{ 'shapes[0].x1': 0.02 + paperFraction, 'annotations[0].text': finalVal + ' ' + unit }});
        }} catch(e) {{ console.log("Scale Error:", e); }}
    }}
    function debounce(func, wait) {{
        let timeout; return function(...args) {{ clearTimeout(timeout); timeout = setTimeout(() => func.apply(this, args), wait); }};
    }}
    const debouncedUpdateScale = debounce(updateScale, 200);

    window.onload = () => setTimeout(() => {{ Plotly.Plots.resize(gd); debouncedUpdateScale(); }}, 1000);
    gd.on('plotly_relayout', function(ed) {{ if(ed && (ed['shapes[0].x1'])) return; debouncedUpdateScale(); }});
    gd.on('plotly_restyle', debouncedUpdateScale);

    // MESSAGE LISTENER
    window.addEventListener('message', function(e) {{
        const payload = e.data;
        if(payload.type === 'updateData') {{
            const rawData = payload.data;
            const origin = payload.origin;
            dataCache = {{}}; // Clear
            const STEPS = rawData.length;
            const LON = 10; const LAT = 9;
            
            for(let t=0; t<STEPS; t+=1) {{
                 let t_lons = []; let t_lats = [];
                 for(let subT=0; subT<=t; subT++) {{
                     for(let m=0; m<rawData[0].length; m++) {{
                         let ln = rawData[subT][m][LON]; let lt = rawData[subT][m][LAT];
                         if(!isNaN(ln) && !isNaN(lt)) {{ t_lons.push(ln); t_lats.push(lt); }}
                     }}
                 }}
                 let h_lon=[], h_lat=[];
                 if(t_lons.length > 2) {{
                     const hull = convexHull(t_lons.map((v, i) => [v, t_lats[i]]));
                     if(hull.length > 0) {{ hull.push(hull[0]); h_lon = hull.map(p => p[0]); h_lat = hull.map(p => p[1]); }}
                 }}
                 if(h_lon.length === 0) {{
                     let cl = origin[1], ct = origin[0];
                     const d = 0.0001;
                     h_lon = [cl, cl+d, cl-d, cl]; h_lat = [ct+d, ct-d, ct-d, ct+d];
                 }}
                 let cur_lons = []; let cur_lats = [];
                 for(let m=0; m<rawData[0].length; m++) {{
                     let ln = rawData[t][m][LON]; let lt = rawData[t][m][LAT];
                     cur_lons.push(isNaN(ln) ? origin[1] : ln); cur_lats.push(isNaN(lt) ? origin[0] : lt);
                 }}
                 dataCache[t] = {{ h_lon: h_lon, h_lat: h_lat, lon: cur_lons, lat: cur_lats }};
            }}
            updateTime(0);
            Plotly.restyle(gd, {{'lon': [[origin[1]]], 'lat': [[origin[0]]]}}, [2]);
            Plotly.relayout(gd, {{'map.center': {{lat: origin[0], lon: origin[1]}}}});
        }}
    }});
</script></body></html>"""
    
    with open("sub_plotly_2d.html", "w", encoding="utf-8") as f:
        f.write(html_content)

def generate_3d_html(data, origin, optimal_trace):
    """Generates the 3D visualization HTML."""
    origin_lat, origin_lon = origin
    
    # Initialize with empty/dummy traces structure so we can use restyle updates
    fig = make_subplots(rows=2, cols=1, row_heights=[0.7, 0.3], specs=[[{"type": "map"}], [{"type": "xy"}]])
    
    colors = ["#ff00ff", "#00ffff", "#ffff00", "#ff0000", "#00ff00", "#0000ff", "#ff7f00", "#7f00ff", "#00ff7f", "#ff007f"]

    # Add Member Traces (Empty Initial)
    dummy_t = [0]
    dummy_v = [0]
    
    for m in range(NUM_MEMBERS):
        color = colors[m % len(colors)]
        # 2D Height Profile (Bottom)
        fig.add_trace(go.Scatter(
            x=dummy_t, y=dummy_v, mode="markers+lines", name=f"Trace {m+1}",
            line=dict(width=1, color=color), marker=dict(size=4, color=color), opacity=0.4,
            visible='legendonly',
            hoverinfo="text"
        ), row=2, col=1)

        # Map Trace (Top)
        fig.add_trace(go.Scattermap(
            lon=dummy_v, lat=dummy_v, mode="markers+lines", name=f"Trace {m+1}",
            line=dict(width=1, color=color), marker=dict(size=5, color=color), opacity=0.4,
            visible='legendonly',
            hoverinfo="text",
            showlegend=False
        ), row=1, col=1)

    # Static Polygons
    # Target Zone 1
    fig.add_trace(go.Scattermap(
        lat=[24.218470, 24.218528, 24.218798, 24.218845, 24.218845, 24.218470, 24.218470],
        lon=[120.617588, 120.617480, 120.617480, 120.617588, 120.618074, 120.618074, 120.617588],
        fill="toself",
        mode="lines+markers",
        fillcolor="rgba(0, 255, 255, 0.4)",
        marker=dict(size=5, color="#00FFFF"),
        line=dict(color="#00FFFF", width=2),
        name="Target Zone 1",
        hoverinfo="skip",
        showlegend=False
    ), row=1, col=1)

    # Target Zone 2
    fig.add_trace(go.Scattermap(
        lat=[24.218247, 24.218247, 24.217954, 24.217815, 24.217815, 24.217954, 24.218247],
        lon=[120.619599, 120.620373, 120.620373, 120.620262, 120.619880, 120.619599, 120.619599],
        fill="toself",
        mode="lines+markers",
        fillcolor="rgba(0, 255, 255, 0.4)",
        marker=dict(size=5, color="#00FFFF"),
        line=dict(color="#00FFFF", width=2),
        name="Target Zone 2",
        hoverinfo="skip",
        showlegend=False
    ), row=1, col=1)

    # Uncertainty Band - Height (Row 2)
    fig.add_trace(go.Scatter(
        x=dummy_t, y=dummy_v, fill='toself', fillcolor='rgba(255, 0, 0, 0.2)',
        line=dict(width=0), hoverinfo="skip", visible='legendonly', name="Uncertainty Band (Height)"
    ), row=2, col=1)

    # Uncertainty Band - Map (Row 1)
    fig.add_trace(go.Scattermap(
        lon=dummy_v, lat=dummy_v, mode="lines", fill='toself', fillcolor='rgba(255, 0, 0, 0.2)',
        line=dict(color='red', width=1), hoverinfo="skip", visible='legendonly', name="Impact Probability Zone"
    ), row=1, col=1)

    # Optimal Trace - Height
    fig.add_trace(go.Scatter(
        x=dummy_t, y=dummy_v, mode="markers+lines", name="Optimal Trace",
        line=dict(width=1, color="#a10000"), marker=dict(size=10, color="#a10000"), visible='legendonly',
        hoverinfo="text"
    ), row=2, col=1)

    # Optimal Trace - Map
    fig.add_trace(go.Scattermap(
        lon=dummy_v, lat=dummy_v, mode="markers+lines", name="Optimal Trace",
        line=dict(width=1, color="#a10000"), marker=dict(size=20, color="#a10000"), visible='legendonly',
        hoverinfo="text"
    ), row=1, col=1)

    fig.update_layout(template="plotly_dark", margin=dict(l=60, r=20, t=40, b=60),
        hovermode="closest", showlegend=False, autosize=True,
        paper_bgcolor="#050505", plot_bgcolor="#050505")
        
    fig.update_layout(
        map=dict(style="open-street-map", center=dict(lat=origin_lat, lon=origin_lon), zoom=10),
        shapes=[dict(type="line", xref="paper", yref="paper", x0=0.02, y0=0.45, x1=0.12, y1=0.45, line=dict(color="#000000", width=2))],
        annotations=[dict(xref="paper", yref="paper", x=0.02, y=0.465, text="Scale", showarrow=False, font=dict(color="#000000", size=12, family="Consolas"), xanchor="left")]
    )
    
    fig.update_xaxes(title="ELAPSED TIME (MIN)", range=[0, 720], row=2, col=1, gridcolor='#222', title_font=dict(size=14, family="Consolas", color="#eee"))
    fig.update_yaxes(title="ALTITUDE (M)", autorange=True, row=2, col=1, gridcolor='#222', title_font=dict(size=14, family="Consolas", color="#eee"))

    html_frag = fig.to_html(include_plotlyjs='cdn', full_html=False)
    
    html_content = f"""
<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
    :root {{ --accent: #00f3ff; --bg: #050505; --panel: #111; --text: #eee; --border: #333; }}
    body, html {{ margin:0; padding:0; height:100vh; width:100vw; overflow:hidden; background:var(--bg); font-family:'Segoe UI', sans-serif; }}
    .master {{ display:flex; width:100vw; height:100vh; }}
    .chart {{ flex:1; position:relative; overflow:hidden; }}
    .chart > div {{ width:100% !important; height:100% !important; }}
    
    .side {{ 
        width:240px; background:var(--panel); border-left:1px solid var(--border); display:flex; flex-direction:column; 
        box-shadow: -5px 0 20px rgba(0,0,0,0.5); z-index: 10;
    }}
    .side-h {{ 
        padding:20px; color:var(--accent); font-weight:bold; border-bottom:1px solid var(--border); 
        font-size:12px; font-family: 'Consolas', monospace; letter-spacing: 1px;
        background: linear-gradient(90deg, rgba(0, 243, 255, 0.05), transparent);
        border-left: 2px solid var(--accent);
        text-align: center;
    }}
    .side-b {{ padding:20px; overflow-y:auto; flex:1; }}
    
    .avg-btn {{ 
        width:100%; padding:15px; margin-bottom:10px; 
        background:transparent; color:#fff; 
        border:1px solid var(--accent); 
        font-family: 'Consolas', monospace; font-size: 11px; font-weight: bold; cursor:pointer; 
        transition: 0.2s; text-transform: uppercase;
    }}
    .avg-btn:hover {{ background: rgba(0, 243, 255, 0.1); box-shadow: 0 0 10px rgba(0, 243, 255, 0.2); }}
    .avg-btn.off {{ color:#555; border-color:#333; background:transparent; box-shadow: none; }}
    
    .lbl {{ font-size:10px; color:#666; margin-bottom:8px; font-weight:bold; font-family: 'Consolas', monospace; letter-spacing: 1px; }}
    
    .btn-group {{ display:flex; gap:5px; margin-bottom:15px; }}
    .sub-btn {{ 
        flex:1; padding:8px; background:#1a1a1a; border:1px solid #333; color:#888; 
        font-size:10px; cursor:pointer; font-family:'Consolas', monospace; transition: all 0.2s;
    }}
    .sub-btn:hover {{ border-color: #666; color: #fff; }}
    .sub-btn:active {{ background: #222; }}
    
    .m-grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:5px; }}
    .m-btn {{ 
        font-size:10px; padding:6px 0; background:#080808; color:#444; border:1px solid #222; 
        cursor:pointer; transition:0.2s; font-family: 'Consolas', monospace;
    }}
    .m-btn:hover {{ border-color: #444; color: #888; }}
    .m-btn.active {{ 
        background:rgba(0,255,204,0.1); color:var(--accent); border-color:var(--accent); 
        box-shadow: 0 0 5px rgba(0,255,204,0.1); 
    }}
    
</style></head>
<body><div class="master">
    <div class="chart">
        {html_frag}
    </div>
    <div class="side"><div class="side-h">CONTROL PANEL</div><div class="side-b">
        <button id="avgBtn" class="avg-btn off" onclick="toggleAvg()">OPTIMAL TRACE</button>
        <button id="bandBtn" class="avg-btn off" onclick="toggleBand()">UNCERTAINTY BAND</button>
        
        <div class="lbl">MEMBER SELECTION</div>
        <div class="btn-group"><button class="sub-btn" onclick="allSelect(true)">Select All</button><button class="sub-btn" onclick="allSelect(false)">Deselect All</button></div>
        <div class="m-grid" id="mGrid"></div>
    </div></div>
</div><script>
    const gd = document.querySelector('.plotly-graph-div');
    const mGrid = document.getElementById('mGrid');
   
    // Dynamic Button Generation
    for(let i=1; i<={NUM_MEMBERS}; i++){{
        let b = document.createElement('button'); 
        b.className='m-btn'; b.innerText=i;
        b.onclick=()=>{{ 
            let act=b.classList.toggle('active'); 
            // 2 Traces per member (Row 1 and Row 2)
            Plotly.restyle(gd, {{visible:act?true:'legendonly'}}, [(i-1)*2, (i-1)*2+1]); 
        }};
        mGrid.appendChild(b);
    }}

    function allSelect(v) {{
        document.querySelectorAll('.m-btn').forEach(b => v ? b.classList.add('active') : b.classList.remove('active'));
        let indices = Array.from({{length: {NUM_MEMBERS}*2}}, (_, i) => i);
        Plotly.restyle(gd, {{visible: v ? true : 'legendonly'}}, indices);
    }}

    function toggleAvg() {{
        let btn = document.getElementById('avgBtn');
        btn.classList.toggle('off');
        let on = !btn.classList.contains('off');
        const total = gd.data.length;
        Plotly.restyle(gd, {{visible: on}}, [total-2, total-1]); // Optimal Traces
    }}

    function toggleBand() {{
        let btn = document.getElementById('bandBtn');
        btn.classList.toggle('off');
        let on = !btn.classList.contains('off');
        const total = gd.data.length;
        Plotly.restyle(gd, {{visible: on}}, [total-4, total-3]); // Uncertainty Bands
    }}

    window.addEventListener('resize', ()=>Plotly.Plots.resize(gd));
    
    function updateScale() {{
        try {{
            const mapLayout = gd._fullLayout.map;
            if(!mapLayout || !mapLayout.zoom) return;
            const zoom = mapLayout.zoom;
            const lat = mapLayout.center.lat;
            const width = gd._fullLayout.width;
            const metersPerPx = 156543.03392 * Math.cos(lat * Math.PI / 180) / Math.pow(2, zoom);
            let targetMeters = metersPerPx * 100;
            let unit = 'm';
            if(targetMeters >= 1000) {{ targetMeters/=1000; unit='km'; }}
            const magnitude = Math.pow(10, Math.floor(Math.log10(targetMeters)));
            let nice = 1;
            const residual = targetMeters / magnitude;
            if(residual >= 2) nice = 2;
            if(residual >= 5) nice = 5;
            if(residual >= 10) nice = 10;
            const finalVal = nice * magnitude;
            const finalMeters = finalVal * (unit==='km'?1000:1);
            const finalPx = finalMeters / metersPerPx;
            const paperFraction = finalPx / width;
            Plotly.relayout(gd, {{ 'shapes[0].x1': 0.02 + paperFraction, 'annotations[0].text': finalVal + ' ' + unit }});
        }} catch(e) {{ console.log("Scale Error 3D:", e); }}
    }}
    function debounce(func, wait) {{
        let timeout; return function(...args) {{ clearTimeout(timeout); timeout = setTimeout(() => func.apply(this, args), wait); }};
    }}
    const debouncedUpdateScale = debounce(updateScale, 200);
    setTimeout(() => {{ Plotly.Plots.resize(gd); debouncedUpdateScale(); }}, 1000);
    gd.on('plotly_relayout', function(ed) {{ if(ed && (ed['shapes[0].x1'])) return; debouncedUpdateScale(); }});
    gd.on('plotly_restyle', debouncedUpdateScale);

    // DATA UPDATE LISTENER
    window.addEventListener('message', function(e) {{
        const payload = e.data;
        if(payload.type === 'updateData') {{
            const rawData = payload.data; // [Time][Member][Var]
            const optimal = payload.optimal;
            
            const LON=10, LAT=9, ALT=11;
            const times = Array.from({{length: rawData.length}}, (_,i)=>i);
            
            // 1. Update Member Traces
            // Structure: Trace 0 & 1 -> Member 1, Trace 2 & 3 -> Member 2...
            // 1. Update Member Traces
            // Structure: Trace 0 & 1 -> Member 1, Trace 2 & 3 -> Member 2...
            for(let m=0; m<{NUM_MEMBERS}; m++) {{
                let traceLons = [];
                let traceLats = [];
                let traceAlts = [];
                let traceText = [];
                
                for(let t=0; t<rawData.length; t++) {{
                    let ln = rawData[t][m][LON];
                    let lt = rawData[t][m][LAT];
                    let al = rawData[t][m][ALT];
                    traceLons.push(ln);
                    traceLats.push(lt);
                    traceAlts.push(al);
                    // Explicit Hover Text
                    traceText.push(`<b>Member ${{m+1}}</b><br>Lon: ${{ln.toFixed(4)}}<br>Lat: ${{lt.toFixed(4)}}<br>Alt: ${{al.toFixed(1)}} m<br>Time: ${{t}} min`);
                }}
                
                // Update Row 2 (Height) - Index m*2
                Plotly.restyle(gd, {{ x: [times], y: [traceAlts], hovertext: [traceText] }}, [m*2]);
                
                // Update Row 1 (Map) - Index m*2+1
                Plotly.restyle(gd, {{ lon: [traceLons], lat: [traceLats], hovertext: [traceText] }}, [m*2+1]);
            }}
            
            // 2. Update Optimal Traces
            // Indices: Total-1 (Map Opt), Total-2 (Height Opt), Total-3 (Map Band), Total-4 (Height Band)
            const T = gd.data.length;
            
            // Simple Optimal Trace Update
            let optText = optimal.alts.map((a, i) => `<b>Optimal Trace</b><br>Lon: ${{optimal.lons[i].toFixed(4)}}<br>Lat: ${{optimal.lats[i].toFixed(4)}}<br>Alt: ${{a.toFixed(1)}} m<br>Time: ${{i}} min`);
            Plotly.restyle(gd, {{ x: [times], y: [optimal.alts], hovertext: [optText] }}, [T-2]); // Height
            Plotly.restyle(gd, {{ lon: [optimal.lons], lat: [optimal.lats], hovertext: [optText] }}, [T-1]); // Map
            
            // Ribbon / Uncertainty - Use calculated ribbon data
            const ribbon = payload.ribbon;
            
            // Auto-enable Optimal Trace & Ribbon (Force Visibility)
            // Indices: T-4 to T-1
            // 1. Update visual state of buttons
            const btn = document.getElementById('avgBtn');
            if(btn && btn.classList.contains('off')) btn.classList.remove('off');
            const bandBtn = document.getElementById('bandBtn');
            if(bandBtn && bandBtn.classList.contains('off')) bandBtn.classList.remove('off');
            
            // 2. Prepare update object (Force visible: true)
            const visUpdate = {{ visible: true }};

            if (ribbon) {{
               // Height Band
               const xRev = times.slice().reverse();
               const xFull = times.concat(xRev);
               const yFull = ribbon.hUpper.concat(ribbon.hLower.slice().reverse());
               Plotly.restyle(gd, {{ x: [xFull], y: [yFull], visible: true }}, [T-4]);

               // Map Band
               Plotly.restyle(gd, {{ lon: [ribbon.lons], lat: [ribbon.lats], visible: true }}, [T-3]);
            }} else {{
               // Fallback
               Plotly.restyle(gd, {{ x: [times.concat(times.reverse())], y: [optimal.alts.concat(optimal.alts.map(x=>x))], visible: true }}, [T-4]);
               Plotly.restyle(gd, {{ lon: [optimal.lons.concat(optimal.lons.slice().reverse())], lat: [optimal.lats.concat(optimal.lats.slice().reverse())], visible: true }}, [T-3]);
            }}
            
            // Ensure Optimal Traces are also visible
            Plotly.restyle(gd, {{ visible: true }}, [T-2, T-1]); 
            
            // Re-center
             Plotly.relayout(gd, {{'map.center': {{lat: optimal.lats[0], lon: optimal.lons[0]}}}});
        }}
    }});
</script></body></html>"""
    
    with open("sub_plotly_3d.html", "w", encoding="utf-8") as f:
        f.write(html_content)

def generate_dashboard():
    # Read and encode logo
    # Assuming the logo is in the same directory as the script
    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Tsmc.svg.png')
    logo_b64 = ""
    try:
        with open(logo_path, "rb") as image_file:
            logo_b64 = "data:image/png;base64," + base64.b64encode(image_file.read()).decode('utf-8')
    except Exception:
        # Fallback to online logo if local fails
        logo_b64 = "https://upload.wikimedia.org/wikipedia/commons/2/29/TSMC_Logo.svg"

    dashboard = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8"><title>TSMC MONITOR SYSTEM</title>
    <style>
        :root {{
            --bg-dark: #050505;
            --panel-bg: #111111;
            --border-color: #333333;
            --accent-color: #00f3ff;
            --text-main: #e0e0e0;
            --text-muted: #666666;
            --font-tech: 'Segoe UI', 'Roboto', Helvetica, Arial, sans-serif;
            --font-mono: 'Consolas', 'Monaco', monospace;
        }}
        * {{ box-sizing: border-box; }}
        html,body {{ margin:0; height:100%; background: var(--bg-dark); font-family: var(--font-tech); overflow:hidden; color: var(--text-main); }}
        .main {{ display: flex; height: 100vh; width: 100vw; }}
        
        .sidebar {{
            width: 280px; background: var(--panel-bg); border-right: 1px solid var(--border-color);
            display: flex; flex-direction: column; z-index: 100; box-shadow: 2px 0 20px rgba(0,0,0,0.5);
        }}
        
        .brand {{
            padding: 25px 20px; border-bottom: 1px solid var(--border-color); margin-bottom: 10px;
            display: flex; align-items: center; gap: 15px;
            background: linear-gradient(180deg, rgba(20,20,20,1) 0%, rgba(10,10,10,1) 100%);
        }}
        .brand-logo {{ width: 42px; height: auto; filter: drop-shadow(0 0 2px rgba(255,255,255,0.1)); }}
        .brand-text {{ overflow: hidden; display: flex; flex-direction: column; justify-content: center; }}
        .title {{ font-size: 14px; font-weight: 700; color: #ffffff; letter-spacing: 0.5px; line-height: 1.2; white-space: nowrap; }}
        .sub {{ font-family: var(--font-mono); font-size: 9px; color: var(--accent-color); margin-top: 4px; letter-spacing: 1px; text-transform: uppercase; opacity: 0.8; }}
        
        .menu-list {{ flex: 1; padding: 10px 0; display: flex; flex-direction: column; gap: 2px; }}
        .menu-btn {{
            background: transparent; border: none; border-left: 3px solid transparent; color: var(--text-muted);
            padding: 15px 24px; cursor: pointer; width: 100%; text-align: left;
            display: flex; align-items: center; justify-content: space-between;
            font-family: var(--font-tech); font-size: 13px; letter-spacing: 0.5px; transition: all 0.2s ease;
        }}
        .menu-btn:hover {{ background: rgba(255,255,255,0.03); color: #fff; }}
        .menu-btn.active {{
            background: rgba(0, 243, 255, 0.05); color: var(--accent-color); border-left-color: var(--accent-color);
            font-weight: 600; box-shadow: inset 10px 0 20px -10px rgba(0, 243, 255, 0.1);
        }}
        
        .status-bar {{
            padding: 15px 20px; border-top: 1px solid var(--border-color); background: #080808;
            font-family: var(--font-mono); font-size: 10px; color: var(--text-muted);
            display: flex; align-items: center; justify-content: space-between;
        }}
        .status-indicator {{ display: flex; align-items: center; gap: 8px; color: var(--accent-color); font-weight: bold; }}
        .status-dot {{ width: 6px; height: 6px; background: var(--accent-color); border-radius: 50%; box-shadow: 0 0 5px var(--accent-color); animation: pulse 2s infinite; }}
        .clock-container {{ text-align: right; display: flex; flex-direction: column; align-items: flex-end; }}
        .clock-time {{ color: #fff; font-size: 14px; font-weight: bold; letter-spacing: 1px; }}
        .clock-date {{ color: var(--accent-color); font-size: 11px; font-weight: 600; margin-top: 3px; letter-spacing: 0.5px; opacity: 0.9; }}
        @keyframes pulse {{ 0% {{ opacity: 0.5; }} 50% {{ opacity: 1; }} 100% {{ opacity: 0.5; }} }}
        
        .control-panel {{ padding: 20px; border-top: 1px solid var(--border-color); display: flex; flex-direction: column; gap: 15px; }}
        .control-group {{ display: flex; flex-direction: column; gap: 6px; }}
        .control-label {{ font-size: 11px; color: var(--text-muted); font-weight: 600; letter-spacing: 0.5px; }}
        .control-select {{
            background: #1a1a1a; border: 1px solid #333; color: #fff;
            padding: 8px 12px; font-family: var(--font-tech); font-size: 12px;
            border-radius: 4px; outline: none; transition: border-color 0.2s;
        }}
        .control-select:focus {{ border-color: var(--accent-color); }}
        
        input[type="date"]::-webkit-calendar-picker-indicator {{
            filter: invert(1); cursor: pointer; opacity: 0.6; transition: 0.2s;
        }}
        input[type="date"]::-webkit-calendar-picker-indicator:hover {{ opacity: 1; transform: scale(1.1); }}
        
        .radio-group {{ display: flex; gap: 15px; }}
        .radio-item {{ display: flex; align-items: center; gap: 6px; cursor: pointer; }}
        .radio-item input {{ margin: 0; accent-color: var(--accent-color); }}
        .radio-item span {{ font-size: 12px; color: #ccc; }}
        
        .start-btn {{
            background: rgba(0, 243, 255, 0.1); border: 1px solid var(--accent-color);
            color: var(--accent-color); padding: 10px;
            font-family: var(--font-tech); font-weight: 700; font-size: 12px;
            letter-spacing: 1px; cursor: pointer; transition: all 0.2s;
            margin-top: 5px; text-align: center;
        }}
        .start-btn:hover {{ background: var(--accent-color); color: #000; box-shadow: 0 0 15px rgba(0, 243, 255, 0.4); }}
        
        .content {{ flex: 1; position: relative; background: #000; box-shadow: inset 5px 0 20px rgba(0,0,0,1); }}
        iframe {{ width: 100%; height: 100%; border: none; display: none; }}
        iframe.active {{ display: block; }}
        
    </style>
</head>
<body>
    <div class="main">
        <div class="sidebar">
            <div class="brand">
                <img src="{logo_b64}" class="brand-logo" alt="TSMC">
                <div class="brand-text">
                    <div class="title">TSMC AIR POLLUTION</div>
                    <div class="title">MONITOR SYSTEM</div>
                    <div class="sub">DISPERSION ANALYTICS V0.0.6</div>
                </div>
            </div>
            
            <div class="menu-list">
                <button class="menu-btn active" onclick="go('3d',this)">TRAJECTORY ANALYSIS</button>
                <button class="menu-btn" onclick="go('2d',this)">IMPACT ANALYSIS</button>
            </div>
            
            <div class="control-panel">
                <div class="control-group">
                    <div class="control-label">START DATE</div>
                    <input type="date" id="simDate" class="control-select">
                </div>
                
                <div class="control-group">
                    <div class="control-label">START HOUR (00-23)</div>
                    <select id="simHour" class="control-select">
                        <!-- JS generated options -->
                    </select>
                </div>

                <div class="control-group">
                    <div class="control-label">DURATION</div>
                    <select id="simDuration" class="control-select">
                        <option value="6">6 Hours</option>
                        <option value="12" selected>12 Hours</option>
                        <option value="18">18 Hours</option>
                        <option value="24">24 Hours</option>
                    </select>
                </div>
                
                <div class="control-group">
                    <div class="control-label">TRAJECTORY DIRECTION</div>
                    <div class="radio-group">
                        <label class="radio-item"><input type="radio" name="direction" value="Forward"><span>Forward</span></label>
                        <label class="radio-item"><input type="radio" name="direction" value="Backward" checked><span>Backward</span></label>
                    </div>
                </div>
                
                <button class="start-btn" onclick="startSimulation()">START SIMULATION</button>
            </div>
            
            <div class="status-bar">
                <div class="clock-container">
                    <div id="clockTime" class="clock-time">00:00:00</div>
                    <div id="clockDate" class="clock-date">YYYY-MM-DD</div>
                </div>
                <div class="status-indicator"><div class="status-dot"></div> ACTIVE</div>
            </div>
        </div>
        
        <div class="content">
            <iframe id="f2d" src="sub_plotly_2d.html"></iframe>
            <iframe id="f3d" src="sub_plotly_3d.html" class="active"></iframe>
        </div>
    </div>
    <script>
        // Init Hour Options
        const sel = document.getElementById('simHour');
        for(let i=0; i<24; i++) {{
            let opt = document.createElement('option');
            let val = i.toString().padStart(2,'0');
            opt.value = val; opt.innerText = val + ":00";
            if(i===8) opt.selected=true;
            sel.appendChild(opt);
        }}
        
        // Default Date
        document.getElementById('simDate').value = new Date().toISOString().split('T')[0];
        
        function go(t,b){{
            document.querySelectorAll('.menu-btn').forEach(x=>x.classList.remove('active'));
            b.classList.add('active');
            document.querySelectorAll('iframe').forEach(f=>f.classList.remove('active'));
            document.getElementById(t==='2d'?'f2d':'f3d').classList.add('active');
        }}
        
        function updateClock() {{
            const now = new Date();
            document.getElementById('clockTime').innerText = now.toLocaleTimeString('en-US', {{ hour12: false }});
            document.getElementById('clockDate').innerText = now.toLocaleDateString('en-US', {{ year: 'numeric', month: '2-digit', day: '2-digit' }});
        }}
        setInterval(updateClock, 1000); updateClock();

        // SIMULATION LOGIC
        const NUM_TIME_STEPS = {NUM_TIME_STEPS};
        const NUM_MEMBERS = {NUM_MEMBERS};
        const NUM_VARS = {NUM_VARS};
        const INTERP_STEPS = {INTERP_STEPS};
        const LAT_IDX = {LAT_IDX};
        const LON_IDX = {LON_IDX};
        const ALT_IDX = {ALT_IDX};

        async function startSimulation() {{
            const dateVal = document.getElementById('simDate').value; 
            const hourVal = document.getElementById('simHour').value;
            const direction = document.querySelector('input[name="direction"]:checked').value;
            
            if(!dateVal) {{ alert("Please select a date."); return; }}
            
            const filename = `tdump.${{dateVal}}-${{hourVal}}00.${{direction}}.txt`;
            const path = `database/${{filename}}`;
            
            console.log("Fetching:", path);
            try {{
                const response = await fetch(path);
                if (!response.ok) throw new Error("File not found");
                const text = await response.text();
                processAndSend(text);
                alert("Simulation Loaded: " + filename);
            }} catch (e) {{
                alert("Startup Failed: " + e.message); 
            }}
        }}

        function processAndSend(text) {{
            const lines = text.trim().split('\\n');
            
            // Parse Origin from Header
            let originFixed = null;
            try {{
                const headerLine = lines[0].trim().split(/\\s+/);
                const numMeteo = parseInt(headerLine[0]);
                // Header structure:
                // Line 0: Num Meteo Files (N) ...
                // Line 1 to N: Meteo File Names
                // Line N+1: Num Starting Locations / Members
                // Line N+2: First Starting Location (We take this as Origin)
                const targetIdx = numMeteo + 2;
                if (lines.length > targetIdx) {{
                    const mParts = lines[targetIdx].trim().split(/\\s+/);
                    // Format: YY MM DD HH LAT LON ...
                    // Index:  0  1  2  3  4   5
                    if (mParts.length >= 6) {{
                        const lat = parseFloat(mParts[4]);
                        const lon = parseFloat(mParts[5]);
                        if (!isNaN(lat) && !isNaN(lon)) {{
                            originFixed = [lat, lon];
                            console.log("Parsed Origin:", originFixed);
                        }}
                    }}
                }}
            }} catch(e) {{ 
                console.log("Origin header parse error:", e); 
            }}


            const dataLines = lines.slice(40); // Ignore header
            
            // Parse flat numbers
            let flatData = [];
            for(let line of dataLines) {{
                const parts = line.trim().split(/\\s+/);
                for(let p of parts) if(p) flatData.push(parseFloat(p));
            }}
            
            // Reshape [Time][Member][Var]
            // Note: If input has fewer steps than expected, we handle gracefully?
            // Assuming strict format for now.
            let rawData = [];
            let ptr = 0;
            for(let t=0; t<NUM_TIME_STEPS; t++) {{
                let members = [];
                for(let m=0; m<NUM_MEMBERS; m++) {{
                    let vars = [];
                    for(let v=0; v<NUM_VARS; v++) {{
                        vars.push(flatData[ptr++] || 0);
                    }}
                    members.push(vars);
                }}
                rawData.push(members);
            }}
            
            // Normalize Alt for t>0 (Python parity)
            for(let t=1; t<NUM_TIME_STEPS; t++) {{
                for(let m=0; m<NUM_MEMBERS; m++) {{
                    rawData[t][m][ALT_IDX] /= 10.0;
                }}
            }}
            
            const interpData = interpolateData(rawData);
            
            // Origin strategy: Use header origin if available, else fallback to mean
            let originFinal = originFixed;
            if (!originFinal) {{
                let sumLat=0, sumLon=0;
                for(let m=0; m<NUM_MEMBERS; m++) {{ sumLat += interpData[0][m][LAT_IDX]; sumLon += interpData[0][m][LON_IDX]; }}
                originFinal = [sumLat/NUM_MEMBERS, sumLon/NUM_MEMBERS];
            }}
            
            const optimalTrace = calculateOptimalTrace(interpData);
            
            // Calculate Uncertainty Polygon (Ribbon)
            const ribbon = calculateRibbonPolygon(optimalTrace.lons, optimalTrace.lats, optimalTrace.std_dist);
            
            // Flatten ribbon for Plotly shape (lon, lat)
            const ribbonLons = ribbon.poly_lons;
            const ribbonLats = ribbon.poly_lats;

            // Height Ribbon (Upper/Lower)
            const hUpper = optimalTrace.alts.map((a, i) => a + optimalTrace.std_alt[i]);
            const hLower = optimalTrace.alts.map((a, i) => a - optimalTrace.std_alt[i]);
            
            const payload = {{ 
                type: 'updateData', 
                data: interpData, 
                origin: originFinal, 
                optimal: optimalTrace,
                ribbon: {{ lons: ribbonLons, lats: ribbonLats, hUpper: hUpper, hLower: hLower }}
            }};

            const f2d = document.getElementById('f2d');
            const f3d = document.getElementById('f3d');
            if(f2d && f2d.contentWindow) f2d.contentWindow.postMessage(payload, '*');
            if(f3d && f3d.contentWindow) f3d.contentWindow.postMessage(payload, '*');
        }}

        function calculateRibbonPolygon(pathLons, pathLats, stdDevs) {{
            let leftLons = [], leftLats = [];
            let rightLons = [], rightLats = [];
            
            // Smoothing window size (approx 3% -> 6% of points for stronger effect)
            const SMOOTH_WIN = 50;
            const SIGMA_SCALE = 0.1;

            for(let i=0; i<pathLons.length; i++) {{
                // Tangent vector
                let dx, dy;
                if (i === 0) {{
                    dx = pathLons[i+1] - pathLons[i];
                    dy = pathLats[i+1] - pathLats[i];
                }} else if (i === pathLons.length - 1) {{
                    dx = pathLons[i] - pathLons[i-1];
                    dy = pathLats[i] - pathLats[i-1];
                }} else {{
                    dx = pathLons[i+1] - pathLons[i-1];
                    dy = pathLats[i+1] - pathLats[i-1];
                }}
                
                // Normal vector (perpendicular)
                const len = Math.sqrt(dx*dx + dy*dy);
                let nx=0, ny=0;
                if(len > 0) {{
                     nx = -dy / len;
                     ny = dx / len;
                }}
                
                const sigma = (stdDevs[i] || 0.001) * SIGMA_SCALE; 
                
                leftLons.push(pathLons[i] + nx * sigma);
                leftLats.push(pathLats[i] + ny * sigma);
                
                rightLons.push(pathLons[i] - nx * sigma);
                rightLats.push(pathLats[i] - ny * sigma);
            }}
            
            // Smooth the edges
            const sLeftLons = smoothArray(leftLons, SMOOTH_WIN);
            const sLeftLats = smoothArray(leftLats, SMOOTH_WIN);
            const sRightLons = smoothArray(rightLons, SMOOTH_WIN);
            const sRightLats = smoothArray(rightLats, SMOOTH_WIN);

            // Force endpoints to match original (Pin to Origin/Destination)
            if(sLeftLons.length > 0) {{
                sLeftLons[0] = leftLons[0];
                sLeftLons[sLeftLons.length-1] = leftLons[leftLons.length-1];
                
                sLeftLats[0] = leftLats[0];
                sLeftLats[sLeftLats.length-1] = leftLats[leftLats.length-1];
                
                sRightLons[0] = rightLons[0];
                sRightLons[sRightLons.length-1] = rightLons[rightLons.length-1];
                
                sRightLats[0] = rightLats[0];
                sRightLats[sRightLats.length-1] = rightLats[rightLats.length-1];
            }}

            // Close loop: Left + Right(Reversed)
            return {{
                poly_lons: sLeftLons.concat(sRightLons.reverse()),
                poly_lats: sLeftLats.concat(sRightLats.reverse())
            }};
        }}

        function smoothArray(values, windowSize) {{
            if (values.length < windowSize) return values;
            const result = [];
            const half = Math.floor(windowSize / 2);
            for (let i = 0; i < values.length; i++) {{
                let sum = 0;
                let count = 0;
                const start = Math.max(0, i - half);
                const end = Math.min(values.length - 1, i + half);
                for (let j = start; j <= end; j++) {{
                    sum += values[j];
                    count++;
                }}
                result.push(sum / count);
            }}
            return result;
        }}

        function interpolateData(data) {{
            const out = [];
            const stepsPerSegment = (INTERP_STEPS - 1) / (NUM_TIME_STEPS - 1);
            for(let i=0; i<INTERP_STEPS; i++) {{
                let tExact = i / stepsPerSegment;
                let t0 = Math.floor(tExact);
                let t1 = Math.min(t0 + 1, NUM_TIME_STEPS - 1);
                let factor = tExact - t0;
                let stepMembers = [];
                for(let m=0; m<NUM_MEMBERS; m++) {{
                    let memberVars = [];
                    for(let v=0; v<NUM_VARS; v++) {{
                        let val = data[t0][m][v] + (data[t1][m][v] - data[t0][m][v]) * factor;
                        memberVars.push(val);
                    }}
                    stepMembers.push(memberVars);
                }}
                out.push(stepMembers);
            }}
            return out;
        }}

        function calculateOptimalTrace(data) {{
            let optLons = [], optLats = [], optAlts = [];
            let stdDist = [], stdAlt = [];

            for(let t=0; t<data.length; t++) {{
                let lons=[], lats=[], alts=[];
                for(let m=0; m<NUM_MEMBERS; m++) {{
                    lons.push(data[t][m][LON_IDX]); lats.push(data[t][m][LAT_IDX]); alts.push(data[t][m][ALT_IDX]);
                }}
                let cLon = lons.reduce((a,b)=>a+b,0)/NUM_MEMBERS;
                let cLat = lats.reduce((a,b)=>a+b,0)/NUM_MEMBERS;
                let dists = lons.map((l, i) => Math.sqrt(Math.pow(l-cLon,2) + Math.pow(lats[i]-cLat, 2)));
                let indices = Array.from({{length: NUM_MEMBERS}}, (_, i) => i);
                indices.sort((a, b) => dists[a] - dists[b]);
                
                // Optimal = Mean of Best 25
                let valid = indices.slice(0, 25); 
                let avgLon=0, avgLat=0, avgAlt=0;
                for(let idx of valid) {{ avgLon += lons[idx]; avgLat += lats[idx]; avgAlt += alts[idx]; }}
                let finalLon = avgLon/valid.length;
                let finalLat = avgLat/valid.length;
                let finalAlt = avgAlt/valid.length;
                
                optLons.push(finalLon); optLats.push(finalLat); optAlts.push(finalAlt);

                // Standard Deviation Calculation (All Members)
                // Distance from Optimal Point
                let sumSqDist = 0;
                let sumSqAlt = 0;
                for(let i=0; i<NUM_MEMBERS; i++) {{
                    let d = Math.sqrt(Math.pow(lons[i]-finalLon, 2) + Math.pow(lats[i]-finalLat, 2));
                    sumSqDist += d*d;
                    let dA = alts[i] - finalAlt;
                    sumSqAlt += dA*dA;
                }}
                stdDist.push(Math.sqrt(sumSqDist / NUM_MEMBERS));
                stdAlt.push(Math.sqrt(sumSqAlt / NUM_MEMBERS));
            }}
            return {{ lons: optLons, lats: optLats, alts: optAlts, std_dist: stdDist, std_alt: stdAlt }};
        }}
    </script>
</body></html>"""
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(dashboard)
    
    webbrowser.open(f"file://{{os.path.abspath('index.html')}}")


def main():
    # Detect file path relative to script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Default fallback file
    file_path = os.path.join(script_dir, 'output.txt')
    
    # We create empty/default data just to generate the initial HTMLs
    # The actual data will be loaded via JS
    
    # Dummy data for initialization
    # If output.txt doesn't exist, we might fail here.
    # But we want to generate the HTMLs even without data.
    
    print("Initializing Views...")
    # Origin default
    origin = (24.0, 120.5) 
    
    # Generate empty/template HTMLs
    generate_2d_html(None, origin)
    generate_3d_html(None, origin, None)
    
    print("Launching Dashboard...")
    generate_dashboard()

if __name__ == "__main__":
    main()
