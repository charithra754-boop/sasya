import React, { useState, useEffect, useRef } from 'react';
import { 
  ShieldCheck, Mic, Send, CloudRain, Thermometer, Droplet, 
  Map, TrendingUp, AlertTriangle, CheckCircle, Database, 
  Leaf, Info, DollarSign, Sprout, Sliders, Play, RefreshCw,
  Compass, HelpCircle, X, HelpCircle as HelpIcon, ChevronRight, ChevronLeft
} from 'lucide-react';

const GATEWAY_URL = "http://localhost:8000"; // API Gateway endpoint

export default function App() {
  // Authentication & Aadhaar Sandbox State
  const [aadhaarId, setAadhaarId] = useState("123456789012");
  const [otp, setOtp] = useState("123456");
  const [sessionId, setSessionId] = useState("");
  const [token, setToken] = useState("");
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [authError, setAuthError] = useState("");
  const [loading, setLoading] = useState(false);

  // Active Twin State
  const [agristackId, setAgristackId] = useState("AGRI-T2026");
  const [twinData, setTwinData] = useState(null);
  const [twinError, setTwinError] = useState("");

  // Chat & Speech Simulation State
  const [activeTab, setActiveTab] = useState("twin");
  const [query, setQuery] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [chatHistory, setChatHistory] = useState([
    { role: "system", text: "Welcome to SasyaAI. Press the microphone to speak your query or type it below." }
  ]);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);

  // Solver & verification state
  const [landLimit, setLandLimit] = useState(5.0);
  const [waterLimit, setWaterLimit] = useState(40000); // kL or 40,000,000 L
  const [capitalLimit, setCapitalLimit] = useState(200000);
  const [optResult, setOptResult] = useState(null);
  const [optLoading, setOptLoading] = useState(false);

  // Verification model state
  const [proposedPaddy, setProposedPaddy] = useState(2.0);
  const [proposedMaize, setProposedMaize] = useState(2.0);
  const [proposedSoybean, setProposedSoybean] = useState(1.0);
  const [verifyResult, setVerifyResult] = useState(null);

  // Onboarding Intention & Interactive Demo States
  const [selectedIntention, setSelectedIntention] = useState(null); // 'optimize' | 'advisor' | 'weather' | 'explore'
  const [hasChosenIntention, setHasChosenIntention] = useState(false);
  const [demoActive, setDemoActive] = useState(false);
  const [demoStep, setDemoStep] = useState(0);

  // Onboarding Guided Tours Configuration
  const tours = {
    optimize: [
      {
        tab: "optimizer",
        instruction: "Step 1/3 (Crop Optimizer): We've opened the 'Crop Optimizer' tab. Slide the Land, Water, and Budget controls on the right, then click 'Run OR-Tools Optimization' to solve for the best crop mix.",
        highlightElement: "optimizer-inputs"
      },
      {
        tab: "verifier",
        instruction: "Step 2/3 (Safety Verifier): We've switched to the 'Plan Safety Verifier' tab. Here you can verify if a manual crop plan exceeds resource limits by running verification.",
        highlightElement: "verifier-inputs"
      },
      {
        tab: "twin",
        instruction: "Step 3/3 (Ask Advisor): Ask the AI Advisor on the left, e.g. 'What crop variety should I plant?' to check government scheme eligibility.",
        highlightElement: "left-advisor"
      }
    ],
    advisor: [
      {
        tab: "twin",
        instruction: "Step 1/2 (Simulate Mic Input): Press the green Mic button in the left panel to simulate speaking a query in your local dialect.",
        highlightElement: "mic-controls"
      },
      {
        tab: "twin",
        instruction: "Step 2/2 (Explainability DAG): Once the agent responds, expand the chat message to inspect sub-agent outcomes (Planner, Vision, Geospatial maps).",
        highlightElement: "left-advisor"
      }
    ],
    weather: [
      {
        tab: "map",
        instruction: "Step 1/2 (Geospatial Canopy Map): We've switched to the 'Geospatial & Climate' tab. Review live weather inputs (Temperature, Humidity) from IMD sensors.",
        highlightElement: "weather-metrics"
      },
      {
        tab: "map",
        instruction: "Step 2/2 (Interactive Parcel Diagnostics): Click on 'Plot Parcel 101' on the map to trigger local water stress analysis.",
        highlightElement: "map-parcel-container"
      }
    ],
    explore: [
      {
        tab: "twin",
        instruction: "Step 1/3 (Digital Twin Card): Inspect your live dynamic soil parameters (NPK, pH, carbon ratio) in the active tab.",
        highlightElement: "twin-grid"
      },
      {
        tab: "optimizer",
        instruction: "Step 2/3 (Crop Optimization): Run the linear solver mix using Google OR-Tools equations.",
        highlightElement: "optimizer-inputs"
      },
      {
        tab: "map",
        instruction: "Step 3/3 (Geospatial Map): Switch to the Geospatial tab to check satellite greenness trajectories.",
        highlightElement: "map-parcel-container"
      }
    ]
  };

  // Synchronize Tab state automatically when onboarding steps progress
  useEffect(() => {
    if (demoActive && selectedIntention && tours[selectedIntention]) {
      const currentTour = tours[selectedIntention][demoStep];
      if (currentTour && currentTour.tab) {
        setActiveTab(currentTour.tab);
      }
    }
  }, [demoActive, demoStep, selectedIntention]);

  // Load default simulated digital twin once logged in
  useEffect(() => {
    if (isLoggedIn) {
      fetchOrInitializeTwin();
    }
  }, [isLoggedIn]);

  // Request Aadhaar OTP via sandbox auth-service
  const handleRequestOtp = async () => {
    setLoading(true);
    setAuthError("");
    try {
      const res = await fetch(`${GATEWAY_URL}/api/v1/auth/aadhaar/request`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ aadhaar_id: aadhaarId })
      });
      const data = await res.json();
      if (res.ok) {
        setSessionId(data.session_id);
        setChatHistory(prev => [...prev, { role: "system", text: "SMS OTP code simulated! Enter code '123456' to proceed." }]);
      } else {
        setAuthError(data.detail || "Failed to trigger Aadhaar OTP");
      }
    } catch (err) {
      setAuthError("Failed to connect to authentication gateway");
    } finally {
      setLoading(false);
    }
  };

  // Verify OTP and issue JWT access token
  const handleVerifyOtp = async () => {
    setLoading(true);
    setAuthError("");
    try {
      const res = await fetch(`${GATEWAY_URL}/api/v1/auth/aadhaar/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ aadhaar_id: aadhaarId, otp: otp })
      });
      const data = await res.json();
      if (res.ok) {
        setToken(data.access_token);
        setIsLoggedIn(true);
      } else {
        setAuthError(data.detail || "Invalid verification OTP");
      }
    } catch (err) {
      setAuthError("Verification process failed");
    } finally {
      setLoading(false);
    }
  };

  // Get or Create dynamic Digital Twin state
  const fetchOrInitializeTwin = async () => {
    setTwinError("");
    try {
      const getRes = await fetch(`${GATEWAY_URL}/api/v1/digital-twin/${agristackId}`);
      if (getRes.status === 200) {
        const data = await getRes.json();
        setTwinData(data);
        return;
      }

      const initPayload = {
        name: "Rajesh Kumar",
        phone: "9876543210",
        land_area: landLimit,
        district: "Gorakhpur",
        state: "Uttar Pradesh",
        soil: {
          nitrogen: 45.0,
          phosphorus: 22.0,
          potassium: 115.0,
          ph: 6.8,
          organic_carbon: 0.55,
          water_holding_capacity: 42.0
        },
        weather: {
          temperature: 32.5,
          humidity: 65.0,
          rainfall_forecast: 12.0,
          anomalies: null
        },
        finance: {
          kcc_active: true,
          credit_score: 720,
          outstanding_loan: 15000.0
        },
        current_season: {
          crop_name: "Maize",
          sowing_date: "2026-06-15",
          stage: "vegetative",
          health_index: 0.78
        },
        crop_history: [
          { year: 2025, season: "Rabi", crop_name: "Wheat", yield_kg_per_acre: 1600.0, income_rupees: 32000.0 }
        ]
      };

      const initRes = await fetch(`${GATEWAY_URL}/api/v1/digital-twin/${agristackId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(initPayload)
      });
      
      if (initRes.ok) {
        const data = await fetch(`${GATEWAY_URL}/api/v1/digital-twin/${agristackId}`).then(r => r.json());
        setTwinData(data);
      } else {
        setTwinError("Unable to initialize farmer profile twin");
      }
    } catch (err) {
      setTwinError("Connection to Digital Twin backend failed");
    }
  };

  // Submit Query to LLM Orchestrator routing to sub-agents
  const handleSendQuery = async (queryText = query) => {
    if (!queryText.trim()) return;
    
    setChatHistory(prev => [...prev, { role: "user", text: queryText }]);
    setQuery("");
    setLoading(true);

    try {
      const res = await fetch(`${GATEWAY_URL}/api/v1/orchestrator/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          agristack_id: agristackId,
          query: queryText,
          language: "en"
        })
      });
      const data = await res.json();
      if (res.ok) {
        setChatHistory(prev => [...prev, { role: "system", text: data.text_response }]);
        setIsPlayingAudio(true);
        setTimeout(() => setIsPlayingAudio(false), 5000);
      } else {
        setChatHistory(prev => [...prev, { role: "system", text: `Error: ${data.detail || "Unable to retrieve advice"}` }]);
      }
    } catch (err) {
      setChatHistory(prev => [...prev, { role: "system", text: "Communication error with AI agent services" }]);
    } finally {
      setLoading(false);
    }
  };

  // Run Google OR-Tools Optimizer
  const handleOptimize = async () => {
    setOptLoading(true);
    try {
      const crop_options = [
        {
          crop_name: "Paddy",
          expected_yield_kg_per_hectare: 4200.0,
          expected_price_per_kg: 22.0,
          cost_per_hectare: 30000.0,
          water_required_liters_per_hectare: 15000000.0
        },
        {
          crop_name: "Maize",
          expected_yield_kg_per_hectare: 5200.0,
          expected_price_per_kg: 20.0,
          cost_per_hectare: 40000.0,
          water_required_liters_per_hectare: 8000000.0
        },
        {
          crop_name: "Soybean",
          expected_yield_kg_per_hectare: 2600.0,
          expected_price_per_kg: 38.0,
          cost_per_hectare: 35000.0,
          water_required_liters_per_hectare: 6000000.0
        }
      ];

      const payload = {
        total_land_hectares: parseFloat(landLimit),
        water_budget_liters: parseFloat(waterLimit * 1000), 
        capital_budget_rupees: parseFloat(capitalLimit),
        crop_options
      };

      const res = await fetch(`${GATEWAY_URL}/api/v1/decision-engine/optimize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (res.ok) {
        setOptResult(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setOptLoading(false);
    }
  };

  // Run proposed plan verifier
  const handleVerifyPlan = async () => {
    try {
      const crop_options = [
        {
          crop_name: "Paddy",
          expected_yield_kg_per_hectare: 4200.0,
          expected_price_per_kg: 22.0,
          cost_per_hectare: 30000.0,
          water_required_liters_per_hectare: 15000000.0
        },
        {
          crop_name: "Maize",
          expected_yield_kg_per_hectare: 5200.0,
          expected_price_per_kg: 20.0,
          cost_per_hectare: 40000.0,
          water_required_liters_per_hectare: 8000000.0
        },
        {
          crop_name: "Soybean",
          expected_yield_kg_per_hectare: 2600.0,
          expected_price_per_kg: 38.0,
          cost_per_hectare: 35000.0,
          water_required_liters_per_hectare: 6000000.0
        }
      ];

      const payload = {
        proposed_allocations: {
          Paddy: parseFloat(proposedPaddy),
          Maize: parseFloat(proposedMaize),
          Soybean: parseFloat(proposedSoybean)
        },
        crop_options,
        total_land_hectares: parseFloat(landLimit),
        water_budget_liters: parseFloat(waterLimit * 1000),
        capital_budget_rupees: parseFloat(capitalLimit)
      };

      const res = await fetch(`${GATEWAY_URL}/api/v1/decision-engine/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (res.ok) {
        setVerifyResult(data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Simulate Mic Voice Query Recording
  const startRecording = () => {
    setIsRecording(true);
    setChatHistory(prev => [...prev, { role: "system", text: "Listening to voice input..." }]);
    setTimeout(() => {
      setIsRecording(false);
      const sampleQueries = [
        "What crop variety should I plant for my soil type?",
        "I found some worms chewing leaf stems, check for pest disease",
        "Give me weather risks and mandi rates for Maize"
      ];
      const randomQuery = sampleQueries[Math.floor(Math.random() * sampleQueries.length)];
      handleSendQuery(randomQuery);
    }, 3000);
  };

  // Intention onboarding submission
  const startGuidedTour = (intentionKey) => {
    setSelectedIntention(intentionKey);
    setHasChosenIntention(true);
    setDemoActive(true);
    setDemoStep(0);
  };

  const skipGuidedTour = (intentionKey) => {
    setSelectedIntention(intentionKey || "explore");
    setHasChosenIntention(true);
    setDemoActive(false);
  };

  // Helper check to apply highlighting class during guided tours
  const getHighlightClass = (elementId) => {
    if (!demoActive || !selectedIntention) return "";
    const tour = tours[selectedIntention];
    if (tour && tour[demoStep] && tour[demoStep].highlightElement === elementId) {
      return "demo-highlight";
    }
    return "";
  };

  // Renders Aadhaar Verification Login
  if (!isLoggedIn) {
    return (
      <div className="app-container" style={{ justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <div className="glass-panel" style={{ width: '450px', padding: '40px' }}>
          <div style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', gap: '12px', alignItems: 'center' }}>
            <div className="logo-icon">
              <ShieldCheck size={26} color="#000" />
            </div>
            <h2 className="logo-text" style={{ fontSize: '28px' }}>AgriStack Login</h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
              Secure sandbox login via Aadhaar OTP simulation
            </p>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginTop: '20px' }}>
            <div className="slider-container">
              <label className="slider-header" style={{ color: 'var(--text-secondary)' }}>Aadhaar ID</label>
              <input 
                type="text" 
                value={aadhaarId} 
                onChange={(e) => setAadhaarId(e.target.value)}
                style={{
                  background: 'rgba(255,255,255,0.03)',
                  border: '1px solid var(--border-glass)',
                  borderRadius: '12px',
                  padding: '12px',
                  color: '#fff',
                  fontSize: '15px'
                }}
              />
            </div>

            {sessionId && (
              <div className="slider-container">
                <label className="slider-header" style={{ color: 'var(--text-secondary)' }}>Verification OTP</label>
                <input 
                  type="text" 
                  value={otp} 
                  onChange={(e) => setOtp(e.target.value)}
                  style={{
                    background: 'rgba(255,255,255,0.03)',
                    border: '1px solid var(--border-glass)',
                    borderRadius: '12px',
                    padding: '12px',
                    color: '#fff',
                    fontSize: '15px'
                  }}
                />
              </div>
            )}

            {authError && (
              <div className="alert-card danger">
                <AlertTriangle size={16} />
                <span>{authError}</span>
              </div>
            )}

            {!sessionId ? (
              <button className="btn-primary" onClick={handleRequestOtp} disabled={loading}>
                {loading ? <RefreshCw className="animate-spin" /> : "Verify Identity"}
              </button>
            ) : (
              <button className="btn-primary" onClick={handleVerifyOtp} disabled={loading}>
                {loading ? <RefreshCw className="animate-spin" /> : "Confirm OTP"}
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Renders Intention Selection Modal at first load after login
  if (!hasChosenIntention) {
    return (
      <div className="app-container" style={{ justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <div className="glass-panel" style={{ width: '600px', padding: '36px', gap: '24px' }}>
          <div style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', gap: '8px', alignItems: 'center' }}>
            <Compass size={32} color="var(--primary)" />
            <h2 className="logo-text" style={{ fontSize: '26px' }}>Select Your Intent Today</h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
              Help us customize your dashboard experience and direct you to the right tools.
            </p>
          </div>

          <div className="intent-grid">
            <div className="intent-card" onClick={() => startGuidedTour("optimize")}>
              <div className="intent-title">
                <Sliders size={18} color="var(--primary)" />
                <span>Optimize Crop Plans</span>
              </div>
              <p className="intent-desc">Calculate the most profitable land allocations under resource caps using mathematical models.</p>
            </div>

            <div className="intent-card" onClick={() => startGuidedTour("advisor")}>
              <div className="intent-title">
                <Mic size={18} color="var(--primary)" />
                <span>Consult AI Advisor</span>
              </div>
              <p className="intent-desc">Ask queries regarding plant pest diagnostics, weather threats, and fertilizer limits.</p>
            </div>

            <div className="intent-card" onClick={() => startGuidedTour("weather")}>
              <div className="intent-title">
                <Map size={18} color="var(--primary)" />
                <span>Weather & Canopy Map</span>
              </div>
              <p className="intent-desc">Inspect NDVI greenness overlays, live local IMD alerts, and plot boundary trackers.</p>
            </div>

            <div className="intent-card" onClick={() => skipGuidedTour("explore")}>
              <div className="intent-title">
                <Database size={18} color="var(--primary)" />
                <span>Free Exploration</span>
              </div>
              <p className="intent-desc">Skip tutorials and navigate the soil digital twins, solver modules, and API cards freely.</p>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '16px', marginTop: '10px' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Guided onboarding takes about 2 minutes.</span>
            <button className="btn-demo-nav" onClick={() => skipGuidedTour("explore")}>
              Skip Tour & Open Dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Dashboard Page with Onboarding Demo Banner
  const tour = tours[selectedIntention];
  const currentStepInfo = tour && tour[demoStep];

  return (
    <div className="app-container">
      <header>
        <div className="logo-container">
          <div className="logo-icon">
            <Sprout size={22} color="#000" />
          </div>
          <div className="logo-text">SasyaAI</div>
        </div>

        <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
          <button 
            className="btn-demo-nav" 
            style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px' }}
            onClick={() => setHasChosenIntention(false)}
          >
            <Compass size={14} />
            <span>Reset Intention</span>
          </button>
          <div className="aadhaar-status">
            <ShieldCheck size={16} />
            <span>Aadhaar Verified</span>
          </div>
          <span style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>Profile: {agristackId}</span>
        </div>
      </header>

      {/* Guided Tour Wizard Banner */}
      {demoActive && currentStepInfo && (
        <div className="demo-banner">
          <div className="demo-content">
            <span className="demo-badge">Tour Step {demoStep + 1} of {tour.length}</span>
            <span className="demo-instruction">{currentStepInfo.instruction}</span>
          </div>
          <div className="demo-actions">
            {demoStep > 0 && (
              <button className="btn-demo-nav" onClick={() => setDemoStep(prev => prev - 1)}>
                <ChevronLeft size={14} style={{ marginRight: '4px', verticalAlign: 'middle' }} /> Back
              </button>
            )}
            {demoStep < tour.length - 1 ? (
              <button className="btn-demo-nav primary" onClick={() => setDemoStep(prev => prev + 1)}>
                Next <ChevronRight size={14} style={{ marginLeft: '4px', verticalAlign: 'middle' }} />
              </button>
            ) : (
              <button className="btn-demo-nav primary" onClick={() => setDemoActive(false)}>
                Finish Tour
              </button>
            )}
            <button 
              className="btn-demo-nav" 
              style={{ padding: '6px 8px', color: 'var(--text-secondary)' }} 
              onClick={() => setDemoActive(false)}
              title="Skip Demo"
            >
              <X size={16} />
            </button>
          </div>
        </div>
      )}

      <div className="dashboard-grid">
        {/* Left side: Voice Assistant chat portal */}
        <div className={`glass-panel assistant-panel ${getHighlightClass("left-advisor")}`}>
          <div className="panel-title">
            <Mic size={18} color="var(--primary)" />
            <span>Multilingual Advisor</span>
          </div>

          <div className="chat-history">
            {chatHistory.map((msg, index) => (
              <div key={index} className={`chat-bubble ${msg.role}`}>
                {msg.text}
              </div>
            ))}
          </div>

          {/* Sound waves simulation playing voice */}
          <div className={`voice-visualizer ${isPlayingAudio ? 'active' : ''}`}>
            {isPlayingAudio && (
              <>
                <div className="voice-bar"></div>
                <div className="voice-bar"></div>
                <div className="voice-bar"></div>
                <div className="voice-bar"></div>
                <div className="voice-bar"></div>
                <div className="voice-bar"></div>
                <div className="voice-bar"></div>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginLeft: '8px' }}>Audio response playing...</span>
              </>
            )}
          </div>

          <div className={`voice-input-area ${getHighlightClass("mic-controls")}`}>
            <input 
              type="text" 
              placeholder="Ask about fertilizer, pest, or schemes..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSendQuery()}
              className="voice-text-input"
            />
            <button 
              className={`mic-button ${isRecording ? 'recording' : ''}`}
              onClick={startRecording}
            >
              <Mic size={18} />
            </button>
          </div>
        </div>

        {/* Right side: Detailed twin tabs */}
        <div className="main-content">
          <div className="tabs-header">
            <button 
              className={`tab-button ${activeTab === 'twin' ? 'active' : ''}`}
              onClick={() => setActiveTab('twin')}
            >
              Digital Twin & Soil
            </button>
            <button 
              className={`tab-button ${activeTab === 'map' ? 'active' : ''}`}
              onClick={() => setActiveTab('map')}
            >
              Geospatial & Climate
            </button>
            <button 
              className={`tab-button ${activeTab === 'optimizer' ? 'active' : ''}`}
              onClick={() => setActiveTab('optimizer')}
            >
              Crop Optimizer
            </button>
            <button 
              className={`tab-button ${activeTab === 'verifier' ? 'active' : ''}`}
              onClick={() => setActiveTab('verifier')}
            >
              Plan Safety Verifier
            </button>
          </div>

          {/* Tab Content: Twin Details */}
          {activeTab === 'twin' && twinData && (
            <div className="glass-panel">
              <div className="panel-title">
                <Database size={18} color="var(--primary)" />
                <span>Dynamic State Snapshot (Soil & Crop Twin)</span>
              </div>

              <div className={`grid-container ${getHighlightClass("twin-grid")}`}>
                <div className="metric-card">
                  <span className="metric-label">Nitrogen (N)</span>
                  <div className="metric-value">{twinData.soil.nitrogen} kg/ha</div>
                  <div className="metric-footer"><Leaf size={14} color="var(--primary)" /> Medium Level</div>
                </div>
                <div className="metric-card">
                  <span className="metric-label">Phosphorus (P)</span>
                  <div className="metric-value">{twinData.soil.phosphorus} kg/ha</div>
                  <div className="metric-footer"><Leaf size={14} color="var(--accent-amber)" /> Deficient</div>
                </div>
                <div className="metric-card">
                  <span className="metric-label">Potassium (K)</span>
                  <div className="metric-value">{twinData.soil.potassium} kg/ha</div>
                  <div className="metric-footer"><Leaf size={14} color="var(--primary)" /> Rich Level</div>
                </div>
                <div className="metric-card">
                  <span className="metric-label">Soil pH</span>
                  <div className="metric-value">{twinData.soil.ph}</div>
                  <div className="metric-footer"><Info size={14} /> Neutral Soil</div>
                </div>
                <div className="metric-card">
                  <span className="metric-label">Active Crop</span>
                  <div className="metric-value">{twinData.current_season.crop_name}</div>
                  <div className="metric-footer"><Sprout size={14} /> Stage: {twinData.current_season.stage}</div>
                </div>
                <div className="metric-card">
                  <span className="metric-label">Health Index</span>
                  <div className="metric-value">{(twinData.current_season.health_index * 100).toFixed(0)}%</div>
                  <div className="metric-footer"><CheckCircle size={14} color="var(--primary)" /> Good greenness</div>
                </div>
              </div>
            </div>
          )}

          {/* Tab Content: Maps & Climate Alerts */}
          {activeTab === 'map' && twinData && (
            <div className="glass-panel">
              <div className="panel-title">
                <Map size={18} color="var(--primary)" />
                <span>NDVI Greenness Parcel Map & Climate Diagnostics</span>
              </div>

              <div className={`map-placeholder ${getHighlightClass("map-parcel-container")}`}>
                <div className="map-grid-layer"></div>
                <div className="map-parcel" onClick={() => handleSendQuery("Check the weather risk and soil moisture warnings")}>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontWeight: 'bold', color: '#fff', fontSize: '14px' }}>Plot Parcel 101</div>
                    <div style={{ fontSize: '11px', color: '#a7f3d0', marginTop: '4px' }}>NDVI greenness: 0.68</div>
                  </div>
                </div>
              </div>

              <div className={`grid-container ${getHighlightClass("weather-metrics")}`}>
                <div className="metric-card">
                  <span className="metric-label">Temperature</span>
                  <div className="metric-value">{twinData.weather.temperature} °C</div>
                  <div className="metric-footer"><Thermometer size={14} /> Live IMD Feed</div>
                </div>
                <div className="metric-card">
                  <span className="metric-label">Humidity</span>
                  <div className="metric-value">{twinData.weather.humidity} %</div>
                  <div className="metric-footer"><Droplet size={14} /> Air Moisture</div>
                </div>
                <div className="metric-card">
                  <span className="metric-label">Rainfall Forecast</span>
                  <div className="metric-value">{twinData.weather.rainfall_forecast} mm</div>
                  <div className="metric-footer"><CloudRain size={14} /> Next 7 days</div>
                </div>
              </div>
            </div>
          )}

          {/* Tab Content: Crop allocation Optimizer */}
          {activeTab === 'optimizer' && (
            <div className="glass-panel">
              <div className="panel-title">
                <Sliders size={18} color="var(--primary)" />
                <span>OR-Tools Optimal Crop Mix Allocation</span>
              </div>

              <div className="grid-container" style={{ gridTemplateColumns: '1fr 1fr', gap: '30px' }}>
                <div className={`slider-container ${getHighlightClass("optimizer-inputs")}`} style={{ gap: '20px' }}>
                  <div className="slider-container">
                    <div className="slider-header">
                      <span>Total Land Area</span>
                      <span>{landLimit} Hectares</span>
                    </div>
                    <input 
                      type="range" 
                      min="1.0" 
                      max="15.0" 
                      step="0.5" 
                      value={landLimit}
                      onChange={(e) => setLandLimit(e.target.value)}
                      className="custom-range"
                    />
                  </div>

                  <div className="slider-container">
                    <div className="slider-header">
                      <span>Water Allocation Limit</span>
                      <span>{waterLimit} kL</span>
                    </div>
                    <input 
                      type="range" 
                      min="10000" 
                      max="100000" 
                      step="5000" 
                      value={waterLimit}
                      onChange={(e) => setWaterLimit(e.target.value)}
                      className="custom-range"
                    />
                  </div>

                  <div className="slider-container">
                    <div className="slider-header">
                      <span>Capital Input Budget</span>
                      <span>₹ {capitalLimit.toLocaleString()}</span>
                    </div>
                    <input 
                      type="range" 
                      min="50000" 
                      max="500000" 
                      step="10000" 
                      value={capitalLimit}
                      onChange={(e) => setCapitalLimit(e.target.value)}
                      className="custom-range"
                    />
                  </div>

                  <button className="btn-primary" onClick={handleOptimize} disabled={optLoading}>
                    {optLoading ? <RefreshCw className="animate-spin" /> : "Run OR-Tools Optimization"}
                  </button>
                </div>

                <div style={{ background: 'rgba(255,255,255,0.01)', border: '1px dashed var(--border-glass)', borderRadius: '16px', padding: '20px' }}>
                  <div style={{ fontSize: '14px', fontWeight: 'bold', color: 'var(--text-secondary)', marginBottom: '12px' }}>Solver Recommendations</div>
                  
                  {optResult ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '8px' }}>
                        <span>Optimal Net Profit:</span>
                        <span style={{ color: 'var(--primary)', fontWeight: 'bold' }}>₹ {optResult.optimal_profit_rupees.toLocaleString()}</span>
                      </div>
                      
                      {optResult.allocations.map((alloc, idx) => (
                        <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                          <span>{alloc.crop_name}:</span>
                          <span style={{ color: '#fff' }}>{alloc.allocated_hectares} ha (Revenue: ₹ {((alloc.expected_profit_rupees) + (alloc.cost_rupees)).toLocaleString()})</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p style={{ color: 'var(--text-muted)', fontSize: '13px', textAlign: 'center', marginTop: '20px' }}>
                      Adjust bounds and trigger optimization to solve allocations.
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Tab Content: Plan Safety Verifier */}
          {activeTab === 'verifier' && (
            <div className="glass-panel">
              <div className="panel-title">
                <AlertTriangle size={18} color="var(--primary)" />
                <span>Hard Constraint Safety Verifier</span>
              </div>

              <div className="grid-container" style={{ gridTemplateColumns: '1fr 1fr', gap: '30px' }}>
                <div className={`slider-container ${getHighlightClass("verifier-inputs")}`} style={{ gap: '20px' }}>
                  <div className="slider-container">
                    <div className="slider-header">
                      <span>Paddy land allocation</span>
                      <span>{proposedPaddy} ha</span>
                    </div>
                    <input 
                      type="range" 
                      min="0.0" 
                      max="10.0" 
                      step="0.5" 
                      value={proposedPaddy}
                      onChange={(e) => setProposedPaddy(e.target.value)}
                      className="custom-range"
                    />
                  </div>

                  <div className="slider-container">
                    <div className="slider-header">
                      <span>Maize land allocation</span>
                      <span>{proposedMaize} ha</span>
                    </div>
                    <input 
                      type="range" 
                      min="0.0" 
                      max="10.0" 
                      step="0.5" 
                      value={proposedMaize}
                      onChange={(e) => setProposedMaize(e.target.value)}
                      className="custom-range"
                    />
                  </div>

                  <div className="slider-container">
                    <div className="slider-header">
                      <span>Soybean land allocation</span>
                      <span>{proposedSoybean} ha</span>
                    </div>
                    <input 
                      type="range" 
                      min="0.0" 
                      max="10.0" 
                      step="0.5" 
                      value={proposedSoybean}
                      onChange={(e) => setProposedSoybean(e.target.value)}
                      className="custom-range"
                    />
                  </div>

                  <button className="btn-primary" onClick={handleVerifyPlan}>
                    Run Constraint Verification
                  </button>
                </div>

                <div>
                  {verifyResult ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                      {verifyResult.is_safe ? (
                        <div className="alert-card success">
                          <CheckCircle size={18} />
                          <div>
                            <div style={{ fontWeight: 'bold' }}>All Constraints Satisfied</div>
                            <div style={{ fontSize: '12px', marginTop: '4px' }}>The proposed plan is safe to execute.</div>
                          </div>
                        </div>
                      ) : (
                        <div className="alert-card danger">
                          <AlertTriangle size={18} />
                          <div>
                            <div style={{ fontWeight: 'bold' }}>Safety Violations Detected</div>
                            <ul style={{ listStyle: 'none', padding: 0, marginTop: '6px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                              {verifyResult.violations.map((v, i) => (
                                <li key={i} style={{ fontSize: '12px' }}>• {v}</li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      )}

                      <div style={{ background: 'rgba(255,255,255,0.01)', border: '1px solid var(--border-glass)', borderRadius: '12px', padding: '16px', display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '13px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <span>Total Land Used:</span>
                          <span>{verifyResult.total_land_used_hectares} ha / {landLimit} ha</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <span>Total Water Used:</span>
                          <span>{(verifyResult.total_water_used_liters / 1000).toLocaleString()} kL / {waterLimit} kL</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <span>Total Capital Cost:</span>
                          <span>₹ {verifyResult.total_capital_used_rupees.toLocaleString()} / ₹ {capitalLimit.toLocaleString()}</span>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <p style={{ color: 'var(--text-muted)', fontSize: '13px', textAlign: 'center', marginTop: '20px' }}>
                      Check proposed allocations to verify water limits and land overruns.
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
