import React, { useState, useEffect, useRef } from 'react'
import { sendIntakeMessage, confirmProfile, matchSchemes } from '../api'

export default function ChatIntake({ profile, setProfile, setMatchedSchemes, setSelectedScheme, setTab, t, lang }) {
  const [messages, setMessages] = useState([])
  const [inputText, setInputText] = useState('')
  const [listening, setListening] = useState(false)
  const [currentOptions, setCurrentOptions] = useState([])
  const [loading, setLoading] = useState(false)
  const [readyToConfirm, setReadyToConfirm] = useState(false)
  const chatEndRef = useRef(null)
  const recognitionRef = useRef(null)

  // Initialize session on mount
  useEffect(() => {
    initChat()
  }, [lang])

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, currentOptions])

  async function initChat() {
    setLoading(true)
    const res = await sendIntakeMessage({
      sessionId: 'user-session',
      message: '',
      language: lang
    })
    setLoading(false)

    if (res) {
      setMessages([
        {
          sender: 'agent',
          text: lang === 'ta' ? res.reply_ta : res.reply,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          schemes: res.matched_schemes || []
        }
      ])
      setCurrentOptions(res.menu_options || [])
      setProfile(res.profile)
      setReadyToConfirm(res.ready_for_confirmation)
      if (res.matched_schemes && res.matched_schemes.length > 0) {
        setMatchedSchemes(res.matched_schemes)
        if (setSelectedScheme) setSelectedScheme(res.matched_schemes[0])
      }
    }
  }

  // Web Speech API Voice Toggle
  function toggleMic() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      alert(t.intake.micUnsupported)
      return
    }

    if (listening) {
      recognitionRef.current?.stop()
      setListening(false)
      return
    }

    try {
      const rec = new SpeechRecognition()
      rec.lang = lang === 'ta' ? 'ta-IN' : 'en-IN'
      rec.interimResults = false
      rec.continuous = false

      rec.onstart = () => setListening(true)
      rec.onresult = (e) => {
        const transcript = e.results[0][0].transcript
        setInputText(transcript)
        handleUserMessage(transcript)
      }
      rec.onerror = (e) => {
        console.warn('Speech recognition error:', e.error)
        setListening(false)
      }
      rec.onend = () => setListening(false)

      recognitionRef.current = rec
      rec.start()
    } catch (err) {
      console.error('Speech recognition failed to start:', err)
      setListening(false)
    }
  }

  async function handleUserMessage(text) {
    if (!text.trim()) return

    const userMsg = {
      sender: 'user',
      text: text.trim(),
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }

    setMessages((prev) => [...prev, userMsg])
    setInputText('')
    setLoading(true)

    const res = await sendIntakeMessage({
      sessionId: 'user-session',
      message: text,
      language: lang
    })
    setLoading(false)

    if (res) {
      setMessages((prev) => [
        ...prev,
        {
          sender: 'agent',
          text: lang === 'ta' ? res.reply_ta : res.reply,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          schemes: res.matched_schemes || []
        }
      ])
      setCurrentOptions(res.menu_options || [])
      setProfile(res.profile)
      setReadyToConfirm(res.ready_for_confirmation)
      if (res.matched_schemes && res.matched_schemes.length > 0) {
        setMatchedSchemes(res.matched_schemes)
        if (setSelectedScheme) setSelectedScheme(res.matched_schemes[0])
      }
    }
  }

  async function handleOptionClick(opt) {
    if (opt.id === 100) {
      setTab('schemes')
      return
    }

    const userMsg = {
      sender: 'user',
      text: lang === 'ta' ? opt.label_ta : opt.label,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
    setMessages((prev) => [...prev, userMsg])
    setLoading(true)

    const res = await sendIntakeMessage({
      sessionId: 'user-session',
      menuChoice: opt.id,
      language: lang
    })
    setLoading(false)

    if (res) {
      setMessages((prev) => [
        ...prev,
        {
          sender: 'agent',
          text: lang === 'ta' ? res.reply_ta : res.reply,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          schemes: res.matched_schemes || []
        }
      ])
      setCurrentOptions(res.menu_options || [])
      setProfile(res.profile)
      setReadyToConfirm(res.ready_for_confirmation)
      if (res.matched_schemes && res.matched_schemes.length > 0) {
        setMatchedSchemes(res.matched_schemes)
        if (setSelectedScheme) setSelectedScheme(res.matched_schemes[0])
      }
    }
  }

  async function handleConfirmAndMatch() {
    setLoading(true)
    await confirmProfile(profile)
    const matchRes = await matchSchemes(profile)
    setLoading(false)

    if (matchRes && matchRes.schemes) {
      const eligible = matchRes.schemes.filter((s) => s.eligible)
      setMatchedSchemes(matchRes.schemes)
      if (setSelectedScheme && eligible.length > 0) {
        setSelectedScheme(eligible[0])
      }
      setMessages((prev) => [
        ...prev,
        {
          sender: 'agent',
          text: lang === 'ta'
            ? `🎉 உங்கள் விவரங்கள் உறுதிசெய்யப்பட்டன! நீங்கள் ${eligible.length} அரசு உதவித்தொகை திட்டங்களுக்கு தகுதி பெற்றுள்ளீர்கள். கீழே உள்ள திட்டங்களை பார்வையிடலாம்:`
            : `🎉 Profile confirmed! You are eligible for ${eligible.length} government scholarship scheme(s). You can explore each verified scheme below:`,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          schemes: eligible
        }
      ])
      setTab('schemes')
    }
  }

  async function handleReset() {
    await sendIntakeMessage({ sessionId: 'user-session', message: 'reset' })
    initChat()
  }

  const isComplete = profile.completed_class && profile.gender && profile.income && profile.category

  return (
    <section className="section wrap">
      <div className="section-head">
        <h2>{t.intake.title}</h2>
        <p>{t.intake.subtitle}</p>
      </div>

      <div className="intake-layout">
        {/* Chat Window */}
        <div className="chat-card">
          <div className="chat-header">
            <div className="chat-header-title">
              <span style={{ fontSize: '1.2rem' }}>🤖</span>
              <span>SETU Intake Agent</span>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10B981', display: 'inline-block' }} />
            </div>
            <button
              type="button"
              onClick={handleReset}
              style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', fontSize: '0.8rem', cursor: 'pointer', textDecoration: 'underline' }}
            >
              {t.intake.btnReset}
            </button>
          </div>

          <div className="chat-body">
            {messages.map((m, idx) => (
              <div key={idx} className={`bubble ${m.sender}`}>
                <p style={{ whiteSpace: 'pre-line' }}>{m.text}</p>

                {/* Matched Schemes Cards inside Chat Bubble */}
                {m.schemes && m.schemes.length > 0 && (
                  <div style={{ marginTop: '14px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#1E40AF', background: '#DBEAFE', padding: '4px 10px', borderRadius: '6px' }}>
                      🎓 {lang === 'ta' ? 'உங்களுக்கான உதவித்தொகை திட்டங்கள்' : 'Matched Government Schemes for You'} ({m.schemes.length})
                    </div>
                    {m.schemes.map((scheme) => (
                      <div
                        key={scheme.scheme_id}
                        style={{
                          background: '#FFFFFF',
                          border: '1.5px solid #CBD5E1',
                          borderRadius: '10px',
                          padding: '12px',
                          boxShadow: '0 2px 5px rgba(0,0,0,0.05)',
                          color: '#1E293B',
                          textAlign: 'left'
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px' }}>
                          <h4 style={{ fontSize: '0.92rem', fontWeight: 800, color: '#1E293B', margin: 0, lineHeight: 1.3 }}>
                            {lang === 'ta' && scheme.name_ta ? scheme.name_ta : scheme.name}
                          </h4>
                          <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#16A34A', background: '#DCFCE7', padding: '2px 8px', borderRadius: '4px', whiteSpace: 'nowrap' }}>
                            ✓ {lang === 'ta' ? 'தகுதி' : 'Eligible'}
                          </span>
                        </div>
                        
                        <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#047857', marginTop: '6px' }}>
                          💰 {lang === 'ta' && scheme.benefit_amount_ta ? scheme.benefit_amount_ta : scheme.benefit_amount}
                        </div>
                        
                        <div style={{ fontSize: '0.74rem', color: '#64748B', marginTop: '3px' }}>
                          🏛️ {scheme.source_authority}
                        </div>

                        <div style={{ display: 'flex', gap: '8px', marginTop: '10px', flexWrap: 'wrap' }}>
                          <a
                            href={scheme.official_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{
                              flex: 1,
                              minWidth: '130px',
                              textAlign: 'center',
                              background: '#F8FAFC',
                              color: '#334155',
                              border: '1px solid #CBD5E1',
                              padding: '7px 10px',
                              borderRadius: '6px',
                              fontSize: '0.78rem',
                              fontWeight: 700,
                              textDecoration: 'none',
                              display: 'inline-flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              gap: '4px'
                            }}
                          >
                            <span>🌐</span>
                            <span>{lang === 'ta' ? 'அதிகாரப்பூர்வ தளம்' : 'Official Portal'} ↗</span>
                          </a>

                          <button
                            type="button"
                            onClick={() => {
                              if (setSelectedScheme) setSelectedScheme(scheme)
                              setTab('tracker')
                            }}
                            style={{
                              flex: 1,
                              minWidth: '130px',
                              textAlign: 'center',
                              background: '#2563EB',
                              color: '#FFFFFF',
                              border: 'none',
                              padding: '7px 10px',
                              borderRadius: '6px',
                              fontSize: '0.78rem',
                              fontWeight: 700,
                              cursor: 'pointer',
                              display: 'inline-flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              gap: '4px'
                            }}
                          >
                            <span>📑</span>
                            <span>{lang === 'ta' ? 'விண்ணப்பிக்கவும்' : 'Apply / Track'} →</span>
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                <div className="bubble-time">{m.time}</div>
              </div>
            ))}

            {loading && (
              <div className="bubble agent" style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#94A3B8', animation: 'pulse 1s infinite' }} />
                <span style={{ fontSize: '0.82rem', color: '#64748B' }}>Thinking...</span>
              </div>
            )}

            {/* Quick Menu Options */}
            {currentOptions.length > 0 && !loading && (
              <div className="menu-options">
                <small style={{ color: 'var(--text-muted)', fontWeight: 600 }}>{t.intake.quickSelect}</small>
                {currentOptions.map((opt) => (
                  <button
                    key={opt.id}
                    type="button"
                    className="menu-opt-btn"
                    onClick={() => handleOptionClick(opt)}
                  >
                    {lang === 'ta' ? opt.label_ta : opt.label}
                  </button>
                ))}
              </div>
            )}

            <div ref={chatEndRef} />
          </div>

          <div className="chat-footer">
            <form
              onSubmit={(e) => {
                e.preventDefault()
                handleUserMessage(inputText)
              }}
              className="chat-input-bar"
            >
              <button
                type="button"
                className={`chat-mic-btn ${listening ? 'active' : ''}`}
                onClick={toggleMic}
                title={listening ? t.intake.micStop : t.intake.micStart}
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
                  <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                  <line x1="12" y1="19" x2="12" y2="22" />
                </svg>
              </button>

              <input
                type="text"
                className="chat-input"
                placeholder={listening ? t.intake.listening : t.intake.typePlaceholder}
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
              />

              <button type="submit" className="btn-primary" style={{ padding: '10px 18px' }} disabled={!inputText.trim()}>
                {t.intake.btnSend}
              </button>
            </form>
          </div>
        </div>

        {/* Live Profile Verification Side Panel */}
        <div className="profile-panel">
          <div>
            <div className="profile-panel-head">
              <h3 style={{ fontSize: '1.1rem', fontWeight: 800 }}>{t.intake.profileHeading}</h3>
              <span className={isComplete ? 'badge-complete' : 'badge-incomplete'}>
                {isComplete ? t.intake.statusComplete : t.intake.statusIncomplete}
              </span>
            </div>

            <div className="data-row">
              <span className="label">{t.intake.fields.class}</span>
              <span className="val">
                {profile.completed_class ? `Class ${profile.completed_class}` : '—'}
              </span>
            </div>

            <div className="data-row">
              <span className="label">{t.intake.fields.gender}</span>
              <span className="val">
                {profile.gender ? profile.gender.toUpperCase() : '—'}
              </span>
            </div>

            <div className="data-row">
              <span className="label">{t.intake.fields.income}</span>
              <span className="val">
                {profile.income ? `₹ ${Number(profile.income).toLocaleString('en-IN')}` : '—'}
              </span>
            </div>

            <div className="data-row">
              <span className="label">{t.intake.fields.category}</span>
              <span className="val">
                {profile.category || '—'}
              </span>
            </div>

            <div className="data-row">
              <span className="label">{t.intake.fields.state}</span>
              <span className="val">{profile.state || 'Tamil Nadu'}</span>
            </div>
          </div>

          <div style={{ marginTop: '24px' }}>
            <button
              type="button"
              className="btn-primary"
              style={{ width: '100%', justifyContent: 'center' }}
              onClick={handleConfirmAndMatch}
              disabled={!isComplete}
            >
              <span>✅</span>
              <span>{t.intake.btnConfirm}</span>
            </button>
            <p style={{ textAlign: 'center', fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '10px' }}>
              {isComplete ? 'All fields verified. Ready for deterministic rule matching.' : 'Complete all fields via chat to evaluate eligibility.'}
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}
