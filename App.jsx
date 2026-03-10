import { useState, useEffect } from "react";

const BASE_URL = "https://apidatalake.tesouro.gov.br/ords/sadipem/tt";

const ENDPOINTS = [
  {
    id: "pvl",
    label: "PVL — Dados Básicos",
    description: "Lista de Pedidos de Verificação de Limites e Condições",
    path: "/pvl",
    params: [
      { name: "uf", label: "UF", placeholder: "ex: SP, RJ, MG", required: false },
      { name: "tipo_interessado", label: "Tipo de Ente", placeholder: "ex: Estado, Município", required: false },
      { name: "id_ente", label: "Código IBGE", placeholder: "ex: 3550308", required: false },
    ],
    color: "#00c896",
  },
  {
    id: "opc-liberacoes",
    label: "Cronograma de Liberações",
    description: "Cronogramas de liberações das operações contratadas",
    path: "/opc-cronograma-liberacoes",
    params: [{ name: "id_pleito", label: "ID do Pleito", placeholder: "ex: 12345", required: true }],
    color: "#4f9ef8",
  },
  {
    id: "opc-pagamentos",
    label: "Cronograma de Pagamentos",
    description: "Cronogramas de pagamentos das operações contratadas",
    path: "/opc-cronograma-pagamentoss",
    params: [{ name: "id_pleito", label: "ID do Pleito", placeholder: "ex: 12345", required: true }],
    color: "#f8934f",
  },
  {
    id: "opc-cambio",
    label: "Taxas de Câmbio",
    description: "Taxas de câmbio das operações contratadas",
    path: "/opc-taxa-cambio",
    params: [{ name: "id_pleito", label: "ID do Pleito", placeholder: "ex: 12345", required: true }],
    color: "#c84fb8",
  },
  {
    id: "res-pagamentos",
    label: "Resumo — Pagamentos",
    description: "Cronograma de pagamentos da aba Resumo",
    path: "/res-cronograma-pagamentos",
    params: [{ name: "id_pleito", label: "ID do Pleito", placeholder: "ex: 12345", required: true }],
    color: "#f8e04f",
  },
  {
    id: "res-cdp",
    label: "Resumo — CDP",
    description: "Informações do Cadastro da Dívida Pública",
    path: "/res-cdp",
    params: [{ name: "id_pleito", label: "ID do Pleito", placeholder: "ex: 12345", required: true }],
    color: "#f84f4f",
  },
];

function JsonTree({ data, depth = 0 }) {
  const [collapsed, setCollapsed] = useState(depth > 1);
  if (data === null) return <span style={{ color: "#999" }}>null</span>;
  if (typeof data === "boolean") return <span style={{ color: "#c084fc" }}>{String(data)}</span>;
  if (typeof data === "number") return <span style={{ color: "#4ade80" }}>{data}</span>;
  if (typeof data === "string") return <span style={{ color: "#fbbf24" }}>"{data}"</span>;
  if (Array.isArray(data)) {
    if (data.length === 0) return <span style={{ color: "#94a3b8" }}>[]</span>;
    return (
      <span>
        <button onClick={() => setCollapsed(!collapsed)} style={{ background: "none", border: "none", color: "#94a3b8", cursor: "pointer", fontFamily: "monospace", fontSize: 13, padding: "0 2px" }}>
          {collapsed ? "▶" : "▼"}
        </button>
        <span style={{ color: "#94a3b8" }}>[{data.length}]</span>
        {!collapsed && (
          <div style={{ paddingLeft: 20, borderLeft: "1px solid #1e2d40" }}>
            {data.map((item, i) => (
              <div key={i} style={{ margin: "2px 0" }}>
                <span style={{ color: "#475569", marginRight: 6 }}>{i}:</span>
                <JsonTree data={item} depth={depth + 1} />
              </div>
            ))}
          </div>
        )}
      </span>
    );
  }
  if (typeof data === "object") {
    const keys = Object.keys(data);
    if (keys.length === 0) return <span style={{ color: "#94a3b8" }}>{"{}"}</span>;
    return (
      <span>
        <button onClick={() => setCollapsed(!collapsed)} style={{ background: "none", border: "none", color: "#94a3b8", cursor: "pointer", fontFamily: "monospace", fontSize: 13, padding: "0 2px" }}>
          {collapsed ? "▶" : "▼"}
        </button>
        <span style={{ color: "#94a3b8" }}>{"{"}  {keys.length} campos{"}"}</span>
        {!collapsed && (
          <div style={{ paddingLeft: 20, borderLeft: "1px solid #1e2d40" }}>
            {keys.map((k) => (
              <div key={k} style={{ margin: "2px 0" }}>
                <span style={{ color: "#7dd3fc" }}>{k}</span>
                <span style={{ color: "#475569" }}>: </span>
                <JsonTree data={data[k]} depth={depth + 1} />
              </div>
            ))}
          </div>
        )}
      </span>
    );
  }
  return <span>{String(data)}</span>;
}

