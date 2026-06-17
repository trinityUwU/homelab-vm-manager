import { Routes, Route, NavLink } from "react-router-dom";
import Dashboard from "./pages/Dashboard.jsx";
import AddVM from "./pages/AddVM.jsx";
import VMDetail from "./pages/VMDetail.jsx";
import Updates from "./pages/Updates.jsx";
import Motd from "./pages/Motd.jsx";
import Settings from "./pages/Settings.jsx";

function Sidebar() {
  return (
    <aside className="sidebar">
      <h1>HomeLab <span>VM</span> Manager</h1>
      <nav>
        <NavLink to="/" end className="nav-link">Dashboard</NavLink>
        <NavLink to="/ajouter" className="nav-link">Ajouter une VM</NavLink>
        <NavLink to="/maj" className="nav-link">Mises à jour</NavLink>
        <NavLink to="/motd" className="nav-link">MOTD</NavLink>
        <NavLink to="/parametres" className="nav-link">Paramètres</NavLink>
      </nav>
    </aside>
  );
}

export default function App() {
  return (
    <div className="layout">
      <Sidebar />
      <main className="content">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/ajouter" element={<AddVM />} />
          <Route path="/vm/:id" element={<VMDetail />} />
          <Route path="/maj" element={<Updates />} />
          <Route path="/motd" element={<Motd />} />
          <Route path="/parametres" element={<Settings />} />
        </Routes>
      </main>
    </div>
  );
}
