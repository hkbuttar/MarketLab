import { Sidebar } from "../../components/sidebar";
import { StrategyBuilder } from "../../components/strategy-builder";
import { getStrategies } from "../../lib/strategies";

export default async function StrategiesPage() {
  const result = await getStrategies();
  return (
    <div className="shell">
      <Sidebar active="Strategies" connected={result.connected} />
      <main>
        <header className="topbar">
          <div><p className="eyebrow">Research workspace / Strategy Builder</p><h1>Define the test before seeing the result.</h1><p className="lede">Run canonical strategies with explicit dates, capital, and cost assumptions.</p></div>
        </header>
        {!result.connected && <div className="connection-banner">Start FastAPI on port 8000 to load strategies and submit backtests.</div>}
        {result.items.length ? <StrategyBuilder strategies={result.items} /> : <p className="empty-state">No executable strategies are available.</p>}
      </main>
    </div>
  );
}
