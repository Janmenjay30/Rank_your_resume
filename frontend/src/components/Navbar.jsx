import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <nav className="border-b border-white/10 bg-white/5 backdrop-blur-sm sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
        <Link to="/" className="text-lg font-bold text-white tracking-tight">
          Resume<span className="text-purple-400">Checker</span>
        </Link>
        <div className="flex items-center gap-4">
          <span className="text-sm text-white/60">{user?.name || user?.email}</span>
          <button
            onClick={handleLogout}
            className="text-sm px-3 py-1.5 rounded-lg border border-white/15 hover:bg-white/10 transition"
          >
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
}
