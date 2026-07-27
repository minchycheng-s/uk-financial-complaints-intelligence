const DEFAULT_V1 =
  "https://public.tableau.com/views/uk_financial_complaints_intelligence_public/ExecutiveOverview?:language=en-US&:showVizHome=no";
const DEFAULT_V2 =
  "https://public.tableau.com/views/uk_financial_complaints_intelligence_v2_public/EconomicandComplaintContext?:language=en-US&:showVizHome=no";

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function tableauUrl(value, fallback) {
  try {
    const url = new URL(value || fallback);
    if (url.protocol !== "https:" || url.hostname !== "public.tableau.com") {
      return fallback;
    }
    url.searchParams.set(":showVizHome", "no");
    return url.toString();
  } catch {
    return fallback;
  }
}

function renderHtml(v1Url, v2Url) {
  const v1 = escapeHtml(v1Url);
  const v2 = escapeHtml(v2Url);
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="description" content="An evidence-led UK financial complaints intelligence case study: prioritising which firm-product cases analysts should investigate first." />
  <title>UK Financial Complaints Intelligence — Business Case Study</title>
  <style>
    :root {
      --ink: #14213d;
      --navy: #0b2942;
      --paper: #f7f3eb;
      --card: #fffdf8;
      --orange: #ed6a2c;
      --amber: #f2b544;
      --red: #c8483f;
      --green: #1b6b5a;
      --muted: #5d675f;
      --line: #d9d3c7;
      --blue-pale: #e5eef2;
      --orange-pale: #fbe8dc;
      --shadow: 0 18px 45px rgba(20, 33, 61, .09);
    }
    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body {
      margin: 0;
      color: var(--ink);
      background:
        linear-gradient(rgba(20,33,61,.025) 1px, transparent 1px),
        linear-gradient(90deg, rgba(20,33,61,.025) 1px, transparent 1px),
        var(--paper);
      background-size: 40px 40px;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.55;
    }
    a { color: inherit; }
    .wrap { width: min(1180px, calc(100% - 40px)); margin: 0 auto; }
    nav {
      position: sticky; top: 0; z-index: 20;
      background: rgba(247,243,235,.94);
      border-bottom: 1px solid var(--line);
      backdrop-filter: blur(14px);
    }
    .nav-inner { min-height: 66px; display: flex; align-items: center; justify-content: space-between; gap: 24px; }
    .brand { font-weight: 850; letter-spacing: -.02em; text-decoration: none; }
    .nav-links { display: flex; flex-wrap: wrap; gap: 18px; font-size: .9rem; }
    .nav-links a { text-decoration: none; color: var(--muted); }
    .nav-links a:hover { color: var(--orange); }
    .hero { padding: 90px 0 54px; }
    .eyebrow {
      display: inline-flex; align-items: center; gap: 9px;
      color: var(--orange); font-size: .8rem; font-weight: 850;
      letter-spacing: .13em; text-transform: uppercase;
    }
    .eyebrow::before { content: ""; width: 28px; height: 3px; background: currentColor; }
    h1, h2, h3, p { margin-top: 0; }
    h1 {
      max-width: 980px; margin: 20px 0 22px;
      font-family: Georgia, "Times New Roman", serif;
      font-size: clamp(3rem, 7.2vw, 6.2rem); line-height: .98; letter-spacing: -.055em;
    }
    .lead { max-width: 810px; font-size: clamp(1.08rem, 2vw, 1.35rem); color: var(--muted); }
    .hero-actions { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 30px; }
    .button {
      display: inline-flex; align-items: center; justify-content: center;
      min-height: 48px; padding: 0 19px; border: 1px solid var(--ink);
      border-radius: 999px; font-weight: 760; text-decoration: none;
      background: var(--ink); color: white;
    }
    .button.secondary { background: transparent; color: var(--ink); }
    .button:hover { transform: translateY(-1px); box-shadow: 0 8px 22px rgba(20,33,61,.12); }
    .outcome-grid {
      display: grid; grid-template-columns: repeat(4, 1fr);
      border: 1px solid var(--line); background: var(--card); box-shadow: var(--shadow);
    }
    .outcome { padding: 24px; border-right: 1px solid var(--line); }
    .outcome:last-child { border-right: 0; }
    .outcome strong { display: block; font-family: Georgia, serif; font-size: 2.55rem; line-height: 1; }
    .outcome span { display: block; margin-top: 9px; color: var(--muted); font-size: .92rem; }
    section { padding: 78px 0; }
    .section-head { display: grid; grid-template-columns: .8fr 1.2fr; gap: 70px; margin-bottom: 36px; align-items: end; }
    h2 { font-family: Georgia, serif; font-size: clamp(2.2rem, 4vw, 4rem); line-height: 1.04; letter-spacing: -.04em; }
    .section-head p { color: var(--muted); font-size: 1.05rem; margin-bottom: 6px; }
    .problem-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; }
    .problem-card, .story, .action-card, .skill-card {
      background: var(--card); border: 1px solid var(--line); box-shadow: var(--shadow);
    }
    .problem-card { padding: 22px; min-height: 230px; }
    .number { color: var(--orange); font-weight: 850; font-size: .8rem; letter-spacing: .12em; }
    .problem-card h3 { margin: 42px 0 10px; font-size: 1.08rem; }
    .problem-card p { color: var(--muted); font-size: .91rem; margin: 0; }
    .stories { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
    .story { padding: 29px; border-top: 5px solid var(--orange); }
    .story:nth-child(2) { border-top-color: var(--amber); }
    .story:nth-child(3) { border-top-color: var(--green); }
    .story:nth-child(4) { border-top-color: var(--red); }
    .story-tag { font-size: .75rem; font-weight: 850; letter-spacing: .12em; text-transform: uppercase; color: var(--muted); }
    .story h3 { font-family: Georgia, serif; font-size: 1.75rem; line-height: 1.13; margin: 10px 0 22px; }
    .evidence { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin: 18px 0; }
    .evidence div { padding: 15px; background: var(--paper); border-left: 3px solid var(--orange); }
    .evidence strong { display: block; font-size: 1.45rem; }
    .evidence span { color: var(--muted); font-size: .82rem; }
    .decision { margin: 18px 0 0; padding-top: 16px; border-top: 1px solid var(--line); }
    .decision b { color: var(--green); }
    .anomaly {
      display: grid; grid-template-columns: 1fr auto 1fr auto 1fr; align-items: center; gap: 18px;
      padding: 34px; background: var(--navy); color: white; box-shadow: var(--shadow);
    }
    .anomaly-value { text-align: center; }
    .anomaly-value strong { display: block; font-family: Georgia, serif; font-size: clamp(2.2rem, 5vw, 4.6rem); }
    .anomaly-value span { color: #bed0d7; font-size: .9rem; }
    .operator { font-size: 2.2rem; color: var(--amber); }
    .anomaly-note { margin-top: 18px; padding: 17px 20px; background: var(--orange-pale); border-left: 4px solid var(--red); }
    .flow { display: grid; grid-template-columns: repeat(5, 1fr); gap: 0; }
    .flow-step { position: relative; padding: 25px 24px 25px 18px; background: var(--card); border: 1px solid var(--line); }
    .flow-step:not(:last-child)::after {
      content: "→"; position: absolute; right: -13px; top: 50%; z-index: 2;
      width: 26px; height: 26px; display: grid; place-items: center;
      border-radius: 50%; background: var(--orange); color: white; transform: translateY(-50%);
    }
    .flow-step strong { display: block; margin-bottom: 9px; }
    .flow-step span { color: var(--muted); font-size: .87rem; }
    .actions { display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; }
    .action-card { display: grid; grid-template-columns: 56px 1fr; gap: 18px; padding: 23px; }
    .action-icon { width: 48px; height: 48px; display: grid; place-items: center; border-radius: 50%; background: var(--blue-pale); color: var(--navy); font-weight: 900; }
    .action-card h3 { margin-bottom: 6px; }
    .action-card p { color: var(--muted); margin: 0; }
    .limits { background: var(--navy); color: white; }
    .limits .section-head p { color: #c2d1d7; }
    .limit-list { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
    .limit-list div { padding: 21px; border: 1px solid rgba(255,255,255,.2); color: #d6e0e4; }
    .limit-list b { color: white; }
    .dashboard-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
    .dashboard-card { padding: 20px; border: 1px solid var(--line); background: var(--card); box-shadow: var(--shadow); }
    .dashboard-card h3 { font-family: Georgia, serif; font-size: 1.7rem; margin: 0 0 7px; }
    .dashboard-card p { color: var(--muted); min-height: 50px; }
    .viz-frame { position: relative; width: 100%; aspect-ratio: 16 / 10; background: var(--blue-pale); overflow: hidden; border: 1px solid var(--line); }
    .viz-frame iframe { width: 100%; height: 100%; border: 0; }
    .dashboard-links { display: flex; gap: 10px; margin-top: 14px; }
    .dashboard-links a { font-weight: 760; color: var(--orange); }
    .skills { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
    .skill-card { padding: 22px; }
    .skill-card h3 { font-size: 1rem; margin-bottom: 9px; }
    .skill-card p { color: var(--muted); font-size: .9rem; margin: 0; }
    footer { padding: 34px 0 54px; border-top: 1px solid var(--line); color: var(--muted); }
    .footer-inner { display: flex; justify-content: space-between; gap: 24px; align-items: center; }
    .footer-inner a { color: var(--ink); font-weight: 760; }
    @media (max-width: 950px) {
      .outcome-grid, .problem-grid, .skills { grid-template-columns: 1fr 1fr; }
      .section-head { grid-template-columns: 1fr; gap: 10px; }
      .flow { grid-template-columns: 1fr; gap: 8px; }
      .flow-step:not(:last-child)::after { content: "↓"; right: 18px; top: auto; bottom: -17px; transform: none; }
      .limit-list { grid-template-columns: 1fr 1fr; }
    }
    @media (max-width: 680px) {
      .wrap { width: min(100% - 24px, 1180px); }
      .nav-links { display: none; }
      .hero { padding-top: 58px; }
      .outcome-grid, .problem-grid, .stories, .actions, .dashboard-grid, .skills, .limit-list { grid-template-columns: 1fr; }
      .outcome { border-right: 0; border-bottom: 1px solid var(--line); }
      .anomaly { grid-template-columns: 1fr; }
      .operator { transform: rotate(90deg); text-align: center; }
      .footer-inner { align-items: flex-start; flex-direction: column; }
    }
  </style>
</head>
<body>
  <nav>
    <div class="wrap nav-inner">
      <a class="brand" href="#top">Complaints Intelligence</a>
      <div class="nav-links">
        <a href="#problems">Problems solved</a>
        <a href="#findings">Evidence</a>
        <a href="#actions">Decisions</a>
        <a href="#dashboards">Dashboards</a>
      </div>
    </div>
  </nav>

  <main id="top">
    <header class="hero wrap">
      <span class="eyebrow">Evidence-led data analytics case study</span>
      <h1>Which complaints cases should analysts investigate first—and why?</h1>
      <p class="lead">I built a traceable review system for UK financial complaints data. It converts inconsistent regulatory workbooks into a prioritised queue, while keeping missing evidence, source anomalies and analytical limits visible.</p>
      <div class="hero-actions">
        <a class="button" href="#findings">See the decisions</a>
        <a class="button secondary" href="https://github.com/minchycheng-s/uk-financial-complaints-intelligence" target="_blank" rel="noreferrer">View code and methodology</a>
      </div>
    </header>

    <div class="wrap outcome-grid" aria-label="Latest reporting period outcomes">
      <div class="outcome"><strong>578</strong><span>firm-product observations assessed in 2025-H2</span></div>
      <div class="outcome"><strong>126</strong><span>observations justified review—21.8% of the period</span></div>
      <div class="outcome"><strong>13</strong><span>highest-priority observations to investigate first</span></div>
      <div class="outcome"><strong>71</strong><span>classified as insufficient data, not mistaken for low risk</span></div>
    </div>

    <section id="problems">
      <div class="wrap">
        <div class="section-head">
          <h2>The problem was decision quality, not a lack of charts.</h2>
          <p>Regulatory complaint data is useful only when analysts can compare like with like, find the cases that deserve attention and trace every signal back to evidence.</p>
        </div>
        <div class="problem-grid">
          <article class="problem-card"><span class="number">01</span><h3>Limited review capacity</h3><p>Hundreds of observations compete for attention. The output must tell reviewers where to start.</p></article>
          <article class="problem-card"><span class="number">02</span><h3>Large-firm bias</h3><p>Raw totals naturally favour large firms, so peer position and contextual rates are needed alongside counts.</p></article>
          <article class="problem-card"><span class="number">03</span><h3>Changing Excel layouts</h3><p>Headers, sheets and definitions change between reporting periods, threatening valid comparisons.</p></article>
          <article class="problem-card"><span class="number">04</span><h3>Missing ≠ safe</h3><p>Unavailable evidence must remain “insufficient data”; it must never silently become zero or low risk.</p></article>
          <article class="problem-card"><span class="number">05</span><h3>Scores need proof</h3><p>A warning without its rule, source workbook and cell lineage is not defensible in review.</p></article>
        </div>
      </div>
    </section>

    <section id="findings">
      <div class="wrap">
        <div class="section-head">
          <h2>Four business questions answered with evidence.</h2>
          <p>Each result is framed as a review decision—not as proof of misconduct, customer harm or causation.</p>
        </div>
        <div class="stories">
          <article class="story">
            <span class="story-tag">Question 1 · Capacity</span>
            <h3>Which cases should analysts review first?</h3>
            <p>The warning framework separates the latest period into actionable groups instead of producing an undifferentiated ranked list.</p>
            <div class="evidence"><div><strong>13</strong><span>highest priority</span></div><div><strong>113</strong><span>additional review</span></div></div>
            <p class="decision"><b>Decision:</b> investigate the 13 highest-priority observations first, then work through the remaining 113 review cases.</p>
          </article>
          <article class="story">
            <span class="story-tag">Question 2 · Workload</span>
            <h3>Where is review demand concentrated?</h3>
            <p>Counts identify workload; rates identify concentration. Both are needed to allocate review capacity fairly.</p>
            <div class="evidence"><div><strong>7 / 163</strong><span>Insurance & pure protection · 4.3%</span></div><div><strong>3 / 63</strong><span>Decumulation & pensions · 4.8%</span></div></div>
            <p class="decision"><b>Decision:</b> insurance creates the largest workload by count, while pensions has a slightly higher priority concentration.</p>
          </article>
          <article class="story">
            <span class="story-tag">Question 3 · Change</span>
            <h3>What drove the latest complaint increase?</h3>
            <p>Total complaints opened increased sharply, but the movement was not broad-based across every product group.</p>
            <div class="evidence"><div><strong>+56.1%</strong><span>all complaints opened, H1 to H2 2025</span></div><div><strong>+116.7%</strong><span>Consumer Credit</span></div></div>
            <p>Other product groups combined fell by roughly 5.0%.</p>
            <p class="decision"><b>Decision:</b> verify Consumer Credit definitions, comparability and reporting population before making an operational or risk conclusion.</p>
          </article>
          <article class="story">
            <span class="story-tag">Question 4 · Guardrails</span>
            <h3>How do we avoid false reassurance?</h3>
            <p>The model explicitly separates incomplete evidence and confirmed source anomalies from normal scoring.</p>
            <div class="evidence"><div><strong>71</strong><span>insufficient-data observations</span></div><div><strong>1</strong><span>confirmed source anomaly</span></div></div>
            <p class="decision"><b>Decision:</b> treat incomplete evidence as a review limitation and require documented business treatment for the source anomaly.</p>
          </article>
        </div>
      </div>
    </section>

    <section>
      <div class="wrap">
        <div class="section-head">
          <h2>A source anomaly the pipeline refused to hide.</h2>
          <p>For one UK Warranty observation, separate source sheets contained closure percentages that added to more than 100%. The extraction was correct; the source values were internally inconsistent.</p>
        </div>
        <div class="anomaly">
          <div class="anomaly-value"><strong>88.35%</strong><span>closed within 3 days</span></div>
          <div class="operator">+</div>
          <div class="anomaly-value"><strong>30.12%</strong><span>closed after 3 days, within 8 weeks</span></div>
          <div class="operator">=</div>
          <div class="anomaly-value"><strong>118.47%</strong><span>invalid combined timeliness</span></div>
        </div>
        <p class="anomaly-note"><b>Treatment:</b> preserve the reported values, flag the inconsistency and do not use the derived timeliness measure until the business defines an appropriate treatment.</p>
      </div>
    </section>

    <section>
      <div class="wrap">
        <div class="section-head">
          <h2>How raw files became defensible decisions.</h2>
          <p>The pipeline was designed for auditability: every transformation and warning remains explainable.</p>
        </div>
        <div class="flow">
          <div class="flow-step"><strong>1. Profile</strong><span>Discover workbooks, sheets, headers, types, missingness and schema changes.</span></div>
          <div class="flow-step"><strong>2. Extract</strong><span>Use sheet-specific rules without altering the raw Excel files.</span></div>
          <div class="flow-step"><strong>3. Reconcile</strong><span>Standardise firms and products, then check totals and rejected records.</span></div>
          <div class="flow-step"><strong>4. Compare</strong><span>Create period change, peer percentile and contextual features.</span></div>
          <div class="flow-step"><strong>5. Prioritise</strong><span>Apply transparent rules and retain workbook, sheet, row, column and cell evidence.</span></div>
        </div>
      </div>
    </section>

    <section id="actions">
      <div class="wrap">
        <div class="section-head">
          <h2>What a manager can do next.</h2>
          <p>The analysis supports focused investigation and data-quality decisions. It does not replace judgement.</p>
        </div>
        <div class="actions">
          <article class="action-card"><div class="action-icon">1</div><div><h3>Open the top-priority cases</h3><p>Begin with the 13 highest-priority observations and inspect the triggered rules and underlying evidence.</p></div></article>
          <article class="action-card"><div class="action-icon">2</div><div><h3>Allocate review capacity deliberately</h3><p>Use both the number of priority cases and their concentration rate when planning product-specialist workload.</p></div></article>
          <article class="action-card"><div class="action-icon">3</div><div><h3>Validate the Consumer Credit jump</h3><p>Check reporting scope, definitions and population changes before interpreting the 116.7% increase.</p></div></article>
          <article class="action-card"><div class="action-icon">4</div><div><h3>Resolve evidence limitations</h3><p>Keep insufficient-data cases separate and document a treatment before using the anomalous timeliness measure.</p></div></article>
        </div>
      </div>
    </section>

    <section class="limits">
      <div class="wrap">
        <div class="section-head">
          <h2>What this analysis does not claim.</h2>
          <p>These boundaries are part of the solution. A trustworthy analyst states what the available data cannot prove.</p>
        </div>
        <div class="limit-list">
          <div><b>No proof of harm.</b> A priority signal is a reason to investigate, not a finding of customer harm or misconduct.</div>
          <div><b>No severity measure.</b> The data does not fully describe individual customer loss, redress or complaint seriousness.</div>
          <div><b>No causal claim.</b> Bank Rate and inflation provide context only; parallel movement does not establish causation.</div>
          <div><b>No “no signal = safe”.</b> A quiet result may reflect insufficient evidence or rule coverage.</div>
          <div><b>No automatic breach finding.</b> The framework does not determine regulatory non-compliance.</div>
          <div><b>No product-group judgement.</b> Higher counts do not prove a product group is inherently worse.</div>
        </div>
      </div>
    </section>

    <section id="dashboards">
      <div class="wrap">
        <div class="section-head">
          <h2>Explore the published evidence.</h2>
          <p>These are direct Tableau Public views. Workbook navigation stays inside Tableau, avoiding duplicate portfolio controls.</p>
        </div>
        <div class="dashboard-grid">
          <article class="dashboard-card">
            <h3>Complaints intelligence suite</h3>
            <p>Executive overview, priority review, firm-product exploration, rule explanation and data-quality controls.</p>
            <div class="viz-frame"><iframe src="${v1}" title="Complaints intelligence Tableau workbook" loading="lazy" allowfullscreen></iframe></div>
            <div class="dashboard-links"><a href="${v1}" target="_blank" rel="noreferrer">Open full workbook ↗</a></div>
          </article>
          <article class="dashboard-card">
            <h3>Economic and complaint context</h3>
            <p>Bank Rate, CPI/CPIH inflation and product-level complaint movement shown as context, not causation.</p>
            <div class="viz-frame"><iframe src="${v2}" title="Economic and complaint context Tableau workbook" loading="lazy" allowfullscreen></iframe></div>
            <div class="dashboard-links"><a href="${v2}" target="_blank" rel="noreferrer">Open full workbook ↗</a></div>
          </article>
        </div>
      </div>
    </section>

    <section>
      <div class="wrap">
        <div class="section-head">
          <h2>Capabilities demonstrated.</h2>
          <p>The project shows an end-to-end analytical approach: define the decision, engineer trustworthy data, analyse it carefully and communicate an actionable result.</p>
        </div>
        <div class="skills">
          <article class="skill-card"><h3>Business problem framing</h3><p>Turned a broad “early warning” brief into a concrete prioritisation question and review workflow.</p></article>
          <article class="skill-card"><h3>Data engineering</h3><p>Built reusable Python profiling, extraction, reconciliation and analysis-ready table pipelines.</p></article>
          <article class="skill-card"><h3>Analytical reasoning</h3><p>Used peer groups, time change, evidence sufficiency and transparent rules without overstating conclusions.</p></article>
          <article class="skill-card"><h3>Data quality governance</h3><p>Preserved raw values, source-cell lineage, exception decisions, review gates and methodological caveats.</p></article>
          <article class="skill-card"><h3>Entity resolution</h3><p>Resolved firm identity across periods with suggestions, manual review and retained unresolved cases.</p></article>
          <article class="skill-card"><h3>Dashboard design</h3><p>Created Tableau views for executives, reviewers, investigators and data-quality monitoring.</p></article>
          <article class="skill-card"><h3>Testing and reproducibility</h3><p>Added automated tests, documented methods and version-controlled the complete workflow.</p></article>
          <article class="skill-card"><h3>Plain-English communication</h3><p>Separated evidence, interpretation, decision and limitation so non-specialists can act responsibly.</p></article>
        </div>
      </div>
    </section>
  </main>

  <footer>
    <div class="wrap footer-inner">
      <div><b>UK Financial Complaints Intelligence</b><br />Portfolio case study · analytical prioritisation only</div>
      <a href="https://github.com/minchycheng-s/uk-financial-complaints-intelligence" target="_blank" rel="noreferrer">Repository and documentation ↗</a>
    </div>
  </footer>
</body>
</html>`;
}

export default {
  async fetch(_request, env) {
    const v1 = tableauUrl(env.TABLEAU_V1_URL, DEFAULT_V1);
    const v2 = tableauUrl(env.TABLEAU_V2_URL, DEFAULT_V2);
    return new Response(renderHtml(v1, v2), {
      headers: {
        "content-type": "text/html; charset=utf-8",
        "cache-control": "public, max-age=300",
        "content-security-policy":
          "default-src 'self'; style-src 'unsafe-inline'; frame-src https://public.tableau.com; img-src 'self' data:; script-src 'none'; base-uri 'none'; frame-ancestors 'none'",
        "referrer-policy": "strict-origin-when-cross-origin",
        "x-content-type-options": "nosniff",
      },
    });
  },
};
