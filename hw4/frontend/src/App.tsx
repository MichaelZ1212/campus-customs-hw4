import { NavLink, Route, Routes } from "react-router-dom";
import ChatWidget from "./components/ChatWidget";
import AboutPage from "./pages/AboutPage";
import AccountPage from "./pages/AccountPage";
import HomePage from "./pages/HomePage";
import LoginPage from "./pages/LoginPage";
import NotFoundPage from "./pages/NotFoundPage";
import ProductDetailPage from "./pages/ProductDetailPage";
import ProductsPage from "./pages/ProductsPage";
import { useAuth } from "./auth";
import ChatResultsSection from "./components/ChatResultsSection";

const navItems = [
  ["/", "Home"],
  ["/products", "Products"],
  ["/about", "About Us"],
] as const;

export default function App() {
  const { user, signOut } = useAuth();
  return (
    <div className="site-shell">
      <div className="announcement">Custom Yale gear for every corner of campus</div>
      <header className="site-header">
        <NavLink className="brand" to="/" aria-label="Campus Customs home">
          <span className="brand-mark">Y</span>
          <span>Campus <b>Customs</b></span>
        </NavLink>
        <nav aria-label="Main navigation">
          {navItems.map(([to, label]) => (
            <NavLink key={to} to={to} end={to === "/"}>
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="account-links">
          {user ? (
            <><span className="user-greeting">Hi, {user.first_name}</span><button className="logout-link" onClick={signOut}>Log out</button></>
          ) : (
            <><NavLink to="/login">Log in</NavLink><NavLink className="button button-small" to="/create-account">Create Account</NavLink></>
          )}
        </div>
      </header>

      <main>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/products" element={<ProductsPage />} />
          <Route path="/products/:productId" element={<ProductDetailPage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/create-account" element={<AccountPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
        <ChatResultsSection />
      </main>

      <footer>
        <div className="footer-brand">Campus Customs</div>
        <p>Made for Bulldogs, families, teams, and the New Haven community.</p>
        <p className="fine-print">© {new Date().getFullYear()} Campus Customs</p>
      </footer>
      <ChatWidget />
    </div>
  );
}