export default function App() {
  const [selected, setSelected] = useState(ENDPOINTS[0]);
  const [paramValues, setParamValues] = useState({});
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [builtUrl, setBuiltUrl] = useState("");
  const [tab, setTab] = useState("tree");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    setParamValues({});
    setResult(null);
    setError(null);
  }, [selected]);

  useEffect(() => {
    const params = new URLSearchParams();
    Object.entries(paramValues).forEach(([k, v]) => { if (v) params.set(k, v); });
    const qs = params.toString();
    setBuiltUrl(`${BASE_URL}${selected.path}${qs ? "?" + qs : ""}`);
  }, [paramValues, selected]);

  const handleFetch = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch(builtUrl);
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      const data = await res.json();
      setResult(data);
      setTab("tree");
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const copyUrl = () => {
    navigator.clipboard.writeText(builtUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const itemCount = result?.items?.length ?? (Array.isArray(result) ? result.length : null);

  return (
    <div style={{ minHeight: "100vh", background: "#070d14", color: "#e2e8f0", fontFamily: "'IBM Plex Mono', 'Courier New', monospace", display: "flex", flexDirection: "column" }}>
      <div style={{ padding: "24px 32px 16px", borderBottom: "1px solid #0f1f2e" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ width: 8, height: 8, borderRadius: "50%", background: "#00c896", boxShadow: "0 0 8px #00c896" }} />
          <span style={{ fontSize: 11, letterSpacing: 3, color: "#00c896", textTransform: "uppercase" }}>Tesouro Nacional</span>
        </div>
        <h1 style={{ margin: "6px 0 2px", fontSize: 22, fontWeight: 700, color: "#fff", letterSpacing: -0.5 }}>
          API SADIPEM <span style={{ color: "#1e3a52", fontSize: 14 }}>// Explorer</span>
        </h1>
        <p style={{ margin: 0, fontSize: 11, color: "#334155" }}>Sistema de Análise da Dívida Pública, Operações de Crédito e Garantias</p>
      </div>

      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        <div style={{ width: 240, borderRight: "1px solid #0f1f2e", padding: "16px 0", flexShrink: 0 }}>
          <div style={{ padding: "0 16px 10px", fontSize: 10, letterSpacing: 2, color: "#1e3a52", textTransform: "uppercase" }}>Endpoints</div>
          {ENDPOINTS.map((ep) => (
            <button key={ep.id} onClick={() => setSelected(ep)}
              style={{ width: "100%", textAlign: "left", background: selected.id === ep.id ? "#0a1825" : "none", border: "none", borderLeft: selected.id === ep.id ? `2px solid ${ep.color}` : "2px solid transparent", padding: "10px 16px", cursor: "pointer", transition: "all 0.15s" }}>
              <div style={{ fontSize: 12, color: selected.id === ep.id ? "#fff" : "#475569", fontWeight: selected.id === ep.id ? 600 : 400, marginBottom: 2 }}>{ep.label}</div>
              <div style={{ fontSize: 10, color: "#1e3a52", lineHeight: 1.4 }}>{ep.description}</div>
            </button>
          ))}
        </div>

        <div style={{ flex: 1, overflow: "auto", padding: 24 }}>
          <div style={{ marginBottom: 20 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
              <span style={{ background: "#0a2a1a", color: selected.color, fontSize: 10, padding: "3px 8px", borderRadius: 4, letterSpacing: 1, border: `1px solid ${selected.color}33` }}>GET</span>
              <span style={{ fontSize: 13, color: "#334155" }}>{BASE_URL}</span>
              <span style={{ fontSize: 13, color: selected.color }}>{selected.path}</span>
            </div>
            <p style={{ margin: 0, fontSize: 12, color: "#475569" }}>{selected.description}</p>
          </div>

          <div style={{ background: "#0a1218", border: "1px solid #0f1f2e", borderRadius: 8, padding: 16, marginBottom: 16 }}>
            <div style={{ fontSize: 10, letterSpacing: 2, color: "#1e3a52", textTransform: "uppercase", marginBottom: 12 }}>Parâmetros</div>
            {selected.params.map((p) => (
              <div key={p.name} style={{ marginBottom: 10 }}>
                <label style={{ display: "block", fontSize: 11, color: "#64748b", marginBottom: 4 }}>
                  {p.label} {p.required && <span style={{ color: "#f84f4f" }}>*</span>}
                </label>
                <input
                  value={paramValues[p.name] || ""}
                  onChange={(e) => setParamValues({ ...paramValues, [p.name]: e.target.value })}
                  placeholder={p.placeholder}
                  style={{ width: "100%", boxSizing: "border-box", background: "#070d14", border: "1px solid #1e2d40", borderRadius: 6, padding: "8px 12px", color: "#e2e8f0", fontSize: 13, fontFamily: "inherit", outline: "none" }}
                />
              </div>
            ))}
          </div>

          <div style={{ background: "#0a1218", border: "1px solid #0f1f2e", borderRadius: 8, padding: "10px 14px", marginBottom: 16, display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ fontSize: 11, color: "#1e3a52", flexShrink: 0 }}>URL:</span>
            <span style={{ fontSize: 11, color: "#4f9ef8", flex: 1, wordBreak: "break-all" }}>{builtUrl}</span>
            <button onClick={copyUrl} style={{ background: "none", border: "1px solid #1e2d40", borderRadius: 4, padding: "4px 10px", color: copied ? "#00c896" : "#475569", fontSize: 10, cursor: "pointer", flexShrink: 0 }}>
              {copied ? "✓ copiado" : "copiar"}
            </button>
          </div>

          <button onClick={handleFetch} disabled={loading}
            style={{ background: loading ? "#0a2a1a" : selected.color, color: loading ? selected.color : "#000", border: "none", borderRadius: 6, padding: "10px 24px", fontSize: 13, fontWeight: 700, cursor: loading ? "wait" : "pointer", fontFamily: "inherit", letterSpacing: 1, marginBottom: 20, transition: "all 0.2s" }}>
            {loading ? "⟳  buscando..." : "▶  Executar"}
          </button>

          {error && (
            <div style={{ background: "#1a0a0a", border: "1px solid #4f1f1f", borderRadius: 8, padding: 16, marginBottom: 16, color: "#f87171", fontSize: 12 }}>
              <span style={{ fontWeight: 700 }}>Erro: </span>{error}
            </div>
          )}

          {result && (
            <div style={{ background: "#0a1218", border: "1px solid #0f1f2e", borderRadius: 8, overflow: "hidden" }}>
              <div style={{ padding: "10px 16px", borderBottom: "1px solid #0f1f2e", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <div style={{ display: "flex", gap: 4 }}>
                  {["tree", "raw"].map((t) => (
                    <button key={t} onClick={() => setTab(t)}
                      style={{ background: tab === t ? "#0f1f2e" : "none", border: "1px solid", borderColor: tab === t ? "#1e2d40" : "transparent", borderRadius: 4, padding: "4px 12px", color: tab === t ? "#e2e8f0" : "#475569", fontSize: 11, cursor: "pointer", fontFamily: "inherit" }}>
                      {t}
                    </button>
                  ))}
                </div>
                <div style={{ fontSize: 11, color: "#334155" }}>
                  {itemCount !== null && <span style={{ color: "#00c896" }}>{itemCount} registros</span>}
                  {result.hasMore && <span style={{ color: "#f8934f", marginLeft: 8 }}>+ mais páginas</span>}
                </div>
              </div>
              <div style={{ padding: 16, fontSize: 12, lineHeight: 1.7, overflow: "auto", maxHeight: 500 }}>
                {tab === "tree" ? (
                  <JsonTree data={result} depth={0} />
                ) : (
                  <pre style={{ margin: 0, color: "#64748b", whiteSpace: "pre-wrap", wordBreak: "break-all" }}>
                    {JSON.stringify(result, null, 2)}
                  </pre>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
