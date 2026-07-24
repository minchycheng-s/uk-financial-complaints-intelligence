const metrics = [
  ["75,231", "source metric records"],
  ["5,751", "firm-product-period observations"],
  ["10", "half-year reporting periods"],
  ["85", "automated tests"],
];

const workflow = [
  ["01", "Profile", "Discover workbook structures, sheets, headers and schema drift."],
  ["02", "Extract", "Standardise period-specific Excel layouts without changing raw files."],
  ["03", "Validate", "Reconcile totals, preserve lineage and surface quality exceptions."],
  ["04", "Analyse", "Build peer benchmarks, transparent signals and review queues."],
  ["05", "Explain", "Connect every dashboard result to its rule and source cell."],
];

const findings = [
  {
    value: "13",
    title: "latest priority observations",
    text: "A focused investigation queue across 13 firms in 2025-H2.",
  },
  {
    value: "71",
    title: "insufficient-evidence observations",
    text: "Kept separate from no-current-signal results to avoid false reassurance.",
  },
  {
    value: "1",
    title: "confirmed source anomaly",
    text: "Preserved exactly as published and excluded from misleading derivations.",
  },
];

const skills = [
  "Python",
  "pandas",
  "openpyxl",
  "pytest",
  "Tableau",
  "Data profiling",
  "Data modelling",
  "Quality assurance",
  "Risk analytics",
  "Governance",
];

function Arrow() {
  return <span aria-hidden="true">↗</span>;
}

