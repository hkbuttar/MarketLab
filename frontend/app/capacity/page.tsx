import { Sidebar } from "../../components/sidebar";
import { getCapacity } from "../../lib/capacity";
import { label } from "../../lib/dashboard";

function money(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value);
}

export default async function CapacityPage() {
  const { data, connected } = await getCapacity();

  return (
    <div className="shell">
      <Sidebar active="Capacity" connected={connected} />
      <main>
        <header className="topbar capacity-header">
          <div>
            <p className="eyebrow">Portfolio implementation / Capacity</p>
            <h1>Liquidity capacity</h1>
            <p className="lede">How much capital can each strategy absorb before execution becomes the constraint?</p>
          </div>
          {data && <span className="assumption-pill">≤ {(data.maximum_adv_participation * 100).toFixed(0)}% ADV · {data.liquidation_days} day</span>}
        </header>

        {!data ? (
          <article className="panel capacity-empty">
            <p className="eyebrow">Artifact required</p>
            <h2>Generate capacity diagnostics</h2>
            <code>python scripts/build_capacity_report.py</code>
          </article>
        ) : (
          <div className="capacity-list">
            {data.strategies.map((strategy) => {
              const maximumCost = Math.max(...strategy.curve.map((point) => point.estimated_cost_bps), 1);
              return (
                <article className="panel capacity-card" key={strategy.name}>
                  <div className="panel-heading">
                    <div><p className="eyebrow">{strategy.latest.date}</p><h2>{label(strategy.name)}</h2></div>
                    <span className="count-pill">{strategy.observations} rebalances</span>
                  </div>
                  <div className="capacity-metrics">
                    <div><span>Latest capacity</span><strong>{money(strategy.latest.maximum_aum)}</strong></div>
                    <div><span>Historical floor</span><strong>{money(strategy.historical_minimum_aum)}</strong></div>
                    <div><span>Binding security</span><strong>{strategy.latest.binding_symbol}</strong></div>
                  </div>
                  <div className="capacity-curve">
                    {strategy.curve.map((point) => (
                      <div className="capacity-point" key={point.aum}>
                        <span>{money(point.aum)}</span>
                        <i><b className={point.feasible ? "feasible" : "infeasible"} style={{ width: `${point.estimated_cost_bps / maximumCost * 100}%` }} /></i>
                        <strong>{point.estimated_cost_bps.toFixed(1)} bps</strong>
                        <em>{(point.maximum_participation * 100).toFixed(1)}% ADV</em>
                      </div>
                    ))}
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
}
