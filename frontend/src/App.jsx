import { Routes, Route, NavLink, useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { pageVariants } from "./components/motion.js";
import { IconDash, IconPlus, IconUpdates, IconMotd, IconSettings } from "./components/icons.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import AddVM from "./pages/AddVM.jsx";
import VMDetail from "./pages/VMDetail.jsx";
import Updates from "./pages/Updates.jsx";
import Motd from "./pages/Motd.jsx";
import Settings from "./pages/Settings.jsx";

const NAV = [
  { to: "/", end: true, label: "Dashboard", Icon: IconDash },
  { to: "/ajouter", label: "Ajouter une VM", Icon: IconPlus },
  { to: "/maj", label: "Mises à jour", Icon: IconUpdates },
  { to: "/motd", label: "MOTD", Icon: IconMotd },
  { to: "/parametres", label: "Paramètres", Icon: IconSettings },
];

function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark"><span /></div>
        <div className="brand-title">HomeLab <em>VM</em></div>
      </div>
      <div className="nav-section">Pilotage</div>
      <nav className="nav">
        {NAV.map(({ to, end, label, Icon }) => (
          <NavLink key={to} to={to} end={end} className="nav-link">
            {({ isActive }) => (
              <>
                {isActive && <motion.span layoutId="nav-active" className="nav-active-bg" transition={{ type: "spring", stiffness: 420, damping: 34 }} />}
                <Icon /> {label}
              </>
            )}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}

function AnimatedRoutes() {
  const location = useLocation();
  return (
    <AnimatePresence mode="wait">
      <motion.div key={location.pathname} variants={pageVariants} initial="initial" animate="enter" exit="exit">
        <Routes location={location}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/ajouter" element={<AddVM />} />
          <Route path="/vm/:id" element={<VMDetail />} />
          <Route path="/maj" element={<Updates />} />
          <Route path="/motd" element={<Motd />} />
          <Route path="/parametres" element={<Settings />} />
        </Routes>
      </motion.div>
    </AnimatePresence>
  );
}

export default function App() {
  return (
    <div className="layout">
      <Sidebar />
      <main className="content">
        <AnimatedRoutes />
      </main>
    </div>
  );
}
