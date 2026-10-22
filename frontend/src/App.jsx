import React, { useState, useEffect } from 'react'
import { T } from './i18n'
import Navbar from './components/Navbar'
import Footer from './components/Footer'
import Home from './components/Home'
import ChatIntake from './components/ChatIntake'
import SchemeCards from './components/SchemeCards'
import ApplicationTracker from './components/ApplicationTracker'
import TeacherDashboard from './components/TeacherDashboard'
import SchemeAdmin from './components/SchemeAdmin'
import { fetchAllSchemes, matchSchemes } from './api'

export default function App() {
  const [currentTab, setTab] = useState('home')
  const [lang, setLang] = useState('en')
  const [profile, setProfile] = useState({
    name: 'Student',
    state: 'Tamil Nadu',
    completed_class: null,
    income: null,
    category: null,
    gender: null,
    course_pursuing: null,
    confirmed: false
  })
  const [matchedSchemes, setMatchedSchemes] = useState([])
  const [selectedScheme, setSelectedScheme] = useState(null)

  const t = T[lang]

  useEffect(() => {
    document.documentElement.lang = lang
  }, [lang])

  // Initial fetch of schemes for fallback / preview
  useEffect(() => {
    async function init() {
      const all = await fetchAllSchemes()
      if (all && all.length > 0) {
        // default evaluation with sample profile
        const initialMatch = await matchSchemes({
          completed_class: 12,
          income: 180000,
          category: 'BC',
          gender: 'female',
          state: 'Tamil Nadu'
        })
        if (initialMatch && initialMatch.schemes) {
          setMatchedSchemes(initialMatch.schemes)
          setSelectedScheme(initialMatch.schemes.find((s) => s.eligible) || initialMatch.schemes[0])
        }
      }
    }
    init()
  }, [])

  return (
    <div className="app-container">
      <Navbar
        currentTab={currentTab}
        setTab={setTab}
        lang={lang}
        setLang={setLang}
        t={t}
      />

      <main style={{ flex: 1 }}>
        {currentTab === 'home' && (
          <Home
            setTab={setTab}
            t={t}
            lang={lang}
          />
        )}

        {currentTab === 'intake' && (
          <ChatIntake
            profile={profile}
            setProfile={setProfile}
            setMatchedSchemes={setMatchedSchemes}
            setSelectedScheme={setSelectedScheme}
            setTab={setTab}
            t={t}
            lang={lang}
          />
        )}

        {currentTab === 'schemes' && (
          <SchemeCards
            schemes={matchedSchemes}
            setSelectedScheme={setSelectedScheme}
            setTab={setTab}
            t={t}
            lang={lang}
          />
        )}

        {currentTab === 'tracker' && (
          <ApplicationTracker
            selectedScheme={selectedScheme}
            profile={profile}
            setTab={setTab}
            t={t}
            lang={lang}
          />
        )}

        {currentTab === 'dashboard' && (
          <TeacherDashboard
            t={t}
            lang={lang}
          />
        )}

        {currentTab === 'admin' && (
          <SchemeAdmin
            t={t}
            lang={lang}
          />
        )}
      </main>

      <Footer t={t} />
    </div>
  )
}
