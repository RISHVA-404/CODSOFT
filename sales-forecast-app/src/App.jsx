import { useState, useRef } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, ReferenceLine, ComposedChart,
  Area, Scatter,
} from "recharts";

// ─── MATH ENGINE ─────────────────────────────────────────────────────────────
function leastSquares(xs, ys) {
  const n = xs.length;
  const sumX  = xs.reduce((a, b) => a + b, 0);
  const sumY  = ys.reduce((a, b) => a + b, 0);
  const sumXY = xs.reduce((acc, x, i) => acc + x * ys[i], 0);
  const sumX2 = xs.reduce((acc, x) => acc + x * x, 0);
  const m = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
  const c = (sumY - m * sumX) / n;
  return { m, c };
}

function calcMetrics(xs, ys, m, c) {
  const preds = xs.map(x => m * x + c);
  const meanY = ys.reduce((a, b) => a + b, 0) / ys.length;
  const mse   = preds.reduce((acc, p, i) => acc + Math.pow(p - ys[i], 2), 0) / ys.length;
  const rmse  = Math.sqrt(mse);
  const ssTot = ys.reduce((acc, y) => acc + Math.pow(y - meanY, 2), 0);
  const ssRes = preds.reduce((acc, p, i) => acc + Math.pow(ys[i] - p, 2), 0);
  const r2    = 1 - ssRes / ssTot;
  const mae   = preds.reduce((acc, p, i) => acc + Math.abs(p - ys[i]), 0) / ys.length;
  return { mse, rmse, r2, mae, preds };
}

// ─── CONSTANTS ────────────────────────────────────────────────────────────────
const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];

const PRODUCT_COLORS = ["#00f5d4","#f72585","#ffd60a","#7b2fff","#ff6b35","#06d6a0"];

// E-Commerce realistic product categories with seasonal-ish sales data
const SAMPLE_PRODUCTS = [
  { name: "Electronics",    data: [5200, 5800, 6100, 6700, 7200, 7850, 8400, 9100] },
  { name: "Apparel",        data: [3100, 3400, 3350, 3800, 4200, 4500, 4800, 5100] },
  { name: "Home & Kitchen", data: [2800, 3000, 3300, 3600, 3900, 4300, 4700, 5000] },
];

// ─── TOOLTIP ─────────────────────────────────────────────────────────────────
const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background:"#0d1117", border:"1px solid #30363d", borderRadius:8,
      padding:"10px 14px", fontFamily:"'IBM Plex Mono',monospace", fontSize:12,
    }}>
      <p style={{ color:"#8b949e", marginBottom:6 }}>{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color:p.color, margin:"2px 0" }}>
          {p.name}: <strong>{typeof p.value === "number" ? p.value.toLocaleString() : p.value}</strong>
        </p>
      ))}
    </div>
  );
};

