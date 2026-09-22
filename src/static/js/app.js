/**
 * OmniSynapse-Titan Enterprise Dashboard Logic.
 */

document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  initAuditFlow();
  initGatewayFlow();
  initTemporalSlider();
  initTableCalculator();
  pollHealth();
});

// -----------------------------------------------------------------------------
// 1. Navigation Tabs
// -----------------------------------------------------------------------------
function initTabs() {
  const tabs = document.querySelectorAll(".tab-btn");
  const panes = document.querySelectorAll(".tab-pane");

  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      panes.forEach(p => p.classList.remove("active"));

      tab.classList.add("active");
      const targetPane = document.getElementById(tab.dataset.tab);
      if (targetPane) targetPane.classList.add("active");
    });
  });
}

// -----------------------------------------------------------------------------
// 2. 360° Risk Triangulation Audit
// -----------------------------------------------------------------------------
function initAuditFlow() {
  const btnAudit = document.getElementById("btn-run-audit");
  const btnFreeze = document.getElementById("btn-hitl-freeze");

  btnAudit.addEventListener("click", async () => {
    const vendorId = document.getElementById("vendor-select").value;
    const vendorText = document.getElementById("vendor-select").selectedOptions[0].text.split("(")[0].trim();
    const liabilityCap = parseFloat(document.getElementById("liability-input").value) || 2000000;

    btnAudit.innerText = "TRIANGULATING SOURCES...";
    btnAudit.style.opacity = "0.7";

    try {
      const response = await fetch("/api/v1/audit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          vendor_id: vendorId,
          vendor_name: vendorText,
          contract_liability_cap_usd: liabilityCap,
          user_clearance: "Procurement"
        })
      });

      const data = await response.json();
      updateAuditUI(data);
    } catch (err) {
      console.error("Audit failed:", err);
    } finally {
      btnAudit.innerHTML = `<span>RUN 360° TRIANGULATION AUDIT</span> <span class="btn-arrow">→</span>`;
      btnAudit.style.opacity = "1";
    }
  });

  // Human-in-the-loop freeze action
  btnFreeze.addEventListener("click", () => {
    const confirmed = confirm(
      "HITL GATE CONFIRMATION:\nAre you sure you want to execute an emergency purchase order freeze for this supplier in SAP ERP?"
    );
    if (confirmed) {
      btnFreeze.innerText = "FROZEN (OFFICER SIGNED)";
      btnFreeze.style.background = "#10b981";
      alert("✅ Human-In-The-Loop Action Executed: Purchase order block registered with audit timestamp.");
    }
  });
}

function updateAuditUI(data) {
  const fused = data.sources_fused;
  const docLiability = fused.contract_pdf.liability_cap_usd;
  const erpSpend = fused.client_erp_api.active_spend_usd;
  const gap = erpSpend - docLiability;

  document.getElementById("doc-liability").innerText = `$${docLiability.toLocaleString()}`;
  document.getElementById("erp-spend").innerText = `$${erpSpend.toLocaleString()}`;
  document.getElementById("exposure-gap").innerText = `$${Math.max(0, gap).toLocaleString()} USD`;

  const verdictTag = document.getElementById("verdict-tag");
  verdictTag.innerText = data.audit_verdict.replace(/_/g, " ");

  if (gap > 0 && fused.live_web_scraping_agent.recent_breaches_count > 0) {
    verdictTag.className = "verdict-tag tag-warning";
    document.getElementById("web-breach").innerText = "CVE-2026-4412";
  } else {
    verdictTag.className = "verdict-tag badge-emerald";
    document.getElementById("web-breach").innerText = "CLEAN";
  }
}

