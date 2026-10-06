import React, { useState, useEffect } from "react";
import { 
  BarChart3, Database, ShieldAlert, Settings, Upload, RefreshCw, Trash2, 
  CheckCircle, AlertCircle, FileText, Globe, Key, Clock, TrendingUp 
} from "lucide-react";
import { API_BASE_URL } from "../apiConfig";


// Admin API calls carry the operator's token (backend: ADMIN_API_TOKEN). Kept in sessionStorage only.
const ADMIN_TOKEN_KEY = "cittaai_admin_token";
const readAdminToken = () => {
  try { return sessionStorage.getItem(ADMIN_TOKEN_KEY) || ""; } catch { return ""; }
};
const adminFetch = (url, options = {}) =>
  fetch(url, { ...options, headers: { ...(options.headers || {}), "X-Admin-Token": readAdminToken() } });

export default function AdminConsultant() {
  const [adminToken, setAdminToken] = useState(readAdminToken());
  const [activeTab, setActiveTab] = useState("analytics");
  const [status, setStatus] = useState({});
  const [analytics, setAnalytics] = useState({});
  const [documents, setDocuments] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState(null);
  
  // Config form inputs
  const [provider, setProvider] = useState("groq");
  const [model, setModel] = useState("openai/gpt-oss-20b");
  
  // Document upload form inputs
  const [uploadFile, setUploadFile] = useState(null);
  const [docPage, setDocPage] = useState("/");
  const [docSection, setDocSection] = useState("brochures");
  const [docTitle, setDocTitle] = useState("");

  const fetchStatus = async () => {
    try {
      const res = await adminFetch(`${API_BASE_URL}/api/admin/status`);
      const data = await res.json();
      setStatus(data);
      setProvider(data.provider || "nvidia");
      setModel(data.model || "meta/llama-3.1-70b-instruct");
    } catch (err) {
      console.error("Failed to fetch admin status", err);
    }
  };

  const fetchAnalytics = async () => {
    try {
      const res = await adminFetch(`${API_BASE_URL}/api/admin/analytics`);
      const data = await res.json();
      setAnalytics(data);
    } catch (err) {
      console.error("Failed to fetch analytics", err);
    }
  };

  const fetchDocuments = async () => {
    try {
      const res = await adminFetch(`${API_BASE_URL}/api/admin/documents`);
      const data = await res.json();
      setDocuments(data);
    } catch (err) {
      console.error("Failed to fetch documents list", err);
    }
  };

  useEffect(() => {
    fetchStatus();
    fetchAnalytics();
    fetchDocuments();
  }, []);

  const showNotification = (msg, isError = false) => {
    setMessage({ text: msg, isError });
    setTimeout(() => setMessage(null), 5000);
  };

  const handleReindex = async () => {
    setIsLoading(true);
    try {
      const res = await adminFetch(`${API_BASE_URL}/api/admin/reindex`, { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        showNotification(data.message || "Website re-indexed successfully!");
        fetchStatus();
        fetchDocuments();
        fetchAnalytics();
      } else {
        const err = await res.json();
        showNotification(err.detail || "Re-indexing failed.", true);
      }
    } catch (err) {
      showNotification("Error connecting to server.", true);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveConfig = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      const res = await adminFetch(`${API_BASE_URL}/api/admin/config`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider,
          model
        })
      });
      if (res.ok) {
        showNotification("LLM configuration saved successfully!");
        fetchStatus();
      } else {
        showNotification("Failed to update config.", true);
      }
    } catch (err) {
      showNotification("Connection error.", true);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    e.preventDefault();
    if (!uploadFile) {
      showNotification("Please select a file to upload.", true);
      return;
    }
    
    setIsLoading(true);
    const formData = new FormData();
    formData.append("file", uploadFile);
    formData.append("page", docPage);
    formData.append("section", docSection);
    formData.append("title", docTitle || uploadFile.name);

    try {
      const res = await adminFetch(`${API_BASE_URL}/api/admin/upload`, {
        method: "POST",
        body: formData
      });
      
      if (res.ok) {
        showNotification(`Successfully uploaded and indexed ${uploadFile.name}!`);
        setUploadFile(null);
        setDocTitle("");
        // Reset file input element
        document.getElementById("file-input-field").value = "";
        fetchDocuments();
        fetchStatus();
      } else {
        const err = await res.json();
        showNotification(err.detail || "Upload failed.", true);
      }
    } catch (err) {
      showNotification("Error uploading document.", true);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteDoc = async (sourceName) => {
    if (!window.confirm(`Are you sure you want to delete all chunks for "${sourceName}"?`)) return;
    
    setIsLoading(true);
    try {
      const res = await adminFetch(`${API_BASE_URL}/api/admin/documents/${encodeURIComponent(sourceName)}`, {
        method: "DELETE"
      });
      if (res.ok) {
        showNotification(`Deleted chunks for ${sourceName}.`);
        fetchDocuments();
        fetchStatus();
      } else {
        showNotification("Failed to delete document.", true);
      }
    } catch (err) {
      showNotification("Connection error.", true);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0A0F1E] pt-24 pb-16 text-white px-4 md:px-8 relative overflow-hidden">
      {/* Background Ambience */}
      <div className="absolute top-0 right-0 w-[400px] h-[400px] bg-blue-600/10 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-emerald-600/5 rounded-full blur-[100px] pointer-events-none" />

      {/* Main Container */}
      <div className="max-w-6xl mx-auto relative z-10">
        
        {/* Admin token (required by the backend for every admin action) */}
        <form
          className="mb-6 flex flex-wrap items-center gap-2 text-sm"
          onSubmit={(e) => {
            e.preventDefault();
            try { sessionStorage.setItem(ADMIN_TOKEN_KEY, adminToken); } catch { /* storage unavailable */ }
            fetchStatus();
          }}
        >
          <Key className="w-4 h-4 text-slate-400" />
          <input
            type="password"
            value={adminToken}
            onChange={(e) => setAdminToken(e.target.value)}
            placeholder="Admin token"
            className="bg-slate-900 border border-white/10 rounded px-3 py-1.5 text-slate-200 w-64"
            aria-label="Admin token"
          />
          <button type="submit" className="px-3 py-1.5 rounded bg-blue-600 text-white">Use token</button>
        </form>

        {/* Title Block */}
        <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 pb-6 border-b border-white/5">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-white mb-2 font-display">
              Enterprise AI Consultant <span className="text-blue-500 font-semibold font-mono text-sm ml-2 px-2.5 py-1 bg-blue-950/40 rounded border border-blue-500/20">ADMIN CONSOLE</span>
            </h1>
            <p className="text-sm text-slate-400">
              Manage the website knowledge graphs, document pipelines, model configurations, and query analytics.
            </p>
          </div>
          
          <div className="mt-4 md:mt-0 flex items-center gap-3">
            {/* Status indicators */}
            <div className="px-3 py-1.5 rounded-lg bg-white/3 border border-white/5 flex items-center gap-2 text-xs">
              <span className={`w-2 h-2 rounded-full ${status.nvidia_status === "Connected" ? "bg-emerald-400" : "bg-rose-400"}`} />
              <span className="text-slate-300">NVIDIA API: {status.nvidia_status || "Checking..."}</span>
            </div>
            
            <button
              onClick={handleReindex}
              disabled={isLoading}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 text-white rounded-lg text-sm font-semibold flex items-center gap-2 shadow-lg shadow-blue-500/15 border border-blue-500/20 transition-all"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
              <span>Re-index Website</span>
            </button>
          </div>
        </div>

        {/* Global Notifications */}
        {message && (
          <div className={`p-4 rounded-xl border mb-6 flex items-center gap-3 ${
            message.isError 
              ? "bg-rose-950/20 border-rose-500/30 text-rose-300" 
              : "bg-emerald-950/20 border-emerald-500/30 text-emerald-300"
          }`}>
            {message.isError ? <AlertCircle className="w-5 h-5" /> : <CheckCircle className="w-5 h-5" />}
            <span className="text-sm">{message.text}</span>
          </div>
        )}

        {/* Tabs Bar */}
        <div className="flex gap-2 mb-8 border-b border-white/5 pb-0.5">
          <button
            onClick={() => setActiveTab("analytics")}
            className={`px-5 py-3 text-sm font-medium border-b-2 transition-all ${
              activeTab === "analytics" 
                ? "border-blue-500 text-blue-400" 
                : "border-transparent text-slate-400 hover:text-white"
            }`}
          >
            <span className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              Analytics Dashboard
            </span>
          </button>
          
          <button
            onClick={() => setActiveTab("knowledge")}
            className={`px-5 py-3 text-sm font-medium border-b-2 transition-all ${
              activeTab === "knowledge" 
                ? "border-blue-500 text-blue-400" 
                : "border-transparent text-slate-400 hover:text-white"
            }`}
          >
            <span className="flex items-center gap-2">
              <Database className="w-4 h-4" />
              Knowledge Sources
            </span>
          </button>
          
          <button
            onClick={() => setActiveTab("config")}
            className={`px-5 py-3 text-sm font-medium border-b-2 transition-all ${
              activeTab === "config" 
                ? "border-blue-500 text-blue-400" 
                : "border-transparent text-slate-400 hover:text-white"
            }`}
          >
            <span className="flex items-center gap-2">
              <Settings className="w-4 h-4" />
              LLM Settings
            </span>
          </button>
        </div>

        {/* --- Tab Content: Analytics --- */}
        {activeTab === "analytics" && (
          <div className="space-y-8">
            {/* KPI Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="p-5 rounded-2xl glass-dark border border-white/8 relative">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">Total Queries</span>
                <span className="text-3xl font-bold font-display text-white">{analytics.total_queries ?? 0}</span>
                <Clock className="absolute top-4 right-4 w-5 h-5 text-slate-500" />
              </div>

              <div className="p-5 rounded-2xl glass-dark border border-white/8 relative">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">Search Success Rate</span>
                <span className="text-3xl font-bold font-display text-emerald-400">{analytics.search_success_rate ?? "100.0%"}</span>
                <TrendingUp className="absolute top-4 right-4 w-5 h-5 text-slate-500" />
              </div>

              <div className="p-5 rounded-2xl glass-dark border border-white/8 relative">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">Avg Response Latency</span>
                <span className="text-3xl font-bold font-display text-white">{analytics.average_response_time ?? "0.0s"}</span>
                <Clock className="absolute top-4 right-4 w-5 h-5 text-slate-500" />
              </div>

              <div className="p-5 rounded-2xl glass-dark border border-white/8 relative">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">Failed / Fallbacks</span>
                <span className="text-3xl font-bold font-display text-rose-400">{analytics.failed_queries ?? 0}</span>
                <ShieldAlert className="absolute top-4 right-4 w-5 h-5 text-slate-500" />
              </div>
            </div>

            {/* Middle row: Most Asked Questions & Redirects */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="p-6 rounded-2xl glass-dark border border-white/5">
                <h3 className="text-base font-semibold mb-4 text-white border-b border-white/5 pb-3">Top Asked Questions</h3>
                <div className="space-y-3">
                  {analytics.most_asked_questions && analytics.most_asked_questions.length > 0 ? (
                    analytics.most_asked_questions.map((item, idx) => (
                      <div key={idx} className="flex justify-between items-center text-sm">
                        <span className="text-slate-300 truncate max-w-[80%]">{item.query}</span>
                        <span className="font-mono text-slate-400 bg-white/3 px-2 py-0.5 rounded text-xs">{item.count} asks</span>
                      </div>
                    ))
                  ) : (
                    <span className="text-xs text-slate-500 block py-4 text-center">No queries logged yet.</span>
                  )}
                </div>
              </div>

              <div className="p-6 rounded-2xl glass-dark border border-white/5">
                <h3 className="text-base font-semibold mb-4 text-white border-b border-white/5 pb-3">Top Page Redirects</h3>
                <div className="space-y-3">
                  {analytics.top_redirects && analytics.top_redirects.length > 0 ? (
                    analytics.top_redirects.map((item, idx) => (
                      <div key={idx} className="flex justify-between items-center text-sm">
                        <span className="text-blue-400 font-mono truncate max-w-[80%]">{item.path}</span>
                        <span className="font-mono text-slate-400 bg-white/3 px-2 py-0.5 rounded text-xs">{item.count} clicks</span>
                      </div>
                    ))
                  ) : (
                    <span className="text-xs text-slate-500 block py-4 text-center">No redirects recorded.</span>
                  )}
                </div>
              </div>
            </div>

            {/* Bottom Row: Detailed Logs Table */}
            <div className="p-6 rounded-2xl glass-dark border border-white/5">
              <h3 className="text-base font-semibold mb-4 text-white border-b border-white/5 pb-3">Recent Interaction Logs</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-white/5 text-slate-400 text-xs">
                      <th className="py-2">Time</th>
                      <th className="py-2">Visitor Question</th>
                      <th className="py-2">Assistant Response Summary</th>
                      <th className="py-2 text-right">Latency</th>
                      <th className="py-2 text-right">Confidence</th>
                    </tr>
                  </thead>
                  <tbody>
                    {analytics.logs && analytics.logs.length > 0 ? (
                      analytics.logs.map((log, idx) => (
                        <tr key={idx} className="border-b border-white/3 text-slate-300 hover:bg-white/1">
                          <td className="py-3 text-[11px] text-slate-500 font-mono">
                            {new Date(log.timestamp).toLocaleTimeString()}
                          </td>
                          <td className="py-3 max-w-[150px] truncate">{log.query}</td>
                          <td className="py-3 max-w-[280px] truncate text-slate-400">{log.response}</td>
                          <td className="py-3 text-right font-mono text-[12px]">{log.latency.toFixed(2)}s</td>
                          <td className={`py-3 text-right font-mono text-[12px] ${log.score >= 0.55 ? "text-emerald-400" : "text-rose-400"}`}>
                            {log.score.toFixed(2)}
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan="5" className="text-center py-6 text-xs text-slate-500">No interaction logs logged.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* --- Tab Content: Knowledge base management --- */}
        {activeTab === "knowledge" && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            
            {/* Left: Upload brochures form */}
            <div className="md:col-span-1 p-6 rounded-2xl glass-dark border border-white/5 flex flex-col justify-between">
              <div>
                <h3 className="text-base font-semibold mb-4 text-white border-b border-white/5 pb-3">Upload Corporate Knowledge</h3>
                <form onSubmit={handleFileUpload} className="space-y-4">
                  <div>
                    <label className="text-xs text-slate-400 font-semibold block mb-1.5">File (PDF or DOCX)</label>
                    <input 
                      id="file-input-field"
                      type="file" 
                      accept=".pdf,.docx,.doc"
                      onChange={(e) => setUploadFile(e.target.files[0])}
                      className="w-full text-xs text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-blue-950 file:text-blue-300 hover:file:bg-blue-900 cursor-pointer bg-white/3 p-2 rounded-lg border border-white/8"
                    />
                  </div>

                  <div>
                    <label className="text-xs text-slate-400 font-semibold block mb-1.5">Document Title</label>
                    <input 
                      type="text"
                      value={docTitle}
                      onChange={(e) => setDocTitle(e.target.value)}
                      placeholder="e.g. Pharma Product Brochure"
                      className="w-full px-3 py-2 bg-white/3 border border-white/8 rounded-lg text-xs text-white focus:border-blue-500/50 outline-none"
                    />
                  </div>

                  <div>
                    <label className="text-xs text-slate-400 font-semibold block mb-1.5">Reference Link / Page Redirect</label>
                    <input 
                      type="text"
                      value={docPage}
                      onChange={(e) => setDocPage(e.target.value)}
                      placeholder="e.g. /solutions/pharma-os"
                      className="w-full px-3 py-2 bg-white/3 border border-white/8 rounded-lg text-xs text-white focus:border-blue-500/50 outline-none font-mono"
                    />
                  </div>
                  
                  <button
                    type="submit"
                    disabled={isLoading}
                    className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-2 shadow-lg shadow-blue-500/10 border border-blue-500/20 transition-all mt-4"
                  >
                    <Upload className="w-4.5 h-4.5" />
                    <span>Upload & Embed</span>
                  </button>
                </form>
              </div>
            </div>

            {/* Right: Indexed Files list */}
            <div className="md:col-span-2 p-6 rounded-2xl glass-dark border border-white/5">
              <h3 className="text-base font-semibold mb-4 text-white border-b border-white/5 pb-3">Indexed Knowledge Base Sources</h3>
              <div className="space-y-4">
                {documents && documents.length > 0 ? (
                  documents.map((doc, idx) => (
                    <div key={idx} className="flex justify-between items-center p-3 rounded-xl bg-white/3 border border-white/5 hover:border-white/10 transition-all">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-lg bg-blue-950/40 border border-blue-500/20 flex items-center justify-center">
                          {doc.source === "content.js" ? <Globe className="w-5 h-5 text-blue-400" /> : <FileText className="w-5 h-5 text-indigo-400" />}
                        </div>
                        <div>
                          <h4 className="text-xs font-semibold text-white tracking-wide">{doc.source}</h4>
                          <div className="flex gap-2.5 text-[10px] text-slate-500 mt-1">
                            <span>Chunks: <strong className="text-slate-300 font-medium">{doc.chunk_count}</strong></span>
                            <span>Type: <strong className="text-slate-300 font-medium uppercase">{doc.document_type}</strong></span>
                            {doc.last_updated && (
                              <span>Updated: <strong className="text-slate-300 font-medium">{new Date(parseFloat(doc.last_updated) * 1000 ? parseFloat(doc.last_updated) * 1000 : doc.last_updated).toLocaleDateString()}</strong></span>
                            )}
                          </div>
                        </div>
                      </div>
                      
                      {doc.source !== "content.js" && (
                        <button
                          onClick={() => handleDeleteDoc(doc.source)}
                          disabled={isLoading}
                          className="w-8 h-8 rounded-lg hover:bg-rose-950/20 border border-transparent hover:border-rose-500/20 text-slate-400 hover:text-rose-400 flex items-center justify-center transition-all duration-200"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  ))
                ) : (
                  <span className="text-xs text-slate-500 block py-6 text-center">No indexed files in vector database. Click Re-index to upload content.js.</span>
                )}
              </div>
            </div>
          </div>
        )}

        {/* --- Tab Content: Config Settings --- */}
        {activeTab === "config" && (
          <div className="p-6 rounded-2xl glass-dark border border-white/5 max-w-xl">
            <h3 className="text-base font-semibold mb-4 text-white border-b border-white/5 pb-3">Active LLM Provider Configuration</h3>
            
            <form onSubmit={handleSaveConfig} className="space-y-4">
              <div>
                <label className="text-xs text-slate-400 font-semibold block mb-1.5">LLM Provider</label>
                <select
                  value={provider}
                  onChange={(e) => setProvider(e.target.value)}
                  className="w-full px-3 py-2.5 bg-[#0C1226] border border-white/10 rounded-lg text-xs text-white outline-none focus:border-blue-500/50"
                >
                  <option value="nvidia">NVIDIA NIM API</option>
                  <option value="openai">OpenAI (Cloud GPT)</option>
                  <option value="gemini">Google Gemini (Cloud)</option>
                  <option value="claude">Anthropic Claude (Cloud)</option>
                </select>
              </div>

              <div>
                <label className="text-xs text-slate-400 font-semibold block mb-1.5">Active Generation Model</label>
                <input 
                  type="text"
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  placeholder="e.g. meta/llama-3.1-70b-instruct, gpt-4o, gemini-1.5-pro, claude-3-5-sonnet"
                  className="w-full px-3 py-2.5 bg-white/3 border border-white/8 rounded-lg text-xs text-white focus:border-blue-500/50 outline-none font-mono"
                  required
                />
              </div>

              <div className="pt-4 border-t border-white/5 mt-6 flex justify-end">
                <button
                  type="submit"
                  disabled={isLoading}
                  className="px-6 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 text-white rounded-lg text-xs font-semibold flex items-center gap-2 shadow-lg shadow-blue-500/10 border border-blue-500/20 transition-all"
                >
                  <Key className="w-4 h-4" />
                  <span>Save Configuration</span>
                </button>
              </div>
            </form>
          </div>
        )}
      </div>
    </div>
  );
}
