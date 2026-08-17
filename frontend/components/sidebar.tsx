const navigation = [
  { label: "Overview", href: "/" },
  { label: "Factor Lab", href: "/factors" },
  { label: "Capacity", href: "/capacity" },
  { label: "Strategies", href: "/strategies" },
  { label: "Backtests", href: "#" },
  { label: "ML Lab", href: "#" },
  { label: "Experiments", href: "#" },
  { label: "Reports", href: "#" },
];

export function Sidebar({ active, connected }: { active: string; connected: boolean }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="brand-mark">M</span>
        <div><strong>MarketLab</strong><small>Research OS</small></div>
      </div>
      <nav aria-label="Primary navigation">
        {navigation.map((item, index) => (
          <a className={item.label === active ? "nav-item active" : "nav-item"} href={item.href} key={item.label}>
            <span className="nav-index">0{index + 1}</span>{item.label}
          </a>
        ))}
      </nav>
      <div className="sidebar-foot">
        <span className={connected ? "status-dot online" : "status-dot"} />
        <div><strong>{connected ? "Research engine online" : "API unavailable"}</strong><small>FastAPI · v0.1</small></div>
      </div>
    </aside>
  );
}
