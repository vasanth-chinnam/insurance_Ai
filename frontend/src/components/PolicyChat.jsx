import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ShieldCheck, MessageSquare, FileText, Paperclip, Send, Trash2, Copy, Check } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import confetti from 'canvas-confetti'

const QUICK_ACTIONS = [
  { icon: ShieldCheck, title: 'Policy Coverage', desc: 'What does my health insurance policy cover?', query: 'What does my health insurance policy cover?' },
  { icon: FileText, title: 'Prescription Drugs', desc: 'Check medication coverage tiers', query: 'What are the prescription drug copays?' },
  { icon: FileText, title: 'Auto Claims', desc: 'Learn about collision coverage', query: 'What is covered under collision coverage?' },
]

export default function PolicyChat({ messages, setMessages, API_BASE, showToast }) {
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [copiedId, setCopiedId] = useState(null)
  
  const messagesEndRef = useRef(null)
  const fileInputRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, loading])

  const handleCopy = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  }

  const sendMessage = async (text) => {
    const query = text || input.trim()
    if (!query) return

    setInput('')

    const userMsg = {
      id: Date.now(),
      role: 'user',
      content: query,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }
    setMessages(prev => [...prev, userMsg])
    setLoading(true)

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      })
      const data = await res.json()

      const botMsg = {
        id: Date.now() + 1,
        role: 'bot',
        content: data.answer,
        sources: data.sources || [],
        route: data.route,
        confidence: data.confidence || 'Medium',
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }
      setMessages(prev => [...prev, botMsg])
    } catch (err) {
      console.error(err)
      const errMsg = {
        id: Date.now() + 1,
        role: 'bot',
        content: '❌ Could not reach the AI backend. Make sure the server is running on port 8000.',
        sources: [],
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }
      setMessages(prev => [...prev, errMsg])
    } finally {
      setLoading(false)
    }
  }

  const handleUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    const formData = new FormData()
    formData.append('file', file)

    const sysMsg = {
      id: Date.now(),
      role: 'system',
      content: `📤 Uploading "${file.name}"...`,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }
    setMessages(prev => [...prev, sysMsg])

    try {
      const res = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData,
      })
      const data = await res.json()

      if (data.status === 'success') {
        const okMsg = {
          id: Date.now() + 1,
          role: 'system',
          content: `✅ "${data.filename}" indexed successfully (${data.chunks} chunks). You can now ask questions about this document!`,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        }
        setMessages(prev => [...prev, okMsg])
        showToast(`${data.filename} uploaded successfully!`)
        confetti({
          particleCount: 100,
          spread: 70,
          origin: { y: 0.6 },
          colors: ['#6366f1', '#4f46e5', '#10b981']
        })
      } else {
        showToast(`Upload failed: ${data.status}`, 'error')
      }
    } catch (err) {
      console.error(err)
      showToast('Failed to upload file', 'error')
    }

    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const clearChat = async () => {
    setMessages([])
    try {
      await fetch(`${API_BASE}/history`, { method: 'DELETE' })
    } catch (err) { }
  }

  return (
    <>
      <header className="chat-header">
        <div>
          <h1>Policy Q&A Assistant</h1>
          <div className="subtitle">Instant answers from your policy documents</div>
        </div>
        <div className="header-actions">
          <button className="btn-icon" title="Clear chat" onClick={clearChat}>
            <Trash2 size={18} />
          </button>
        </div>
      </header>

      <div className="messages-container">
        <AnimatePresence mode='wait'>
          {messages.length === 0 ? (
            <motion.div 
              key="welcome"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="welcome-screen"
            >
              <div className="welcome-icon">
                <ShieldCheck size={48} />
              </div>
              <h2>How can I help you today?</h2>
              <p>Upload your insurance policy PDFs to get instant, accurate answers about coverage.</p>
              <div className="quick-actions">
                {QUICK_ACTIONS.map((qa, i) => (
                  <motion.div 
                    key={i} 
                    whileHover={{ y: -4, boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)' }}
                    whileTap={{ scale: 0.98 }}
                    className="quick-action" 
                    onClick={() => sendMessage(qa.query)}
                  >
                    <div className="qa-icon"><qa.icon size={24} className="text-primary" /></div>
                    <div className="qa-title">{qa.title}</div>
                    <div className="qa-desc">{qa.desc}</div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          ) : (
            <div className="messages-list">
              {messages.map((msg) => (
                <motion.div key={msg.id} initial={{ opacity: 0, x: msg.role === 'user' ? 20 : -20 }} animate={{ opacity: 1, x: 0 }} className={`message ${msg.role}`}>
                  <div className="message-avatar">
                    {msg.role === 'user' ? <ShieldCheck size={18} /> : msg.role === 'system' ? <FileText size={18} /> : <MessageSquare size={18} />}
                  </div>
                  <div className="message-content">
                    <div className="message-bubble">
                      {msg.role === 'bot' ? (
                        <div className="bot-bubble-wrapper">
                          <div className="markdown-body">
                            <ReactMarkdown>{msg.content}</ReactMarkdown>
                          </div>
                          <div className="bubble-actions">
                            <button className="btn-copy" onClick={() => handleCopy(msg.content, msg.id)}>
                              {copiedId === msg.id ? <Check size={14} color="#10b981" /> : <Copy size={14} />}
                              <span>{copiedId === msg.id ? 'Copied!' : 'Copy'}</span>
                            </button>
                          </div>
                        </div>
                      ) : (
                        msg.content
                      )}
                      
                      {msg.sources && msg.sources.length > 0 && msg.role === 'bot' && (
                        <div className="clean-sources">
                          {msg.sources.slice(0, 1).map((src, i) => (
                            <div key={i} className="clean-source-item">📄 Source: {src.page ? `${src.page}, ` : ''}{src.section || 'Document Extract'}</div>
                          ))}
                        </div>
                      )}
                      {msg.confidence && msg.role === 'bot' && (
                        <div className="clean-confidence">🧠 Policy AI | Confidence: {msg.confidence}</div>
                      )}
                    </div>
                    <div className="message-time">{msg.time}</div>
                  </div>
                </motion.div>
              ))}
              {loading && (
                <motion.div className="typing-state">
                  <div className="message-avatar" style={{ background: 'var(--primary-light)' }}><span style={{ fontSize: '1.2rem' }}>🤖</span></div>
                  <div className="typing-text">Thinking...</div>
                </motion.div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </AnimatePresence>
      </div>

      <div className="input-bar">
        <div className="input-wrapper">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !loading && sendMessage()}
            placeholder="Type your question here..."
            disabled={loading}
          />
          <input
            type="file"
            ref={fileInputRef}
            accept=".pdf,.txt,.md"
            onChange={handleUpload}
            style={{ display: 'none' }}
          />
          <button className="btn-upload" title="Upload document" onClick={() => fileInputRef.current?.click()}><Paperclip size={20} /></button>
          <button className="btn-send" onClick={() => sendMessage()} disabled={loading || !input.trim()} title="Send message"><Send size={18} /></button>
        </div>
        <div className="input-hint">AI-powered answers can occasionally be inaccurate. Please verify important details.</div>
      </div>
    </>
  )
}
