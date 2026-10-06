import React, { useState, useEffect, useRef } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { MessageSquare, Send, X, Minus, Sparkles, User, Bot, ExternalLink, ArrowRight, RefreshCw, Globe } from "lucide-react";
import { API_BASE_URL } from "../apiConfig";

// Generate or retrieve persistent Session ID
const getSessionId = () => {
  let id = localStorage.getItem("cittaai_consultant_session_id");
  if (!id) {
    id = "session_" + Math.random().toString(36).substring(2, 15);
    localStorage.setItem("cittaai_consultant_session_id", id);
  }
  return id;
};

export default function AIConsultant() {
  const navigate = useNavigate();
  const location = useLocation();
  // dev-only: ?chat=open starts with the panel open (screenshot reviews)
  const [isOpen, setIsOpen] = useState(() => process.env.NODE_ENV !== "production"
    && new URLSearchParams(window.location.search).get("chat") === "open");
  const [isExpanding, setIsExpanding] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [sessionId, setSessionId] = useState(getSessionId());
  const [isStreaming, setIsStreaming] = useState(false);
  const [hasReceivedFirstToken, setHasReceivedFirstToken] = useState(false);
  const [activeBotMsgId, setActiveBotMsgId] = useState(null);
  
  // RAG / SSE Response Metadata
  const [citations, setCitations] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [preferences, setPreferences] = useState({});
  const [recommendedRedirect, setRecommendedRedirect] = useState(null);

  // Magnetic Cursor Effect Ref and State
  const orbRef = useRef(null);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);
  const isSendingRef = useRef(false);
  const abortControllerRef = useRef(null);

  // Welcome message content
  const welcomeText = 
    "👋 Welcome to CittaAI\n\n" +
    "I'm your Enterprise AI Consultant.\n\n" +
    "I can help you explore:\n\n" +
    "• **Products**\n" +
    "• **Services**\n" +
    "• **AI Solutions**\n" +
    "• **Company Information**\n" +
    "• **Technologies**\n" +
    "• **Achievements**\n" +
    "• **Contact Details**\n\n" +
    "How may I assist you today?";

  // Quick Action Chips (12 requested)
  const quickActions = [
    { label: "About CittaAI", action: "Tell me about CittaAI company, mission, and vision." },
    { label: "AI Services", action: "What AI services does CittaAI provide?" },
    { label: "Enterprise AI", action: "Tell me about CittaAI Enterprise AI OS solutions." },
    { label: "Agentic AI", action: "Explain CittaAI Agentic AI capabilities." },
    { label: "WhatsApp Automation", action: "Explain WhatsApp Marketing Platform details." },
    { label: "Pharma Suite", action: "What features are in the Pharma AI Suite?" },
    { label: "GovTech", action: "What Smart Cities and GovTech solutions do you have?" },
    { label: "Data Engineering", action: "What are your data engineering capabilities?" },
    { label: "Recognition", action: "What achievements and ISO certifications does CittaAI hold?" },
    { label: "Case Studies", action: "Show me some customer success metrics and case studies." },
    { label: "Book Strategy Call", action: "How do I book a strategy call or get in contact?" },
    { label: "Contact Us", action: "What is CittaAI's contact number, email, and address?" }
  ];

  // Dispatch custom window event when chatbot state changes for external listeners (e.g. Hero Robot Concierge)
  useEffect(() => {
    window.dispatchEvent(new CustomEvent("cittaai_chat_toggle", { detail: { isOpen } }));
  }, [isOpen]);

  // 1. Magnetic cursor effect tracking
  useEffect(() => {
    const handleMouseMove = (e) => {
      if (isOpen || !orbRef.current) return;

      const rect = orbRef.current.getBoundingClientRect();
      const orbX = rect.left + rect.width / 2;
      const orbY = rect.top + rect.height / 2;

      const distX = e.clientX - orbX;
      const distY = e.clientY - orbY;
      const distance = Math.sqrt(distX * distX + distY * distY);

      const threshold = 120; // Snapping radius
      if (distance < threshold) {
        // Pull orb towards the cursor (magnetic intensity 0.35)
        setPosition({
          x: distX * 0.35,
          y: distY * 0.35
        });
      } else {
        // Snap back smoothly
        setPosition({ x: 0, y: 0 });
      }
    };

    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, [isOpen]);

  // Scroll to bottom helper
  const scrollToBottom = () => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTo({
        top: messagesContainerRef.current.scrollHeight,
        behavior: "smooth"
      });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  // Abort ongoing streams on location/path changes
  useEffect(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
  }, [location.pathname]);

  // Cleanup abort controller on component unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);


  // Immediately display static welcome message when chatbot is opened
  const triggerWelcome = () => {
    if (messages.length > 0) return;
    setMessages([
      {
        id: "welcome",
        sender: "bot",
        text: welcomeText,
        timestamp: new Date()
      }
    ]);
  };

  const handleOpen = () => {
    setIsExpanding(true);
    // Expand transition timing
    setTimeout(() => {
      setIsOpen(true);
      setIsExpanding(false);
      triggerWelcome();
    }, 450);
  };

  const handleMinimize = () => {
    setIsOpen(false);
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
  };

  const handleClose = () => {
    setIsOpen(false);
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    // Clear chat history & state
    setMessages([]);
    setCitations([]);
    setSuggestions([]);
    setRecommendedRedirect(null);
    setInputValue("");
    
    // Generate new Session ID
    const newId = "session_" + Math.random().toString(36).substring(2, 15);
    localStorage.setItem("cittaai_consultant_session_id", newId);
    setSessionId(newId);
  };

  // 2. Dynamic Scroll & Highlight Navigation
  const performNavigationAndHighlight = (path) => {
    if (!path) return;
    
    // Check if the path is external/contact vs internal route
    if (path.startsWith("/")) {
      navigate(path);
      
      // Wait for page transition, then search DOM for keywords and scroll
      setTimeout(() => {
        // Dynamic search of terms on page load
        let targetKeywords = [];
        if (path.includes("whatsapp")) targetKeywords = ["WhatsApp", "Onboarding", "Broadcasting"];
        else if (path.includes("pharma")) targetKeywords = ["Quality Dashboards", "BMR", "APQR"];
        else if (path.includes("enterprise")) targetKeywords = ["RAG", "Agentic", "Voice", "Knowledge Graph"];
        else if (path.includes("data-engineering")) targetKeywords = ["pipeline", "warehouse", "integration"];
        else if (path.includes("contact")) targetKeywords = ["Address", "info@cittaai.com", "Phone"];
        else if (path.includes("recognition")) targetKeywords = ["MSME", "ISO", "Startup India"];
        else if (path.includes("case-studies")) targetKeywords = ["Jewellery", "Spices", "ROI"];

        // Find matches in page
        for (const kw of targetKeywords) {
          const xpath = `//*[text()[contains(., '${kw}')]]`;
          const result = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
          const element = result.singleNodeValue;
          
          if (element) {
            // Find parent div or card container to scroll to (usually 1-3 levels up)
            let container = element;
            if (element.parentElement && (element.tagName === "H3" || element.tagName === "SPAN" || element.tagName === "P")) {
              container = element.parentElement;
              if (container.parentElement && container.tagName === "DIV" && container.classList.contains("flex")) {
                container = container.parentElement;
              }
            }
            
            container.scrollIntoView({ behavior: "smooth", block: "center" });
            
            // Apply flashing neon highlight
            container.classList.add("neon-highlight");
            setTimeout(() => {
              container.classList.remove("neon-highlight");
            }, 3000);
            break; // Stop at first matched target
          }
        }
      }, 500);
    }
  };

  // 3. POST-Based SSE Chat Streaming Client
  const sendMessage = async (textToSend) => {
    if (!textToSend.trim() || isSendingRef.current) return;
    
    // Abort previous fetch/stream if active
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    
    isSendingRef.current = true;
    // Add user message to state
    const userMsgId = "msg_" + Date.now();
    const userMsg = { id: userMsgId, sender: "user", text: textToSend, timestamp: new Date() };
    setMessages((prev) => [...prev, userMsg]);
    setInputValue("");
    setIsTyping(true);
    setIsStreaming(true);
    setHasReceivedFirstToken(false);
    
    // Reset state parameters
    setCitations([]);
    setSuggestions([]);
    setRecommendedRedirect(null);

    const botMsgId = "msg_bot_" + Date.now();
    const botMsg = { id: botMsgId, sender: "bot", text: "", timestamp: new Date() };
    setActiveBotMsgId(botMsgId);
    setMessages((prev) => [...prev, botMsg]);

    let flushInterval = null;
    
    // Create new abort controller
    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, message: textToSend }),
        signal: controller.signal
      });

      if (!response.ok) {
        throw new Error(`Server returned error code: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      
      let rawBuffer = "";      // Line buffer for incoming stream data
      let pendingBuffer = "";  // Text accumulator buffer before flushing
      let streamedAnswer = ""; // Currently rendered bot response text
      
      let lastFlushTime = Date.now();

      // Flushes text at word boundaries to prevent partial words from rendering
      const flushPending = (force = false) => {
        if (controller.signal.aborted) return;
        if (!pendingBuffer) return;

        // Find last word boundary index: space, newline or punctuation
        const lastIndex = Math.max(
          pendingBuffer.lastIndexOf(" "),
          pendingBuffer.lastIndexOf("\n"),
          pendingBuffer.lastIndexOf("."),
          pendingBuffer.lastIndexOf(","),
          pendingBuffer.lastIndexOf("!"),
          pendingBuffer.lastIndexOf("?"),
          pendingBuffer.lastIndexOf(";"),
          pendingBuffer.lastIndexOf(":"),
          pendingBuffer.lastIndexOf("-")
        );

        let toFlush = "";

        if (force) {
          toFlush = pendingBuffer;
          pendingBuffer = "";
        } else {
          const timeSinceLastFlush = Date.now() - lastFlushTime;
          const charCount = pendingBuffer.length;

          if (lastIndex !== -1) {
            toFlush = pendingBuffer.slice(0, lastIndex + 1);
            pendingBuffer = pendingBuffer.slice(lastIndex + 1);
          } else if (charCount >= 30 || timeSinceLastFlush >= 60) {
            // Safe fallback to prevent locking up on long contiguous strings
            toFlush = pendingBuffer;
            pendingBuffer = "";
          }
        }

        if (toFlush) {
          streamedAnswer += toFlush;
          lastFlushTime = Date.now();
          setMessages((prev) => 
            prev.map((m) => (m.id === botMsgId ? { ...m, text: streamedAnswer } : m))
          );
        }
      };

      // Periodic update cycle to flush complete tokens smoothly (batched to 60ms)
      flushInterval = setInterval(() => {
        if (!controller.signal.aborted) {
          flushPending(false);
        }
      }, 60);

      while (true) {
        if (controller.signal.aborted) break;
        const { value, done } = await reader.read();
        if (controller.signal.aborted) break;
        
        // Decode chunk safely keeping multibyte split characters buffered
        const chunkText = decoder.decode(value || new Uint8Array(), { stream: true });
        rawBuffer += chunkText;

        const lines = rawBuffer.split("\n");
        rawBuffer = lines.pop() || ""; // Retain incomplete line

        for (const line of lines) {
          if (controller.signal.aborted) break;
          const trimmed = line.trim();
          if (trimmed.startsWith("data: ")) {
            const dataStr = trimmed.slice(6).trim();
            if (!dataStr) continue;

            try {
              const data = JSON.parse(dataStr);
              if (data.text) {
                setHasReceivedFirstToken(true);
                pendingBuffer += data.text;
              }
              if (data.done) {
                // Read final payload metadata
                if (data.citations) setCitations(data.citations);
                if (data.suggested_questions) setSuggestions(data.suggested_questions);
                if (data.preferences) setPreferences(data.preferences);
                if (data.redirect) {
                  setRecommendedRedirect(data.redirect);
                  performNavigationAndHighlight(data.redirect);
                } else {
                  setRecommendedRedirect(null);
                }
              }
            } catch (err) {
              // Ignore split line JSON parse issues
            }
          }
        }

        if (done) {
          if (controller.signal.aborted) break;
          
          // Flush any remaining decoder state
          const finalChunk = decoder.decode(new Uint8Array(), { stream: false });
          rawBuffer += finalChunk;

          // Process any remaining tail content
          if (rawBuffer.trim().startsWith("data: ")) {
            const dataStr = rawBuffer.trim().slice(6).trim();
            try {
              const data = JSON.parse(dataStr);
              if (data.done) {
                if (data.citations) setCitations(data.citations);
                if (data.suggested_questions) setSuggestions(data.suggested_questions);
                if (data.preferences) setPreferences(data.preferences);
                if (data.redirect) {
                  setRecommendedRedirect(data.redirect);
                  performNavigationAndHighlight(data.redirect);
                } else {
                  setRecommendedRedirect(null);
                }
              } else if (data.text) {
                setHasReceivedFirstToken(true);
                pendingBuffer += data.text;
              }
            } catch (e) {}
          }
          
          if (flushInterval) {
            clearInterval(flushInterval);
            flushInterval = null;
          }
          flushPending(true); // Final force flush of remaining text
          break;
        }
      }
    } catch (error) {
      if (error.name === "AbortError") {
        console.log("Chat stream connection aborted.");
        return;
      }
      console.error("Failed to stream answer:", error);
      setMessages((prev) => 
        prev.map((m) => 
          m.id === botMsgId 
            ? { ...m, text: "I encountered a connection error. Please verify the CittaAI backend service is operational and try again." } 
            : m
        )
      );
    } finally {
      if (flushInterval) clearInterval(flushInterval);
      setIsTyping(false);
      setIsStreaming(false);
      setHasReceivedFirstToken(false);
      setActiveBotMsgId(null);
      isSendingRef.current = false;
      if (abortControllerRef.current === controller) {
        abortControllerRef.current = null;
      }
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      sendMessage(inputValue);
    }
  };

  const renderInline = (str) => {
    if (!str) return null;
    let parts = str.split(/(`[^`]+`|\*\*[^*]+\*\*)/g);
    return parts.map((part, index) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return <strong key={index} className="text-ink font-semibold">{part.slice(2, -2)}</strong>;
      }
      if (part.startsWith("`") && part.endsWith("`")) {
        return <code key={index} className="bg-accent/20 border border-accent/30 px-1.5 py-0.5 rounded text-accent text-xs font-mono">{part.slice(1, -1)}</code>;
      }
      return part;
    });
  };

  const formatText = (text) => {
    if (!text) return null;

    const lines = text.split("\n");
    const blocks = [];
    let currentTable = null;
    let currentList = null;

    const flushTable = () => {
      if (currentTable) {
        blocks.push({ type: "table", ...currentTable });
        currentTable = null;
      }
    };

    const flushList = () => {
      if (currentList) {
        blocks.push({ type: "list", items: currentList });
        currentList = null;
      }
    };

    lines.forEach((line) => {
      const trimmed = line.trim();

      // Table row detection
      const isTableRow = trimmed.startsWith("|") && (trimmed.endsWith("|") || trimmed.includes("|"));
      const isTableSeparator = isTableRow && /^\|[\s:\-|\+]+\|$/.test(trimmed);

      if (isTableRow) {
        flushList();
        if (isTableSeparator) {
          return;
        }
        const cells = trimmed
          .split("|")
          .map((c) => c.trim())
          .filter((_, idx, arr) => idx > 0 && idx < arr.length - 1);

        if (cells.length > 0) {
          if (!currentTable) {
            currentTable = { headers: cells, rows: [] };
          } else {
            currentTable.rows.push(cells);
          }
          return;
        }
      } else {
        flushTable();
      }

      // Bullet list detection
      const isBullet = /^(?:[\-\*•]|\d+\.)\s+(.+)/.exec(trimmed);
      if (isBullet) {
        if (!currentList) currentList = [];
        currentList.push(isBullet[1]);
        return;
      } else {
        flushList();
      }

      // Heading detection
      if (trimmed.startsWith("#") || /^[\*]{2}[^\*]+[\*]{2}$/.test(trimmed)) {
        const headingText = trimmed.replace(/^#+\s*/, "").replace(/^\*\*/, "").replace(/\*\*$/, "");
        blocks.push({ type: "heading", text: headingText });
        return;
      }

      // Regular paragraph
      if (trimmed.length > 0) {
        blocks.push({ type: "paragraph", text: trimmed });
      }
    });

    flushTable();
    flushList();

    return (
      <div className="space-y-2">
        {blocks.map((block, i) => {
          if (block.type === "table") {
            return (
              <div key={i} className="my-2.5 overflow-x-auto rounded-xl border border-line/20 bg-surface2 shadow-inner">
                <table className="w-full border-collapse text-xs text-left">
                  <thead>
                    <tr className="bg-accent/20 border-b border-line/20 text-accent font-semibold">
                      {block.headers.map((h, hIdx) => (
                        <th key={hIdx} className="py-2 px-3 whitespace-nowrap">{renderInline(h)}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-line/10">
                    {block.rows.map((row, rIdx) => (
                      <tr key={rIdx} className="hover:bg-ink/5 transition-colors">
                        {row.map((cell, cIdx) => (
                          <td key={cIdx} className="py-2 px-3 text-ink-soft">{renderInline(cell)}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            );
          }

          if (block.type === "heading") {
            return (
              <h4 key={i} className="text-sm font-bold text-ink mt-3 mb-1 flex items-center gap-1.5 border-b border-line/15 pb-1">
                {renderInline(block.text)}
              </h4>
            );
          }

          if (block.type === "list") {
            return (
              <ul key={i} className="my-1.5 space-y-1 pl-1">
                {block.items.map((item, itemIdx) => (
                  <li key={itemIdx} className="flex items-start gap-2 text-xs text-ink-soft leading-relaxed">
                    <span className="w-1.5 h-1.5 rounded-full bg-accent mt-1.5 flex-shrink-0" />
                    <span>{renderInline(item)}</span>
                  </li>
                ))}
              </ul>
            );
          }

          return (
            <p key={i} className="text-sm leading-relaxed text-ink-soft">
              {renderInline(block.text)}
            </p>
          );
        })}
      </div>
    );
  };

  return (
    <>
      <AnimatePresence>
        {/* Floating Orb State (only shown when chatbot closed) */}
        {!isOpen && !isExpanding && (
          <div className="fixed bottom-4 right-4 sm:bottom-6 sm:right-6 z-[9999]">
            {/* Ambient Ambient Outer Ring and Glow */}
            <div className="absolute inset-[-10px] rounded-full bg-accent/10 blur-[15px] pointer-events-none" />
            
            {/* Orbiting particles */}
            <div className="orbit-particle orbit-particle-1" />
            <div className="orbit-particle orbit-particle-2" />

            <motion.div
              ref={orbRef}
              className="liquid-orb-container"
              onClick={handleOpen}
              style={{ x: position.x, y: position.y }}
              whileHover={{ scale: 1.08 }}
              whileTap={{ scale: 0.95 }}
            >
              <div className="liquid-orb">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {/* Expanded Glass Panel UI */}
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.85, y: 100 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.85, y: 100 }}
            transition={{ type: "spring", damping: 25, stiffness: 180 }}
            className="fixed bottom-4 right-4 sm:bottom-6 sm:right-6 z-[9999] w-[calc(100vw-32px)] sm:w-[420px] h-[calc(100vh-100px)] sm:h-[640px] max-h-[640px] rounded-2xl glass-strong border border-line/15 shadow-2xl flex flex-col overflow-hidden text-ink"
          >
            {/* Panel Ambient Aurora Backgrounds */}
            <div className="absolute inset-0 bg-gradient-to-b from-accent/5 to-transparent pointer-events-none" />
            <div className="absolute -top-[10%] -left-[10%] w-[50%] h-[50%] bg-accent/10 rounded-full blur-[50px] pointer-events-none" />
            <div className="absolute -bottom-[10%] -right-[10%] w-[50%] h-[50%] bg-jade/5 rounded-full blur-[50px] pointer-events-none" />

            {/* Header */}
            <div className="relative z-20 px-6 py-4 flex items-center justify-between border-b border-line/10 bg-ink/5 backdrop-blur-md">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-full bg-accent/20 border border-accent/30 flex items-center justify-center">
                  <Sparkles className="w-5 h-5 text-accent" />
                </div>
                <div>
                  <h4 className="text-sm font-semibold tracking-wide text-ink">CittaAI Consultant</h4>
                  <div className="flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-jade animate-pulse" />
                    <span className="text-[10px] uppercase font-semibold text-ink-muted tracking-wider">Enterprise Intelligence</span>
                  </div>
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                <button 
                  onClick={handleMinimize}
                  title="Minimize"
                  className="w-9 h-9 rounded-full border border-line/10 hover:border-line/15 bg-ink/5 hover:bg-ink/10 flex items-center justify-center transition-all duration-200 cursor-pointer"
                >
                  <span className="text-[12px] font-bold text-ink-muted hover:text-ink tracking-tighter select-none pointer-events-none">
                    {"><"}
                  </span>
                </button>
                <button 
                  onClick={handleClose}
                  title="Close & Reset Chat"
                  className="w-9 h-9 rounded-full border border-line/10 hover:border-line/15 bg-ink/5 hover:bg-ink/10 flex items-center justify-center transition-all duration-200 cursor-pointer"
                >
                  <X className="w-4.5 h-4.5 text-ink-muted hover:text-ink pointer-events-none" />
                </button>
              </div>
            </div>

            {/* Body / Scrollable Messages */}
            <div 
              ref={messagesContainerRef}
              className="flex-1 overflow-y-auto px-6 py-4 space-y-4 custom-scrollbar relative z-10"
            >
              {messages.map((m) => (
                <div 
                  key={m.id}
                  className={`flex gap-3 ${m.sender === "user" ? "justify-end" : "justify-start"}`}
                >
                  {m.sender === "bot" && (
                    <div className="w-7 h-7 rounded-full border border-accent/20 bg-accent/20 flex items-center justify-center flex-shrink-0 mt-1">
                      <Bot className="w-4.5 h-4.5 text-accent" />
                    </div>
                  )}

                  <div className="max-w-[82%]">
                    <div className={`p-3.5 rounded-2xl text-sm ${
                      m.sender === "user" 
                        ? "bg-accent border border-accent/30 text-accent-ink [&_*]:!text-accent-ink rounded-tr-none shadow-md"
                        : "bg-ink/4 border border-line/13 text-ink-soft rounded-tl-none"
                    }`}>
                      {m.sender === "bot" && isStreaming && m.id === activeBotMsgId && !hasReceivedFirstToken ? (
                        <div className="flex items-center gap-1.5 py-1 px-0.5">
                          <span className="w-2 h-2 rounded-full bg-ink-muted animate-bounce" />
                          <span className="w-2 h-2 rounded-full bg-ink-muted animate-bounce [animation-delay:0.2s]" />
                          <span className="w-2 h-2 rounded-full bg-ink-muted animate-bounce [animation-delay:0.4s]" />
                        </div>
                      ) : (
                        formatText(m.text)
                      )}
                    </div>
                    
                    {/* Timestamp */}
                    <span className={`text-[10px] text-ink-muted mt-1 block px-1 ${
                      m.sender === "user" ? "text-right" : "text-left"
                    }`}>
                      {m.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                </div>
              ))}

              {isTyping && messages[messages.length - 1]?.text === "" && messages[messages.length - 1]?.id !== activeBotMsgId && (
                <div className="flex gap-3 justify-start">
                  <div className="w-7 h-7 rounded-full border border-accent/20 bg-accent/20 flex items-center justify-center flex-shrink-0">
                    <Bot className="w-4.5 h-4.5 text-accent" />
                  </div>
                  <div className="bg-ink/4 border border-line/13 rounded-2xl rounded-tl-none p-3.5 flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-ink-muted animate-bounce" />
                    <span className="w-2 h-2 rounded-full bg-ink-muted animate-bounce [animation-delay:0.2s]" />
                    <span className="w-2 h-2 rounded-full bg-ink-muted animate-bounce [animation-delay:0.4s]" />
                  </div>
                </div>
              )}



              {/* Recommended Redirect Webpage CTA Button */}
              {!isTyping && recommendedRedirect && (
                <motion.div 
                  initial={{ scale: 0.95, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  className="pt-1"
                >
                  <button 
                    onClick={() => performNavigationAndHighlight(recommendedRedirect)}
                    className="w-full py-2.5 px-4 rounded-xl bg-accent hover:brightness-110 text-accent-ink text-xs font-semibold flex items-center justify-between shadow-lg  border border-accent/30 transition-all duration-200 cursor-pointer group"
                  >
                    <span className="flex items-center gap-2">
                      <Globe className="w-4 h-4 text-accent group-hover:text-ink" />
                      <span>View Webpage ({recommendedRedirect})</span>
                    </span>
                    <ArrowRight className="w-3.5 h-3.5 text-accent group-hover:translate-x-0.5 transition-transform" />
                  </button>
                </motion.div>
              )}

              {/* suggested follow up questions */}
              {!isTyping && suggestions.length > 0 && (
                <div className="pt-2 space-y-2">
                  <span className="text-[10px] font-semibold text-ink-muted uppercase tracking-wider block">Suggested Questions</span>
                  <div className="flex flex-col gap-2">
                    {suggestions.map((q, i) => (
                      <button 
                        key={i}
                        onClick={() => sendMessage(q)}
                        className="text-left text-xs p-2.5 rounded-xl border border-line/10 hover:border-accent/30 bg-ink/3 hover:bg-accent/8 text-ink-soft hover:text-accent transition-all duration-150"
                      >
                        {q}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Quick Actions Scroll Area */}
            {messages.length === 1 && !isTyping && (
              <div className="relative z-10 px-6 py-2 border-t border-line/10 bg-surface2">
                <span className="text-[10px] font-semibold text-ink-muted uppercase tracking-wider block mb-2">Frequently Asked</span>
                <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-none">
                  {quickActions.map((item, idx) => (
                    <button
                      key={idx}
                      onClick={() => sendMessage(item.action)}
                      className="whitespace-nowrap px-3 py-1.5 rounded-full border border-line/13 hover:border-accent/30 bg-ink/3 hover:bg-accent/10 text-xs text-ink-soft hover:text-accent transition-all duration-150"
                    >
                      {item.label}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Input Form */}
            <div className="relative z-10 p-4 border-t border-line/10 bg-surface2 flex gap-2">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder="Ask me about CittaAI capabilities..."
                className="flex-1 px-4 py-2.5 rounded-xl border border-line/15 focus:border-accent/50 bg-surface text-sm placeholder:text-ink-muted text-ink outline-none focus:ring-1 focus:ring-accent/20 transition-all"
               
              />
              <button
                onClick={() => sendMessage(inputValue)}
                disabled={!inputValue.trim() || isTyping}
                className="w-10 h-10 rounded-xl bg-accent hover:brightness-110 disabled:bg-ink/10 disabled:text-ink-muted text-accent-ink flex items-center justify-center transition-all shadow-md  border border-accent/20"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
