
import { useState } from "react";
import {
  Activity, Zap, LayoutDashboard, Network, Building2,
  AlertTriangle, Gauge, Users, Receipt, Wrench,
  BrainCircuit, Settings, Bell, Search, ChevronDown,
  TrendingUp, TrendingDown, MapPin, Clock, Menu,
  CircleDollarSign, ShieldCheck, Radio, ArrowUpRight,
  ArrowDownRight, Sun, Moon
} from "lucide-react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, BarChart, Bar
} from "recharts";
import GridMap from "./components/GridMap";

const navigation = [
  { section: "OVERVIEW" },
  { name: "Executive Dashboard", icon: LayoutDashboard },
  { section: "POWER OPERATIONS" },
  { name: "Grid Network", icon: Network },
  { name: "Substations", icon: Building2 },
  { name: "Outage Management", icon: AlertTriangle },
  { name: "Energy Monitoring", icon: Activity },
  { section: "CUSTOMER SERVICES" },
  { name: "Customers & Meters", icon: Gauge },
  { name: "Billing & Revenue", icon: Receipt },
  { section: "ENGINEERING" },
  { name: "Maintenance", icon: Wrench },
  { name: "Workforce", icon: Users },
  { section: "INTELLIGENCE" },
  { name: "AI Analytics", icon: BrainCircuit },
  { name: "Administration", icon: Settings },
];

const usageData = [
  { time: "06:00", demand: 420, supply: 480 },
  { time: "08:00", demand: 590, supply: 650 },
  { time: "10:00", demand: 680, supply: 740 },
  { time: "12:00", demand: 760, supply: 820 },
  { time: "14:00", demand: 710, supply: 790 },
  { time: "16:00", demand: 850, supply: 910 },
  { time: "18:00", demand: 980, supply: 1050 },
  { time: "20:00", demand: 870, supply: 940 },
  { time: "22:00", demand: 620, supply: 700 },
];

const regionalData = [
  { name: "Yangon", value: 85 },
  { name: "Mandalay", value: 72 },
  { name: "Bago", value: 64 },
  { name: "Naypyidaw", value: 58 },
  { name: "Mon", value: 49 },
];

const outages = [
  { area: "South Okkalapa", type: "Distribution Fault", time: "09:42 AM", status: "In Progress", level: "high" },
  { area: "North Dagon", type: "Transformer Issue", time: "10:15 AM", status: "Investigating", level: "medium" },
  { area: "Hlaing Township", type: "Scheduled Maintenance", time: "11:30 AM", status: "Scheduled", level: "low" },
  { area: "Thingangyun", type: "Line Maintenance", time: "12:05 PM", status: "In Progress", level: "medium" },
];

const stats = [
  { label: "TOTAL CUSTOMERS", value: "1,284,590", change: "+4.8%", up: true, icon: Users, color: "#60a5fa" },
  { label: "ENERGY SUPPLY", value: "1,284 MW", change: "+2.4%", up: true, icon: Zap, color: "#fbbf24" },
  { label: "ACTIVE OUTAGES", value: "24", change: "-12.5%", up: false, icon: AlertTriangle, color: "#fb7185" },
  { label: "COLLECTION REVENUE", value: "8.42 B", change: "+8.2%", up: true, icon: CircleDollarSign, color: "#34d399" },
];

