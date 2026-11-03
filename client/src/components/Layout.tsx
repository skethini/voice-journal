import { NavLink, Outlet } from "react-router-dom";

const tabs = [
  { to: "/", label: "Journal", end: true },
  { to: "/entries", label: "Entries" },
  { to: "/insights", label: "Insights" },
  { to: "/ask", label: "Ask" },
  { to: "/guidance", label: "Guidance" },
  { to: "/settings", label: "Settings" },
];

export function Layout() {
  return (
    <div className="mx-auto flex min-h-dvh max-w-lg flex-col px-4 pb-24">
      <header className="py-4">
        <h1 className="text-lg font-medium tracking-tight">Voice Journal</h1>
      </header>
      <main className="flex-1">
        <Outlet />
      </main>
      <nav className="fixed bottom-0 left-0 right-0 border-t bg-background/95 backdrop-blur">
        <ul className="mx-auto flex max-w-lg overflow-x-auto text-xs">
          {tabs.map((t) => (
            <li key={t.to}>
              <NavLink
                to={t.to}
                end={t.end}
                className={({ isActive }) =>
                  `block px-3 py-3 ${isActive ? "font-medium text-emerald-700" : "text-muted-foreground"}`
                }
              >
                {t.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  );
}
