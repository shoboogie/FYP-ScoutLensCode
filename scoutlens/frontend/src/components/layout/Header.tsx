import { Link } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";

export default function Header() {
  const { isAuthenticated, logout } = useAuth();

  return (
    <header className="bg-navy text-white shadow-lg">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
        <Link to="/" className="text-xl font-bold tracking-tight">
          <span className="text-teal-light">Scout</span>Lens
        </Link>

        <nav className="flex items-center gap-6 text-sm font-medium">
          <Link to="/" className="hover:text-teal-light transition-colors">
            Search
          </Link>
          {isAuthenticated && (
            <Link to="/shortlist" className="hover:text-teal-light transition-colors">
              Shortlist
            </Link>
          )}
          {isAuthenticated ? (
            <button
              onClick={logout}
              className="rounded bg-teal px-3 py-1.5 text-white hover:bg-teal-dark transition-colors"
            >
              Sign Out
            </button>
          ) : (
            <Link
              to="/login"
              className="rounded bg-teal px-3 py-1.5 text-white hover:bg-teal-dark transition-colors"
            >
              Sign In
            </Link>
          )}
        </nav>
      </div>
    </header>
  );
}