// ─── MAIN APP ─────────────────────────────────────────────────────────────────
export default function App() {
  const [tab, setTab] = useState("single");

  // Single-product state — pre-loaded with e-commerce monthly order data
  const [rows, setRows] = useState([
    { month: "Jan", sales: 5200 }, { month: "Feb", sales: 5800 },
    { month: "Mar", sales: 6100 }, { month: "Apr", sales: 6700 },
    { month: "May", sales: 7200 }, { month: "Jun", sales: 7850 },
  ]);
  const [newMonth,  setNewMonth]  = useState("");
  const [newSales,  setNewSales]  = useState("");
  const [forecastMonths, setForecastMonths] = useState(3);
  const [products,  setProducts]  = useState(SAMPLE_PRODUCTS);
  const [csvError,  setCsvError]  = useState("");
  const fileRef = useRef();

  // ── Regression ─────────────────────────────────────────────────────────────
  const xs = rows.map((_, i) => i + 1);
  const ys = rows.map(r => r.sales);
  const { m, c } = rows.length >= 2 ? leastSquares(xs, ys) : { m:0, c:0 };
  const { mse, rmse, r2, mae, preds } =
    rows.length >= 2 ? calcMetrics(xs, ys, m, c) : { mse:0,rmse:0,r2:0,mae:0,preds:[] };

  const chartData = rows.map((r, i) => ({
    name: r.month,
    actual: r.sales,
    regression: parseFloat((m * (i + 1) + c).toFixed(1)),
  }));

  const forecasts = Array.from({ length: forecastMonths }, (_, i) => {
    const x = rows.length + i + 1;
    const monthIdx = (rows.length + i) % 12;
    return {
      name: MONTHS[monthIdx],
      predicted: parseFloat((m * x + c).toFixed(0)),
      isForecast: true,
    };
  });

  const fullChart = [
    ...chartData,
    ...forecasts.map(f => ({ name: f.name, actual: null, regression: f.predicted, isForecast:true })),
  ];

  // ── Handlers ───────────────────────────────────────────────────────────────
  const addRow = () => {
    if (!newMonth || !newSales) return;
    setRows([...rows, { month: newMonth, sales: parseFloat(newSales) }]);
    setNewMonth(""); setNewSales("");
  };
  const removeRow = i => setRows(rows.filter((_, idx) => idx !== i));

  const handleCSV = e => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = ev => {
      try {
        const lines = ev.target.result.trim().split("\n").filter(Boolean);
        const parsed = [];
        for (let i = 1; i < lines.length; i++) {
          const [month, sales] = lines[i].split(",").map(s => s.trim());
          if (!month || isNaN(parseFloat(sales))) throw new Error(`Row ${i+1} invalid`);
          parsed.push({ month, sales: parseFloat(sales) });
        }
        if (parsed.length < 2) throw new Error("Need at least 2 rows");
        setRows(parsed); setCsvError("");
      } catch (err) { setCsvError(err.message); }
    };
    reader.readAsText(file);
  };

  // Multi-product
  const productResults = products.map(p => {
    const pxs = p.data.map((_, i) => i + 1);
    const { m: pm, c: pc } = leastSquares(pxs, p.data);
    const { r2: pr2 } = calcMetrics(pxs, p.data, pm, pc);
    const nextX = p.data.length + 1;
    return { ...p, m: pm, c: pc, r2: pr2, nextPred: parseFloat((pm * nextX + pc).toFixed(0)) };
  });

  const multiChart = Array.from(
    { length: Math.max(...products.map(p => p.data.length)) + 1 },
    (_, i) => {
      const obj = { name: MONTHS[i % 12] };
      products.forEach((p, pi) => {
        if (i < p.data.length) obj[p.name] = p.data[i];
        const { m: pm, c: pc } = leastSquares(p.data.map((_,j)=>j+1), p.data);
        obj[`${p.name} Trend`] = parseFloat((pm * (i + 1) + pc).toFixed(1));
      });
      return obj;
    }
  );

  // ─── STYLES ──────────────────────────────────────────────────────────────
  const S = {
    app: {
      minHeight:"100vh", background:"#080c12",
      color:"#e6edf3", fontFamily:"'IBM Plex Sans',sans-serif",
      padding:"0 0 60px",
    },
    header: {
      background:"linear-gradient(135deg,#0d1117 0%,#161b22 100%)",
      borderBottom:"1px solid #21262d",
      padding:"32px 40px 24px", position:"relative", overflow:"hidden",
    },
    headerGlow: {
      position:"absolute", top:-80, right:-80, width:300, height:300,
      background:"radial-gradient(circle,rgba(0,245,212,0.12) 0%,transparent 70%)",
      borderRadius:"50%", pointerEvents:"none",
    },
    projectBadge: {
      display:"inline-block",
      background:"rgba(247,37,133,0.12)", color:"#f72585",
      border:"1px solid rgba(247,37,133,0.35)",
      borderRadius:4, padding:"2px 10px", fontSize:11,
      fontFamily:"'IBM Plex Mono',monospace",
      letterSpacing:1, marginBottom:8,
    },
    badge: {
      display:"inline-block",
      background:"rgba(0,245,212,0.10)", color:"#00f5d4",
      border:"1px solid rgba(0,245,212,0.3)",
      borderRadius:4, padding:"2px 10px", fontSize:11,
      fontFamily:"'IBM Plex Mono',monospace",
      letterSpacing:1, marginBottom:12, marginLeft:8,
    },
    title: {
      fontSize:26, fontWeight:700, margin:"0 0 4px",
      background:"linear-gradient(90deg,#e6edf3,#8b949e)",
      WebkitBackgroundClip:"text", WebkitTextFillColor:"transparent",
    },
    sub: { color:"#8b949e", marginTop:15, fontSize:14, lineHeight:1.6 },
    coBadges: { display:"flex", gap:8, marginTop:15, flexWrap:"wrap" },
    tabs: {
      display:"flex", gap:4, padding:"16px 40px",
      borderBottom:"1px solid #21262d", background:"#0d1117",
    },
    tab: active => ({
      padding:"8px 20px", borderRadius:6, cursor:"pointer",
      border: active ? "1px solid rgba(0,245,212,0.5)" : "1px solid transparent",
      background: active ? "rgba(0,245,212,0.08)" : "transparent",
      color: active ? "#00f5d4" : "#8b949e",
      fontSize:13, fontWeight:500, transition:"all 0.2s",
    }),
    body: { padding:"32px 40px", maxWidth:1200, margin:"0 auto" },
    grid2: { display:"grid", gridTemplateColumns:"1fr 1fr", gap:24 },
    grid3: { display:"grid", gridTemplateColumns:"1fr 1fr 1fr", gap:16 },
    card: {
      background:"#0d1117", border:"1px solid #21262d",
      borderRadius:12, padding:"24px",
    },
    cardTitle: {
      fontFamily:"'IBM Plex Mono',monospace",
      fontSize:11, color:"#00f5d4",
      letterSpacing:2, textTransform:"uppercase",
      marginBottom:20, display:"flex", alignItems:"center", gap:8,
    },
    statBlock: {
      background:"#161b22", borderRadius:8,
      padding:"14px 18px", border:"1px solid #21262d",
    },
    statLabel: { fontSize:11, color:"#8b949e", fontFamily:"'IBM Plex Mono',monospace", letterSpacing:1 },
    statValue: { fontSize:22, fontWeight:700, color:"#e6edf3", marginTop:4 },
    statSub: { fontSize:11, color:"#8b949e", marginTop:2 },
    input: {
      background:"#161b22", border:"1px solid #30363d",
      borderRadius:6, padding:"8px 12px",
      color:"#e6edf3", fontSize:13,
      fontFamily:"'IBM Plex Mono',monospace",
      outline:"none", width:"100%", boxSizing:"border-box",
    },
    btn: {
      background:"linear-gradient(135deg,#00f5d4,#00b4d8)",
      border:"none", borderRadius:6, padding:"9px 20px",
      color:"#080c12", fontWeight:700, fontSize:13,
      cursor:"pointer", whiteSpace:"nowrap",
    },
    btnDanger: {
      background:"transparent", border:"1px solid #f72585",
      borderRadius:4, padding:"3px 8px",
      color:"#f72585", fontSize:11, cursor:"pointer",
    },
    table: { width:"100%", borderCollapse:"collapse" },
    th: {
      textAlign:"left", padding:"8px 12px",
      fontFamily:"'IBM Plex Mono',monospace",
      fontSize:10, color:"#8b949e", letterSpacing:1,
      borderBottom:"1px solid #21262d",
    },
    td: { padding:"8px 12px", fontSize:13, borderBottom:"1px solid #161b22" },
    eq: {
      background:"#161b22", borderRadius:8,
      padding:"20px 24px", textAlign:"center",
      fontFamily:"'IBM Plex Mono',monospace",
      fontSize:18, color:"#00f5d4",
      border:"1px solid rgba(0,245,212,0.2)", letterSpacing:1,
    },
    forecastRow: {
      display:"flex", justifyContent:"space-between", alignItems:"center",
      padding:"10px 0", borderBottom:"1px solid #21262d",
    },
    mathBox: {
      background:"linear-gradient(135deg,rgba(0,245,212,0.05),rgba(0,180,216,0.05))",
      border:"1px solid rgba(0,245,212,0.15)",
      borderRadius:10, padding:"18px 22px",
    },
    pill: color => ({
      display:"inline-block",
      background:`${color}18`, color,
      border:`1px solid ${color}40`,
      borderRadius:12, padding:"2px 10px", fontSize:11,
      fontFamily:"'IBM Plex Mono',monospace",
    }),
    infoBanner: {
      background:"rgba(0,245,212,0.04)",
      border:"1px solid rgba(0,245,212,0.15)",
      borderRadius:8, padding:"12px 18px",
      fontSize:13, color:"#8b949e", lineHeight:1.7,
    },
  };

  return (
    <div style={S.app}>
      <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet" />

      {/* ── HEADER ─────────────────────────────────────────────────────── */}
      <div style={S.header}>
        <div style={S.headerGlow} />
        <div>
          <span style={S.badge}>◈ LEAST SQUARES REGRESSION</span>
        </div>
        <h1 style={S.title}>Sales Forecasting System</h1>

        <p style={S.sub}>
          Predictive demand modeling for online retail · Least Squares Linear Regression · Time-Series Forecasting
        </p>
      </div>

      {/* ── TABS ───────────────────────────────────────────────────────── */}
      <div style={S.tabs}>
        {[
          { id:"single", label:"Single Category" },
          { id:"multi",  label:"Multi-Category"  },
          { id:"math",   label:"∑ Math Model"        },
        ].map(t => (
          <button key={t.id} style={S.tab(tab===t.id)} onClick={()=>setTab(t.id)}>
            {t.label}
          </button>
        ))}
      </div>

      <div style={S.body}>

        {/* ══════════════════════════════════════════════════════════════
            TAB 1 — SINGLE CATEGORY
        ══════════════════════════════════════════════════════════════ */}
        {tab === "single" && (
          <div style={{display:"flex",flexDirection:"column",gap:24}}>

            {/* Context banner */}
            <div style={S.infoBanner}>
              <strong style={{color:"#00f5d4"}}>Industry: E-Commerce</strong> — This model fits a
              least-squares regression line to monthly order/revenue data for a single product category.
              Use it to forecast future demand, plan inventory, and optimize supply chain decisions.
            </div>

            {/* KPIs */}
            <div style={S.grid3}>
              {[
                { label:"SLOPE (m)",    value:m.toFixed(4), sub:"Avg. sales growth per month",   color:"#00f5d4" },
                { label:"INTERCEPT (c)",value:c.toFixed(2), sub:"Baseline projected sales",       color:"#ffd60a" },
                { label:"R² ACCURACY",  value:(r2*100).toFixed(1)+"%", sub:"Model fit quality",
                  color: r2>0.9?"#06d6a0":r2>0.7?"#ffd60a":"#f72585" },
              ].map(k => (
                <div key={k.label} style={{...S.statBlock, borderLeft:`3px solid ${k.color}`}}>
                  <div style={S.statLabel}>{k.label}</div>
                  <div style={{...S.statValue, color:k.color}}>{k.value}</div>
                  <div style={S.statSub}>{k.sub}</div>
                </div>
              ))}
            </div>

            {/* Equation */}
            <div style={S.eq}>
              ŷ = {m.toFixed(2)}x {c >= 0 ? "+" : "−"} {Math.abs(c).toFixed(2)}
              <span style={{fontSize:12,color:"#8b949e",display:"block",marginTop:6}}>
                Best-Fit Regression Line · Least Squares Method
              </span>
            </div>

            {/* Main Chart */}
            <div style={S.card}>
              <div style={S.cardTitle}>
                <span style={{width:8,height:8,borderRadius:"50%",background:"#00f5d4",display:"inline-block"}}/>
                Monthly Sales Trend &amp; Regression Line
              </div>
              <ResponsiveContainer width="100%" height={320}>
                <ComposedChart data={fullChart} margin={{top:10,right:20,left:0,bottom:0}}>
                  <defs>
                    <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor="#00f5d4" stopOpacity={0.15}/>
                      <stop offset="95%" stopColor="#00f5d4" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#21262d" />
                  <XAxis dataKey="name" stroke="#8b949e" tick={{fontSize:11,fontFamily:"'IBM Plex Mono',monospace"}}/>
                  <YAxis stroke="#8b949e" tick={{fontSize:11,fontFamily:"'IBM Plex Mono',monospace"}}/>
                  <Tooltip content={<CustomTooltip/>} />
                  <Legend wrapperStyle={{fontSize:12,fontFamily:"'IBM Plex Mono',monospace"}} />
                  <Area dataKey="actual" name="Actual Orders" fill="url(#areaGrad)"
                    stroke="#00f5d4" strokeWidth={2} dot={{fill:"#00f5d4",r:4}} />
                  <Line dataKey="regression" name="Regression Line"
                    stroke="#f72585" strokeWidth={2} dot={false} />
                </ComposedChart>
              </ResponsiveContainer>
              <div style={{display:"flex",gap:16,marginTop:12,flexWrap:"wrap"}}>
                {[
                  {label:"MSE",  val:mse.toFixed(2)},
                  {label:"RMSE", val:rmse.toFixed(2)},
                  {label:"MAE",  val:mae.toFixed(2)},
                ].map(m2=>(
                  <div key={m2.label} style={{background:"#161b22",borderRadius:6,padding:"8px 14px"}}>
                    <span style={{fontFamily:"'IBM Plex Mono',monospace",fontSize:10,color:"#8b949e"}}>{m2.label} </span>
                    <span style={{fontFamily:"'IBM Plex Mono',monospace",fontSize:13,color:"#e6edf3",fontWeight:600}}>{m2.val}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Data + Forecast */}
            <div style={S.grid2}>
              {/* Historical Data */}
              <div style={S.card}>
                <div style={S.cardTitle}>
                  <span style={{width:8,height:8,borderRadius:"50%",background:"#ffd60a",display:"inline-block"}}/>
                  Historical Sales Data
                </div>
                {/* CSV Upload */}
                <div style={{marginBottom:16}}>
                  <input type="file" accept=".csv" ref={fileRef} onChange={handleCSV} style={{display:"none"}}/>
                  <button
                    style={{...S.btn,background:"#161b22",color:"#8b949e",border:"1px solid #30363d",fontSize:12}}
                    onClick={()=>fileRef.current.click()}>
                    ↑ Upload CSV (month, sales)
                  </button>
                  {csvError && <div style={{color:"#f72585",fontSize:11,marginTop:4}}>{csvError}</div>}
                  <div style={{fontSize:11,color:"#8b949e",marginTop:4}}>
                    CSV format: header row + month, sales columns
                  </div>
                </div>
                {/* Table */}
                <div style={{maxHeight:240,overflowY:"auto"}}>
                  <table style={S.table}>
                    <thead>
                      <tr>
                        <th style={S.th}>#</th>
                        <th style={S.th}>MONTH</th>
                        <th style={S.th}>ACTUAL</th>
                        <th style={S.th}>PREDICTED(ŷ)</th>
                        <th style={S.th}></th>
                      </tr>
                    </thead>
                    <tbody>
                      {rows.map((r, i) => (
                        <tr key={i}>
                          <td style={{...S.td,color:"#8b949e",fontFamily:"monospace"}}>{i+1}</td>
                          <td style={{...S.td,color:"#e6edf3"}}>{r.month}</td>
                          <td style={{...S.td,color:"#00f5d4",fontFamily:"monospace"}}>{r.sales.toLocaleString()}</td>
                          <td style={{...S.td,color:"#f72585",fontFamily:"monospace"}}>{preds[i]?.toFixed(0)}</td>
                          <td style={S.td}>
                            <button style={S.btnDanger} onClick={()=>removeRow(i)}>✕</button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {/* Add Row */}
                <div style={{display:"flex",gap:8,marginTop:16}}>
                  <input style={S.input} placeholder="Month"
                    value={newMonth} onChange={e=>setNewMonth(e.target.value)}
                    onKeyDown={e=>e.key==="Enter"&&addRow()} />
                  <input style={S.input} placeholder="Orders/Revenue"
                    type="number" value={newSales} onChange={e=>setNewSales(e.target.value)}
                    onKeyDown={e=>e.key==="Enter"&&addRow()} />
                  <button style={S.btn} onClick={addRow}>+</button>
                </div>
              </div>

              {/* Forecast */}
              <div style={S.card}>
                <div style={S.cardTitle}>
                  <span style={{width:8,height:8,borderRadius:"50%",background:"#7b2fff",display:"inline-block"}}/>
                  Demand Forecast
                </div>
                <div style={{marginBottom:16,display:"flex",alignItems:"center",gap:12}}>
                  <span style={{fontSize:13,color:"#8b949e"}}>Periods ahead:</span>
                  {[1,3,6,12].map(n=>(
                    <button key={n} onClick={()=>setForecastMonths(n)} style={{
                      padding:"4px 12px", borderRadius:4, fontSize:12, cursor:"pointer",
                      background: forecastMonths===n?"rgba(123,47,255,0.2)":"transparent",
                      border:     forecastMonths===n?"1px solid #7b2fff":"1px solid #30363d",
                      color:      forecastMonths===n?"#7b2fff":"#8b949e",
                    }}>{n}mo</button>
                  ))}
                </div>
                {forecasts.map((f, i) => (
                  <div key={i} style={S.forecastRow}>
                    <div>
                      <div style={{fontSize:13,fontWeight:600,color:"#e6edf3"}}>{f.name}</div>
                      <div style={{fontSize:11,color:"#8b949e",fontFamily:"monospace"}}>
                        Period x = {rows.length + i + 1}
                      </div>
                    </div>
                    <div style={{textAlign:"right"}}>
                      <div style={{fontSize:20,fontWeight:700,color:"#7b2fff",fontFamily:"'IBM Plex Mono',monospace"}}>
                        {f.predicted.toLocaleString()}
                      </div>
                      <div style={{fontSize:11,color:"#8b949e"}}>units projected</div>
                    </div>
                  </div>
                ))}
                <div style={{...S.mathBox,marginTop:20}}>
                  <div style={{fontSize:11,color:"#8b949e",marginBottom:6,fontFamily:"monospace"}}>REGRESSION FORMULA</div>
                  <div style={{fontFamily:"'IBM Plex Mono',monospace",fontSize:14,color:"#e6edf3"}}>
                    ŷ = {m.toFixed(2)} × x {c>=0?"+ ":"− "}{Math.abs(c).toFixed(2)}
                  </div>
                  <div style={{fontSize:11,color:"#8b949e",marginTop:6}}>
                    Trend: {m>0?"▲ Growing":"▼ Declining"} at {Math.abs(m).toFixed(0)} units/month
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ══════════════════════════════════════════════════════════════
            TAB 2 — MULTI-CATEGORY
        ══════════════════════════════════════════════════════════════ */}
        {tab === "multi" && (
          <div style={{display:"flex",flexDirection:"column",gap:24}}>

            <div style={S.infoBanner}>
              <strong style={{color:"#00f5d4"}}>Multi-Category Analysis</strong> — Compare regression
              trends across <strong style={{color:"#e6edf3"}}>Electronics, Apparel, and Home &amp; Kitchen</strong> — three
              core e-commerce verticals. Each product line has its own slope, intercept, and R² score.
            </div>

            {/* Product Cards */}
            <div style={S.grid3}>
              {productResults.map((p, pi) => (
                <div key={pi} style={{...S.card,borderTop:`3px solid ${PRODUCT_COLORS[pi]}`}}>
                  <div style={{fontWeight:700,color:"#e6edf3",marginBottom:12,fontSize:15}}>{p.name}</div>
                  <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:10,marginBottom:14}}>
                    {[
                      {l:"SLOPE (m)", v:p.m.toFixed(2)},
                      {l:"INTERCEPT",  v:p.c.toFixed(2)},
                      {l:"R² FIT",    v:(p.r2*100).toFixed(1)+"%"},
                      {l:"NEXT PRED", v:p.nextPred.toLocaleString()},
                    ].map(s=>(
                      <div key={s.l} style={{background:"#161b22",borderRadius:6,padding:"8px 10px"}}>
                        <div style={{fontSize:9,color:"#8b949e",fontFamily:"monospace",letterSpacing:1}}>{s.l}</div>
                        <div style={{fontSize:15,fontWeight:700,color:PRODUCT_COLORS[pi],fontFamily:"monospace"}}>{s.v}</div>
                      </div>
                    ))}
                  </div>
                  <div style={{fontFamily:"monospace",fontSize:11,color:"#8b949e",
                    background:"#161b22",borderRadius:6,padding:"8px 10px"}}>
                    y = {p.m.toFixed(2)}x {p.c>=0?"+ ":"− "}{Math.abs(p.c).toFixed(2)}
                  </div>
                </div>
              ))}
            </div>

            {/* Multi Chart */}
            <div style={S.card}>
              <div style={S.cardTitle}>
                <span style={{width:8,height:8,borderRadius:"50%",background:"#f72585",display:"inline-block"}}/>
                All Categories · Actual Sales vs Regression Trend
              </div>
              <ResponsiveContainer width="100%" height={360}>
                <ComposedChart data={multiChart} margin={{top:10,right:20,left:0,bottom:0}}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#21262d" />
                  <XAxis dataKey="name" stroke="#8b949e" tick={{fontSize:11,fontFamily:"'IBM Plex Mono',monospace"}}/>
                  <YAxis stroke="#8b949e" tick={{fontSize:11,fontFamily:"'IBM Plex Mono',monospace"}}/>
                  <Tooltip content={<CustomTooltip/>} />
                  <Legend wrapperStyle={{fontSize:11,fontFamily:"'IBM Plex Mono',monospace"}} />
                  {products.map((p, pi) => (
                    <>
                      <Scatter key={`s-${pi}`} dataKey={p.name} fill={PRODUCT_COLORS[pi]} />
                      <Line key={`l-${pi}`} dataKey={`${p.name} Trend`}
                        stroke={PRODUCT_COLORS[pi]} strokeWidth={1.5}
                        strokeDasharray="4 2" dot={false} />
                    </>
                  ))}
                </ComposedChart>
              </ResponsiveContainer>
            </div>

            {/* Comparison Table */}
            <div style={S.card}>
              <div style={S.cardTitle}>
                <span style={{width:8,height:8,borderRadius:"50%",background:"#ffd60a",display:"inline-block"}}/>
                Category-wise Regression Comparison
              </div>
              <table style={S.table}>
                <thead>
                  <tr>
                    {["CATEGORY","EQUATION","SLOPE","R² FIT","NEXT FORECAST","TREND"].map(h=>(
                      <th key={h} style={S.th}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {productResults.map((p,pi)=>(
                    <tr key={pi}>
                      <td style={{...S.td,fontWeight:600,color:PRODUCT_COLORS[pi]}}>{p.name}</td>
                      <td style={{...S.td,fontFamily:"monospace",fontSize:11,color:"#8b949e"}}>
                        y={p.m.toFixed(2)}x{p.c>=0?"+":""}{p.c.toFixed(2)}
                      </td>
                      <td style={{...S.td,fontFamily:"monospace",color:PRODUCT_COLORS[pi]}}>{p.m.toFixed(2)}</td>
                      <td style={S.td}>
                        <span style={S.pill(p.r2>0.9?"#06d6a0":p.r2>0.7?"#ffd60a":"#f72585")}>
                          {(p.r2*100).toFixed(1)}%
                        </span>
                      </td>
                      <td style={{...S.td,fontWeight:700,color:"#e6edf3",fontFamily:"monospace"}}>
                        {p.nextPred.toLocaleString()}
                      </td>
                      <td style={S.td}>
                        <span style={S.pill(p.m>0?"#06d6a0":"#f72585")}>
                          {p.m>0?"▲ Growing":"▼ Declining"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ══════════════════════════════════════════════════════════════
            TAB 3 — MATH MODEL  (CO3 · CO4 · CO5)
        ══════════════════════════════════════════════════════════════ */}
        {tab === "math" && (
          <div style={{display:"flex",flexDirection:"column",gap:24}}>

            {/* ── CO5 ─────────────────────────────────────────────────── */}
            <div style={S.card}>
              <div style={S.cardTitle}>
                <span style={S.pill("#00f5d4")}>CO5</span>
                Least Squares Regression — Core Methodology
              </div>
              <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:20}}>
                <div>
                  <p style={{color:"#8b949e",fontSize:14,lineHeight:1.8}}>
                    The <strong style={{color:"#e6edf3"}}>Least Squares Method</strong> minimizes the sum
                    of squared differences between observed sales values and predicted values on the regression line.
                    It computes the optimal slope <em style={{color:"#00f5d4"}}>m</em> and
                    intercept <em style={{color:"#ffd60a"}}>c</em> that best describe the sales trend.
                  </p>
                  <p style={{color:"#8b949e",fontSize:13,lineHeight:1.8,marginTop:8}}>
                    In e-commerce, this enables precise demand forecasting by identifying the underlying
                    growth trajectory hidden in noisy month-to-month sales data.
                  </p>
                  <div style={{display:"flex",flexDirection:"column",gap:10,marginTop:16}}>
                    {[
                      { label:"Slope Formula",      eq:"m = (n·ΣXY − ΣX·ΣY) / (n·ΣX² − (ΣX)²)" },
                      { label:"Intercept Formula",   eq:"c = (ΣY − m·ΣX) / n" },
                      { label:"Predicted Value",     eq:"ŷ = m·x + c" },
                      { label:"Mean Squared Error",  eq:"MSE = (1/n) · Σ(yᵢ − ŷᵢ)²" },
                      { label:"R² Coefficient",      eq:"R² = 1 − SS_res / SS_tot" },
                    ].map(f=>(
                      <div key={f.label} style={S.mathBox}>
                        <div style={{fontSize:10,color:"#8b949e",fontFamily:"monospace",marginBottom:4}}>{f.label}</div>
                        <div style={{fontFamily:"'IBM Plex Mono',monospace",fontSize:13,color:"#00f5d4"}}>{f.eq}</div>
                      </div>
                    ))}
                  </div>
                </div>
                {/* Live computed values */}
                <div style={{...S.card,background:"#161b22"}}>
                  <div style={{fontSize:11,color:"#8b949e",marginBottom:12,fontFamily:"monospace",letterSpacing:1}}>
                    COMPUTED VALUES — CURRENT DATASET
                  </div>
                  <div style={{display:"flex",flexDirection:"column",gap:10}}>
                    {[
                      {l:"n  (data points)", v:rows.length},
                      {l:"ΣX  (sum of x)",   v:xs.reduce((a,b)=>a+b,0)},
                      {l:"ΣY  (sum of y)",   v:ys.reduce((a,b)=>a+b,0).toLocaleString()},
                      {l:"ΣXY",              v:xs.reduce((a,x,i)=>a+x*ys[i],0).toLocaleString()},
                      {l:"ΣX²",             v:xs.reduce((a,x)=>a+x*x,0)},
                      {l:"Slope  m",         v:m.toFixed(4),  color:"#00f5d4"},
                      {l:"Intercept  c",     v:c.toFixed(4),  color:"#ffd60a"},
                      {l:"R²  Score",        v:(r2*100).toFixed(2)+"%", color:r2>0.9?"#06d6a0":"#ffd60a"},
                      {l:"MSE",              v:mse.toFixed(2)},
                      {l:"RMSE",             v:rmse.toFixed(2)},
                      {l:"MAE",              v:mae.toFixed(2)},
                    ].map(item=>(
                      <div key={item.l} style={{
                        display:"flex",justifyContent:"space-between",
                        padding:"6px 0",borderBottom:"1px solid #21262d",
                      }}>
                        <span style={{fontFamily:"monospace",fontSize:12,color:"#8b949e"}}>{item.l}</span>
                        <span style={{fontFamily:"monospace",fontSize:12,fontWeight:700,
                          color:item.color||"#e6edf3"}}>{item.v}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* ── CO3 ─────────────────────────────────────────────────── */}
            <div style={S.card}>
              <div style={S.cardTitle}>
                <span style={S.pill("#f72585")}>CO3</span>
                Vector Space Representation of Sales Data
              </div>
              <p style={{color:"#8b949e",fontSize:14,lineHeight:1.8}}>
                Monthly sales data can be interpreted as vectors in an <em>n</em>-dimensional vector space.
                The regression problem is equivalent to finding the <strong style={{color:"#e6edf3"}}>orthogonal projection</strong> of
                the sales vector <strong style={{color:"#00f5d4"}}>Y</strong> onto the column space of the
                design matrix <strong style={{color:"#f72585"}}>X</strong>.
                The normal equation gives the exact closed-form solution for the coefficient vector <strong style={{color:"#ffd60a"}}>β</strong>.
              </p>
              <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr",gap:14,marginTop:16}}>
                <div style={S.mathBox}>
                  <div style={{fontSize:10,color:"#8b949e",fontFamily:"monospace",marginBottom:6}}>TIME VECTOR  X</div>
                  <div style={{fontFamily:"monospace",fontSize:12,color:"#f72585"}}>
                    [{xs.join(", ")}]
                  </div>
                  <div style={{fontSize:11,color:"#8b949e",marginTop:6}}>
                    Period indices (x₁ = 1, x₂ = 2 …)
                  </div>
                </div>
                <div style={S.mathBox}>
                  <div style={{fontSize:10,color:"#8b949e",fontFamily:"monospace",marginBottom:6}}>SALES VECTOR  Y</div>
                  <div style={{fontFamily:"monospace",fontSize:12,color:"#00f5d4",wordBreak:"break-word"}}>
                    [{ys.map(v=>v.toLocaleString()).join(", ")}]
                  </div>
                  <div style={{fontSize:11,color:"#8b949e",marginTop:6}}>Observed order volumes</div>
                </div>
                <div style={S.mathBox}>
                  <div style={{fontSize:10,color:"#8b949e",fontFamily:"monospace",marginBottom:6}}>NORMAL EQUATION</div>
                  <div style={{fontFamily:"monospace",fontSize:14,color:"#ffd60a",marginBottom:8}}>
                    β = (XᵀX)⁻¹ Xᵀy
                  </div>
                  <div style={{fontSize:11,color:"#8b949e"}}>
                    Solves the system by projecting Y onto the column space of X, minimizing ‖y − Xβ‖²
                  </div>
                </div>
              </div>
              <div style={{...S.mathBox,marginTop:14}}>
                <div style={{fontSize:10,color:"#8b949e",fontFamily:"monospace",marginBottom:6}}>PREDICTION VECTOR  Ŷ</div>
                <div style={{fontFamily:"monospace",fontSize:12,color:"#7b2fff",wordBreak:"break-word"}}>
                  [{preds.map(p=>p.toFixed(0)).join(", ")}]
                </div>
                <div style={{fontSize:11,color:"#8b949e",marginTop:6}}>
                  Each entry ŷᵢ = m·xᵢ + c — the fitted value for that sales period
                </div>
              </div>
            </div>

            {/* ── CO4 ─────────────────────────────────────────────────── */}
            <div style={S.card}>
              <div style={S.cardTitle}>
                <span style={S.pill("#ffd60a")}>CO4</span>
                Time-Dependent Modeling &amp; Laplace Transform Connection
              </div>
              <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:20}}>
                <div>
                  <p style={{color:"#8b949e",fontSize:14,lineHeight:1.8}}>
                    E-commerce sales are a <strong style={{color:"#e6edf3"}}>discrete time-series signal</strong>.
                    The Laplace Transform conceptually maps this time-domain signal
                    into the <em>s</em>-domain, allowing analysis of system dynamics — such as
                    seasonal spikes, growth rates, and market response — beyond what a static regression captures.
                  </p>
                  <p style={{color:"#8b949e",fontSize:13,lineHeight:1.8,marginTop:10}}>
                    For a linear growth model y(t) = m·t + c, the Laplace Transform gives:
                  </p>
                  <div style={{display:"flex",flexDirection:"column",gap:10,marginTop:12}}>
                    {[
                      { label:"Laplace Transform Definition", eq:"L{f(t)} = F(s) = ∫₀^∞ f(t)·e⁻ˢᵗ dt" },
                      { label:"Transform of Linear Growth",   eq:"L{mt + c} = m/s² + c/s" },
                      { label:"Inverse (time domain)",        eq:"f(t) = L⁻¹{F(s)} → Forecast signal" },
                    ].map(f=>(
                      <div key={f.label} style={S.mathBox}>
                        <div style={{fontSize:10,color:"#8b949e",fontFamily:"monospace",marginBottom:4}}>{f.label}</div>
                        <div style={{fontFamily:"'IBM Plex Mono',monospace",fontSize:13,color:"#ffd60a"}}>{f.eq}</div>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <div style={{...S.card,background:"#161b22",height:"100%"}}>
                    <div style={{fontSize:11,color:"#8b949e",marginBottom:12,fontFamily:"monospace"}}>
                      SALES SIGNAL PIPELINE
                    </div>
                    {[
                      { step:"① Raw Data",        desc:"Monthly order volumes recorded per period",           color:"#8b949e" },
                      { step:"② Pre-processing",  desc:"Outlier removal, normalization, index assignment",    color:"#00f5d4" },
                      { step:"③ Time Domain",      desc:"Signal y(t) = sales as a function of time period t", color:"#ffd60a" },
                      { step:"④ Laplace Domain",   desc:"F(s) captures growth rate & stability of demand",    color:"#f72585" },
                      { step:"⑤ Regression Model", desc:"Best-fit line extracted as steady-state trend",      color:"#7b2fff" },
                      { step:"⑥ Forecast Output",  desc:"ŷ projected forward for inventory & finance plans",  color:"#06d6a0" },
                    ].map(s=>(
                      <div key={s.step} style={{
                        display:"flex",gap:12,padding:"10px 0",borderBottom:"1px solid #21262d",alignItems:"flex-start",
                      }}>
                        <span style={{fontFamily:"monospace",fontSize:12,color:s.color,whiteSpace:"nowrap",fontWeight:700}}>
                          {s.step}
                        </span>
                        <span style={{fontSize:12,color:"#8b949e"}}>{s.desc}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Residual Chart */}
            <div style={S.card}>
              <div style={S.cardTitle}>
                <span style={{width:8,height:8,borderRadius:"50%",background:"#06d6a0",display:"inline-block"}}/>
                Residual Analysis · Error Visualization
              </div>
              <ResponsiveContainer width="100%" height={220}>
                <ComposedChart
                  data={rows.map((r,i)=>({
                    name: r.month,
                    residual: parseFloat((r.sales - preds[i]).toFixed(0)),
                    zero: 0,
                  }))}
                  margin={{top:10,right:20,left:0,bottom:0}}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#21262d" />
                  <XAxis dataKey="name" stroke="#8b949e" tick={{fontSize:11}}/>
                  <YAxis stroke="#8b949e" tick={{fontSize:11}}/>
                  <Tooltip content={<CustomTooltip/>} />
                  <ReferenceLine y={0} stroke="#8b949e" strokeDasharray="4 2" />
                  <Line dataKey="residual" name="Residual (y − ŷ)"
                    stroke="#06d6a0" strokeWidth={2} dot={{fill:"#06d6a0",r:4}} />
                </ComposedChart>
              </ResponsiveContainer>
              <p style={{fontSize:12,color:"#8b949e",marginTop:10}}>
                <strong style={{color:"#e6edf3"}}>Interpretation:</strong> Residuals scattered randomly around
                zero indicate a well-fitting model with no systematic bias — the regression line captures
                the true sales trend. Patterns in residuals would suggest a non-linear relationship.
              </p>
            </div>

            {/* Business Outcomes */}
            <div style={S.card}>
              <div style={S.cardTitle}>
                <span style={{width:8,height:8,borderRadius:"50%",background:"#ff6b35",display:"inline-block"}}/>
                E-Commerce Business Outcomes
              </div>
              <div style={{display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:14}}>
                {[
                  { icon:"📦", title:"Inventory Optimization",  desc:"Forecast demand to prevent stockouts and overstock, reducing holding costs." },
                  { icon:"📣", title:"Marketing Planning",       desc:"Identify growth periods to schedule campaigns and maximize ROI." },
                  { icon:"🔗", title:"Supply Chain Efficiency",  desc:"Share demand projections with suppliers for timely procurement." },
                  { icon:"💰", title:"Financial Forecasting",    desc:"Project monthly revenue to inform budgets and investment decisions." },
                  { icon:"📈", title:"Resource Allocation",      desc:"Scale warehouse staff and logistics based on predicted order volumes." },
                  { icon:"🎯", title:"Strategic Planning",       desc:"Identify high-growth product categories and prioritize accordingly." },
                ].map(o=>(
                  <div key={o.title} style={{...S.mathBox,padding:"16px 18px"}}>
                    <div style={{fontSize:20,marginBottom:6}}>{o.icon}</div>
                    <div style={{fontSize:13,fontWeight:600,color:"#e6edf3",marginBottom:4}}>{o.title}</div>
                    <div style={{fontSize:12,color:"#8b949e",lineHeight:1.6}}>{o.desc}</div>
                  </div>
                ))}
              </div>
            </div>

          </div>
        )}
      </div>
    </div>
  );
}