// -----------------------------------------------------------------------------
// 3. Resilient LLM Gateway
// -----------------------------------------------------------------------------
function initGatewayFlow() {
  const btnSend = document.getElementById("btn-send-query");
  const promptInput = document.getElementById("prompt-input");
  const termBody = document.getElementById("query-response");

  btnSend.addEventListener("click", async () => {
    const prompt = promptInput.value.trim();
    if (!prompt) return;

    termBody.innerText = "Routing query through Resilient LLM Gateway...\n[Checking Token Bucket Rate Limiter]\n[Scanning Semantic Cache]";

    try {
      const start = performance.now();
      const response = await fetch("/api/v1/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, tenant_id: "enterprise_web_ui" })
      });

      const elapsed = Math.round(performance.now() - start);
      const data = await response.json();

      if (response.ok) {
        document.getElementById("meta-provider").innerText = `Provider: ${data.provider_used}`;
        document.getElementById("meta-cached").innerText = `Cache: ${data.cached ? "HIT (<5ms)" : "MISS"}`;
        document.getElementById("meta-latency").innerText = `Latency: ${data.latency_ms || elapsed}ms`;
        document.getElementById("meta-cost").innerText = `Cost: $${data.cost_estimate_usd.toFixed(4)}`;

        termBody.innerText = data.content;
      } else {
        termBody.innerText = `[GATEWAY SHIELD TRIGGERED]\nStatus: ${response.status}\nDetail: ${data.detail}`;
      }
    } catch (err) {
      termBody.innerText = `Network Error: ${err.message}`;
    }
  });
}

function setQueryPrompt(text) {
  const input = document.getElementById("prompt-input");
  input.value = text;
}

// -----------------------------------------------------------------------------
// 4. Bi-Temporal GraphRAG Slider
// -----------------------------------------------------------------------------
function initTemporalSlider() {
  const slider = document.getElementById("temporal-slider");
  const dateLabel = document.getElementById("slider-date-label");
  const contractName = document.getElementById("graph-contract-name");
  const contractCap = document.getElementById("graph-contract-cap");

  slider.addEventListener("input", (e) => {
    const year = e.target.value;
    if (year === "2024" || year === "2025") {
      dateLabel.innerText = `${year}-06-01`;
      contractName.innerText = "Original MSA (2024)";
      contractCap.innerText = "Liability Cap: $2,000,000 USD";
      document.getElementById("node-active-contract").style.borderTopColor = "#06b6d4";
    } else {
      dateLabel.innerText = "2026-09-15";
      contractName.innerText = "Amendment No. 1 (2026)";
      contractCap.innerText = "Liability Cap: $10,000,000 USD (Amended)";
      document.getElementById("node-active-contract").style.borderTopColor = "#10b981";
    }
  });
}

// -----------------------------------------------------------------------------
// 5. DuckDB Table Calculator
// -----------------------------------------------------------------------------
function initTableCalculator() {
  const btnCalc = document.getElementById("btn-calc-price");
  const inputUnits = document.getElementById("compute-units-calc");

  btnCalc.addEventListener("click", async () => {
    const units = parseInt(inputUnits.value) || 750000;
    const sql = `SELECT volume_tier, unit_price_usd, guaranteed_sla FROM volume_pricing_matrix WHERE min_units <= ${units} AND max_units >= ${units};`;

    document.getElementById("sql-preview-text").innerText = sql;

    try {
      const response = await fetch("/api/v1/tables/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sql_query: sql })
      });

      const data = await response.json();
      if (data.results && data.results.length > 0) {
        const row = data.results[0];
        document.getElementById("stat-unit-price").innerText = `$${row.unit_price_usd.toFixed(3)}`;
        document.getElementById("stat-tier").innerText = row.volume_tier;
        document.getElementById("stat-sla").innerText = `${row.guaranteed_sla} Availability`;
      }
    } catch (err) {
      console.error("Table calculation error:", err);
    }
  });
}

// -----------------------------------------------------------------------------
// 6. System Health Poller
// -----------------------------------------------------------------------------
async function pollHealth() {
  try {
    const res = await fetch("/health");
    if (res.ok) {
      const data = await res.json();
      document.getElementById("circuit-badge").innerHTML = `<span>CIRCUIT: ${data.circuit_breaker_state}</span>`;
    }
  } catch (_) {
    // Keep default display
  }
}
