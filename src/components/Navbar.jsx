import { useState } from "react";
import { Link, NavLink } from "react-router-dom";

const links = [
  { to: "/ask-doubt", label: "Ask Doubt", active: "bg-yellow-100 text-yellow-800" },
  { to: "/history", label: "History", active: "bg-sky-100 text-sky-800" },
  { to: "/bookmarks", label: "Bookmarks", active: "bg-green-100 text-green-800" },
  { to: "/profile", label: "Profile", active: "bg-violet-100 text-violet-800" },
];

function Navbar() {
  const [open, setOpen] = useState(false);

  const linkClass = ({ isActive }, active) =>
    `block rounded-xl px-4 py-2.5 text-sm font-semibold transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-600 ${
      isActive ? active : "bg-slate-50 text-slate-800 hover:bg-slate-100"
    }`;

  return (
    <nav
      className="relative z-50 mx-3 mt-3 rounded-2xl bg-white/90 px-4 py-3 shadow-lg backdrop-blur-md sm:mx-6 sm:mt-4 sm:px-6 sm:py-4"
      aria-label="Main navigation"
    >
      <div className="flex items-center gap-3">
        <Link
          to="/ask-doubt"
          className="min-w-0 truncate text-lg font-bold text-slate-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-600 sm:text-2xl"
          onClick={() => setOpen(false)}
        >
          AI Doubt Solver
        </Link>

        <div className="ml-auto hidden items-center gap-2 md:flex lg:gap-3">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={(args) => linkClass(args, link.active)}
            >
              {link.label}
            </NavLink>
          ))}
        </div>

        <button
          type="button"
          aria-label={open ? "Close navigation menu" : "Open navigation menu"}
          aria-expanded={open}
          aria-controls="mobile-nav"
          onClick={() => setOpen((prev) => !prev)}
          className="ml-auto inline-flex h-10 w-10 items-center justify-center rounded-xl bg-slate-100 text-slate-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-600 md:hidden"
        >
          <span className="text-xl leading-none" aria-hidden="true">
            {open ? "✕" : "☰"}
          </span>
        </button>
      </div>

      {open && (
        <div
          id="mobile-nav"
          className="mt-3 grid gap-2 border-t border-slate-100 pt-3 md:hidden"
        >
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              onClick={() => setOpen(false)}
              className={(args) => linkClass(args, link.active)}
            >
              {link.label}
            </NavLink>
          ))}
        </div>
      )}
    </nav>
  );
}

export default Navbar;