export default function App() {
  const [active, setActive] = useState("Executive Dashboard");
  const [collapsed, setCollapsed] = useState(false);
  const [dark, setDark] = useState(true);
  const [period, setPeriod] = useState("Today");
  const [search, setSearch] = useState("");

  const isDashboard = active === "Executive Dashboard";

  return (
    <div className={`app ${dark ? "dark" : "light"}`}>
      <aside className={`sidebar ${collapsed ? "collapsed" : ""}`}>
        <div className="brand">
          <div className="brand-icon"><Zap size={23} fill="currentColor" /></div>
          {!collapsed && <div><strong>APEXIVE<span>AI</span></strong><small>ENERGY OS</small></div>}
        </div>

        <div className="nav-list">
          {navigation.map((item, i) => {
            if (item.section) return !collapsed ? <div className="nav-section" key={i}>{item.section}</div> : null;
            const Icon = item.icon!;
            return (
              <button
                key={item.name}
                title={item.name}
                className={`nav-item ${active === item.name ? "selected" : ""}`}
                onClick={() => setActive(item.name!)}
              >
                <Icon size={19} />
                {!collapsed && <span>{item.name}</span>}
                {!collapsed && item.name === "Outage Management" &&
                  <span className="nav-count">24</span>}
              </button>
            );
          })}
        </div>

        {!collapsed && (
          <div className="sidebar-bottom">
            <div className="system-status"><span className="pulse" /> SYSTEM OPERATIONAL</div>
            <div className="version">APEXIVEAI ENERGY OS · v0.1.0</div>
          </div>
        )}
      </aside>

      <main className="main">
        <header className="topbar">
          <div className="top-left">
            <button className="icon-button" onClick={() => setCollapsed(!collapsed)}><Menu size={20}/></button>
            <div className="breadcrumb">ENERGY OS <span>/</span> <b>{active.toUpperCase()}</b></div>
          </div>
          <div className="top-actions">
            <div className="search-box">
              <Search size={16}/>
              <input placeholder="Search anything..." value={search} onChange={e => setSearch(e.target.value)}/>
              <kbd>⌘ K</kbd>
            </div>
            <button className="icon-button" onClick={() => setDark(!dark)}>{dark ? <Sun size={19}/> : <Moon size={19}/>}</button>
            <button className="icon-button notification"><Bell size={19}/><i/></button>
            <div className="profile">
              <div className="avatar">EA</div>
              <div className="profile-info"><strong>EPC Administrator</strong><small>SUPER ADMIN</small></div>
              <ChevronDown size={15}/>
            </div>
          </div>
        </header>

        <div className="content">
          <div className="page-heading">
            <div>
              <div className="eyebrow"><span className="pulse"/> NATIONAL POWER OPERATIONS CENTER</div>
              <h1>{active}</h1>
              <p>Electricity infrastructure intelligence and operational overview.</p>
            </div>
            <div className="heading-right">
              <div className="live-tag"><Radio size={14}/> LIVE MONITORING DEMO</div>
              <div className="date-tag"><Clock size={15}/> 08 NOV 2026</div>
            </div>
          </div>

          {isDashboard ? (
            <>
              <div className="stats-grid">
                {stats.map((s, i) => {
                  const Icon = s.icon;
                  return (
                    <div className="stat-card" key={i}>
                      <div className="stat-top">
                        <span>{s.label}</span>
                        <div className="stat-icon" style={{ color: s.color, background: `${s.color}15` }}><Icon size={20}/></div>
                      </div>
                      <div className="stat-value">{s.value}</div>
                      <div className="stat-bottom">
                        <span className={`change ${s.up ? "positive" : "negative"}`}>
                          {s.up ? <TrendingUp size={14}/> : <TrendingDown size={14}/>} {s.change}
                        </span>
                        <span>vs previous period</span>
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="main-grid">
                <section className="panel demand-panel">
                  <div className="panel-heading">
                    <div><h3>Electricity Demand & Supply</h3><p>National grid performance · MW</p></div>
                    <select value={period} onChange={e => setPeriod(e.target.value)}>
                      <option>Today</option><option>Weekly</option><option>Monthly</option>
                    </select>
                  </div>
                  <div className="chart-legend">
                    <span><i className="legend-blue"/> Electricity Demand</span>
                    <span><i className="legend-green"/> Electricity Supply</span>
                  </div>
                  <div className="chart">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={usageData}>
                        <defs>
                          <linearGradient id="supply" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#34d399" stopOpacity={0.25}/>
                            <stop offset="95%" stopColor="#34d399" stopOpacity={0}/>
                          </linearGradient>
                          <linearGradient id="demand" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#60a5fa" stopOpacity={0.25}/>
                            <stop offset="95%" stopColor="#60a5fa" stopOpacity={0}/>
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--grid)"/>
                        <XAxis dataKey="time" stroke="var(--muted)" tickLine={false} axisLine={false}/>
                        <YAxis stroke="var(--muted)" tickLine={false} axisLine={false}/>
                        <Tooltip contentStyle={{background:"var(--panel)",border:"1px solid var(--border)",borderRadius:10,color:"var(--text)"}}/>
                        <Area type="monotone" dataKey="supply" stroke="#34d399" fill="url(#supply)" strokeWidth={2}/>
                        <Area type="monotone" dataKey="demand" stroke="#60a5fa" fill="url(#demand)" strokeWidth={2}/>
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </section>

                <section className="panel grid-panel">
                  <div className="panel-heading"><div><h3>Grid Health</h3><p>Infrastructure status</p></div><ShieldCheck color="#34d399" size={21}/></div>
                  <div className="health-score"><strong>96.8</strong><span>%</span></div>
                  <div className="health-caption">OVERALL GRID HEALTH</div>
                  <div className="health-bar"><span/></div>
                  <div className="health-list">
                    <div><span><i className="dot green"/>Operational</span><b>1,248</b></div>
                    <div><span><i className="dot yellow"/>Under Maintenance</span><b>32</b></div>
                    <div><span><i className="dot red"/>Critical Alerts</span><b>8</b></div>
                  </div>
                </section>
              </div>

              <div className="main-grid lower-grid">
                <section className="panel regional-panel">
                  <div className="panel-heading"><div><h3>Regional Energy Distribution</h3><p>Electricity supply by region · illustrative data</p></div><button className="text-button" onClick={() => setActive("Grid Network")}>View network <ArrowUpRight size={14}/></button></div>
                  <div className="region-chart">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={regionalData} layout="vertical" margin={{left:0,right:15}}>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--grid)" horizontal={false}/>
                        <XAxis type="number" stroke="var(--muted)" tickLine={false} axisLine={false}/>
                        <YAxis dataKey="name" type="category" stroke="var(--muted)" tickLine={false} axisLine={false} width={90}/>
                        <Tooltip contentStyle={{background:"var(--panel)",border:"1px solid var(--border)",borderRadius:10}}/>
                        <Bar dataKey="value" fill="#60a5fa" radius={[0,5,5,0]} barSize={17}/>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </section>

                <section className="panel outage-panel">
                  <div className="panel-heading"><div><h3>Recent Outage Reports</h3><p>Operational incident monitoring</p></div><span className="outage-count">24 ACTIVE</span></div>
                  <div className="outage-list">
                    {outages.map((o,i) => (
                      <div className="outage-item" key={i}>
                        <div className={`outage-icon ${o.level}`}><AlertTriangle size={17}/></div>
                        <div className="outage-info"><strong>{o.area}</strong><span>{o.type} · {o.time}</span></div>
                        <span className={`status ${o.level}`}>{o.status}</span>
                      </div>
                    ))}
                  </div>
                </section>
              </div>

              <div className="footer-note"><span>APEXIVEAI ENERGY OS</span><span>DEMO ENVIRONMENT · MOCK DATA · NOT CONNECTED TO LIVE GRID SYSTEMS</span></div>
            </>
          ) :  active === "Grid Network" ? (
            <GridMap />
          ) : (
            <section className="panel module-placeholder">
              <div className="module-symbol"><Zap size={32}/></div>
              <h2>{active}</h2>
              <p>This module is registered in the Energy OS navigation.</p>
              <p className="placeholder-detail">Next development stage: dedicated screens, API integration, database models and operational workflows.</p>
              <button className="primary-button" onClick={() => setActive("Executive Dashboard")}>Return to Dashboard</button>
            </section>
          )}
        </div>
      </main>
    </div>
  );
}