export default function Home() {
  return (
    <main>
      <nav className="nav shell">
        <a className="brand" href="#top" aria-label="Portfolio home">
          MC<span>.</span>
        </a>
        <div className="navLinks">
          <a href="#case-study">Case study</a>
          <a href="#findings">Findings</a>
          <a href="#method">Method</a>
          <a
            className="navCta"
            href="https://github.com/minchycheng-s/uk-financial-complaints-intelligence"
            target="_blank"
            rel="noreferrer"
          >
            View GitHub <Arrow />
          </a>
        </div>
      </nav>

      <section className="hero shell" id="top">
        <div className="eyebrow">Data analytics portfolio · FCA complaints</div>
        <div className="heroGrid">
          <div>
            <h1>
              From difficult Excel files to
              <em> decision-ready intelligence.</em>
            </h1>
            <p className="lead">
              I built an auditable Python and Tableau platform that turns five years of
              inconsistent FCA complaints workbooks into explainable investigation
              priorities—with every result traceable to its source.
            </p>
            <div className="heroActions">
              <a href="#case-study" className="button primary">
                Explore the case study <Arrow />
              </a>
              <a
                href="https://github.com/minchycheng-s/uk-financial-complaints-intelligence"
                target="_blank"
                rel="noreferrer"
                className="button secondary"
              >
                Read the code
              </a>
            </div>
          </div>
          <div className="signalCard" aria-label="Illustration of the analytical dashboard">
            <div className="cardTop">
              <span>Signal monitor</span>
              <span className="live"><i /> 2025-H2</span>
            </div>
            <div className="chart">
              {[48, 61, 59, 72, 66, 78, 74, 83, 79, 88].map((height, index) => (
                <div className="barWrap" key={index}>
                  <div
                    className={`bar ${index === 9 ? "active" : ""}`}
                    style={{ height: `${height}%` }}
                  />
                  <small>{index % 2 === 0 ? String(21 + index / 2) : ""}</small>
                </div>
              ))}
            </div>
            <div className="cardFooter">
              <div><strong>13</strong><span>priority firms</span></div>
              <div><strong>293</strong><span>latest firms</span></div>
              <div><strong>578</strong><span>observations</span></div>
            </div>
          </div>
        </div>
        <div className="metricStrip">
          {metrics.map(([value, label]) => (
            <div key={label}><strong>{value}</strong><span>{label}</span></div>
          ))}
        </div>
      </section>

      <section className="problem section shell" id="case-study">
        <div className="sectionLabel">01 · The challenge</div>
        <div className="twoCol">
          <h2>Public data was available. Reliable longitudinal analysis was not.</h2>
          <div className="prose">
            <p>
              FCA complaints data arrived as period-specific Excel workbooks. Headers
              moved, sheet purposes differed, product definitions evolved and identical
              looking values sometimes represented different measurement bases.
            </p>
            <p>
              The task was not simply to concatenate spreadsheets. It was to create a
              defensible analytical record while respecting the meaning—and the
              limitations—of the original data.
            </p>
          </div>
        </div>
        <div className="challengeGrid">
          <article><span>Schema drift</span><p>Layouts and headers changed across ten reporting periods.</p></article>
          <article><span>Semantic risk</span><p>Counts, percentages and per-1,000 context rates could not be mixed.</p></article>
          <article><span>Identity gaps</span><p>Firm names varied and FRNs were not consistently available.</p></article>
          <article><span>Source anomalies</span><p>Published inconsistencies needed preservation, not silent correction.</p></article>
        </div>
      </section>

      <section className="dark section" id="method">
        <div className="shell">
          <div className="sectionLabel light">02 · The approach</div>
          <div className="twoCol">
            <h2>A pipeline designed for trust before speed.</h2>
            <p className="darkLead">
              Each stage creates an explicit output and quality gate. Raw Excel files are
              read-only; ambiguous decisions remain reviewable mappings rather than
              hidden cleaning rules.
            </p>
          </div>
          <div className="workflow">
            {workflow.map(([number, title, text]) => (
              <article key={number}>
                <span>{number}</span>
                <h3>{title}</h3>
                <p>{text}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="section shell" id="findings">
        <div className="sectionLabel">03 · What the analysis surfaced</div>
        <div className="twoCol findingsIntro">
          <h2>A small priority queue, with clear evidence boundaries.</h2>
          <p>
            The warning methodology combines peer-relative, deterioration, volume and
            timeliness signals. It prioritises investigation; it does not claim to
            predict misconduct or customer harm.
          </p>
        </div>
        <div className="findingGrid">
          {findings.map((finding) => (
            <article key={finding.title}>
              <strong>{finding.value}</strong>
              <h3>{finding.title}</h3>
              <p>{finding.text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="dashboardSection">
        <div className="shell">
          <div className="sectionLabel">04 · Dashboard experience</div>
          <div className="dashboardMock">
            <div className="dashHeader">
              <div>
                <small>UK Financial Complaints Intelligence</small>
                <h3>Executive overview</h3>
              </div>
              <span>Latest period · 2025-H2</span>
            </div>
            <div className="dashKpis">
              <div><b>293</b><span>latest firms</span></div>
              <div><b>13</b><span>priority firms</span></div>
              <div><b>71</b><span>insufficient data</span></div>
              <div><b>1</b><span>source anomaly</span></div>
            </div>
            <div className="dashBody">
              <div className="trendPanel">
                <h4>Warning trend</h4>
                <div className="stacked">
                  {[48, 62, 58, 71, 66, 74, 69, 81, 76, 84].map((h, i) => (
                    <div key={i} style={{ height: `${h}%` }}>
                      <i /><i /><i />
                    </div>
                  ))}
                </div>
              </div>
              <div className="productPanel">
                <h4>Latest product signals</h4>
                {[
                  ["Insurance & protection", 92],
                  ["Consumer credit", 68],
                  ["Investments", 48],
                  ["Pensions", 41],
                  ["Home finance", 28],
                ].map(([label, width]) => (
                  <div className="productRow" key={label}>
                    <span>{label}</span><i style={{ width: `${width}%` }} />
                  </div>
                ))}
              </div>
            </div>
          </div>
          <p className="caption">
            The Tableau layer supports an investigation journey from executive signals
            to firm history, rule explanation and exact workbook cell lineage.
          </p>
        </div>
      </section>

      <section className="section shell learning">
        <div className="sectionLabel">05 · What this project demonstrates</div>
        <div className="twoCol">
          <h2>Analysis is strongest when uncertainty stays visible.</h2>
          <div className="prose">
            <p>
              The most important design decision was separating “no current signal”
              from “insufficient data.” Missing evidence was never converted to zero,
              and fuzzy firm matches were never accepted without review.
            </p>
            <p>
              That made the final dashboard more than a visual layer: it became an
              auditable interface to the whole analytical process.
            </p>
          </div>
        </div>
        <div className="skills">
          {skills.map((skill) => <span key={skill}>{skill}</span>)}
        </div>
      </section>

      <section className="cta">
        <div className="shell ctaInner">
          <div>
            <div className="sectionLabel light">Explore the work</div>
            <h2>See the complete pipeline, tests and methodology.</h2>
          </div>
          <a
            className="button pale"
            href="https://github.com/minchycheng-s/uk-financial-complaints-intelligence"
            target="_blank"
            rel="noreferrer"
          >
            Open GitHub repository <Arrow />
          </a>
        </div>
      </section>

      <footer className="shell">
        <div><strong>Mingzhi Cheng</strong><span>Data analytics portfolio</span></div>
        <p>
          Analytical demonstration only. Signals are not findings of misconduct or
          customer harm.
        </p>
      </footer>
    </main>
  );
}
