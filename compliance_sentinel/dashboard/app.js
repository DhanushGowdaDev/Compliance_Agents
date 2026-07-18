/* app.js — Compliance Sentinel Dashboard Logic */
const API = window.location.origin;
const RATING_COLORS = { Red:'#ef4444', Amber:'#f59e0b', Green:'#10b981' };
const AGENT_COLORS  = { legal_agent:'#818cf8', data_privacy_agent:'#38bdf8', commercial_agent:'#fb923c' };

let _data = null;         // full risk_map array
let _contractId = null;
let _view = 'buyer';
let _selected = null;    // selected clause entry

// ── Bootstrap ────────────────────────────────────────────────────────────────
async function init() {
  await loadContracts();
  document.getElementById('contract-select').addEventListener('change', e => {
    _contractId = e.target.value;
    if (_contractId) loadData();
  });
  document.getElementById('view-select').addEventListener('change', e => {
    _view = e.target.value;
    if (_contractId) loadData();
  });
}

// ── Load contract list ────────────────────────────────────────────────────────
async function loadContracts() {
  try {
    const res = await fetch(`${API}/api/contracts`);
    const json = await res.json();
    const sel = document.getElementById('contract-select');
    if (!json.contracts.length) {
      sel.innerHTML = '<option value="">No contracts found — run pipeline first</option>';
      return;
    }
    sel.innerHTML = json.contracts.map(c =>
      `<option value="${c.id}">${c.id}</option>`
    ).join('');
    _contractId = json.contracts[0].id;
    loadData();
  } catch (e) {
    console.error('loadContracts:', e);
  }
}

// ── Load scorecard data ───────────────────────────────────────────────────────
async function loadData() {
  try {
    const res = await fetch(`${API}/api/scorecard/${_contractId}?view=${_view}`);
    if (!res.ok) { showToast('Scorecard not found for this contract.'); return; }
    const json = await res.json();
    _data = json.risk_map || [];
    const summary = json.summary || {};
    updateStats(summary, _data);
    renderPlot(_data);
    renderClauseList(_data);
    renderMediatorList(_data);
    loadAudit();
    // Risk badge
    const badge = document.getElementById('risk-badge');
    badge.style.display = '';
    const pct = summary.total ? Math.round((summary.red / summary.total) * 100) : 0;
    badge.className = `risk-badge ${pct > 30 ? 'risk-high' : pct > 10 ? 'risk-med' : 'risk-low'}`;
    badge.textContent = pct > 30 ? 'High Risk' : pct > 10 ? 'Medium Risk' : 'Low Risk';
  } catch (e) {
    console.error('loadData:', e);
    showToast('Error loading data. Is the server running?');
  }
}

// ── Stats bar ─────────────────────────────────────────────────────────────────
function updateStats(summary, data) {
  document.getElementById('s-total').textContent   = summary.total  ?? data.length;
  document.getElementById('s-red').textContent     = summary.red    ?? 0;
  document.getElementById('s-amber').textContent   = summary.amber  ?? 0;
  document.getElementById('s-green').textContent   = summary.green  ?? 0;
  const clauses = [...new Set(data.map(e => e.clause_id))].length;
  document.getElementById('s-clauses').textContent = clauses;
}

// ── Plotly 2D Risk Map ────────────────────────────────────────────────────────
function renderPlot(data) {
  const agents = [...new Set(data.map(e => e.agent_source))];
  
  // Custom glowing marker colors
  const GLOW_COLORS = {
    Red: 'rgba(239, 68, 68, 0.9)',
    Amber: 'rgba(245, 158, 11, 0.9)',
    Green: 'rgba(16, 185, 129, 0.9)'
  };
  
  const traces = agents.map(agent => {
    const pts = data.filter(e => e.agent_source === agent);
    return {
      x: pts.map(e => e.x_likelihood),
      y: pts.map(e => e.y_impact),
      mode: 'markers+text',
      type: 'scatter',
      name: agent.replace(/_/g,' '),
      textposition: 'top center',
      text: pts.map(e => e.rating === 'Red' ? '§ ' + e.clause_id : ''), // only label reds
      textfont: { family: 'Inter', size: 10, color: '#f87171' },
      hovertext: pts.map(e => 
        `<b>Clause ${e.clause_id}</b> [${e.rule_id}]<br>` +
        `<i>${e.agent_source.replace(/_/g, ' ').toUpperCase()}</i><br><br>` +
        `<b>Risk Score:</b> Likelihood ${e.x_likelihood} / Impact ${e.y_impact}<br>` +
        `<b>Finding:</b> ${(e.reason||'').slice(0, 90)}...<br>` +
        (e.suggested_redline && !e.suggested_redline.includes('unavailable') 
          ? `<br><b>💡 Suggested Fix:</b> ${e.suggested_redline.slice(0, 70)}...` : '')
      ),
      hovertemplate: 
        '<div style="padding:10px;border-radius:8px;background:rgba(15,22,41,0.95);border:1px solid #1e2d4a;backdrop-filter:blur(10px)">' +
        '<span style="font-family:Inter;font-size:12px;color:#e2e8f0;line-height:1.5">%{hovertext}</span>' +
        '</div><extra></extra>',
      marker: {
        size: pts.map(e => e.rating === 'Red' ? 22 : e.rating === 'Amber' ? 16 : 10),
        color: pts.map(e => GLOW_COLORS[e.rating] || '#64748b'),
        line: { 
          color: pts.map(e => e.rating === 'Red' ? '#ffffff' : AGENT_COLORS[agent]), 
          width: pts.map(e => e.rating === 'Red' ? 2 : 1) 
        },
        opacity: 0.9,
      },
      customdata: pts.map(e => e),
    };
  });

  const layout = {
    paper_bgcolor: 'transparent',
    plot_bgcolor:  'transparent',
    font: { family: 'Inter', color: '#64748b', size: 12 },
    margin: { l: 60, r: 30, t: 40, b: 60 },
    hoverlabel: { bgcolor: 'transparent', bordercolor: 'transparent' },
    xaxis: {
      title: '<b>Likelihood of Enforcement</b> →',
      range: [-0.5, 11],
      gridcolor: 'rgba(30, 45, 74, 0.4)',
      zerolinecolor: 'rgba(30, 45, 74, 0.8)',
      tickfont: { size: 10, color: '#475569' },
      tickvals: [0, 2, 4, 6, 8, 10],
    },
    yaxis: {
      title: '<b>Business Impact</b> →',
      range: [-0.5, 11],
      gridcolor: 'rgba(30, 45, 74, 0.4)',
      zerolinecolor: 'rgba(30, 45, 74, 0.8)',
      tickfont: { size: 10, color: '#475569' },
      tickvals: [0, 2, 4, 6, 8, 10],
    },
    legend: { 
      font: { size: 11, color: '#cbd5e1' }, 
      bgcolor: 'rgba(15,22,41,0.6)', 
      bordercolor: '#1e2d4a',
      borderwidth: 1,
      x: 0.98, xanchor: 'right', y: 0.98, yanchor: 'top',
      borderpad: 8
    },
    shapes: [
      // High Risk Zone (Top Right)
      { type:'rect', x0:6, y0:6, x1:11, y1:11, fillcolor:'rgba(239,68,68,0.08)', line:{width:1, color:'rgba(239,68,68,0.2)', dash:'dot'} },
      // Medium Risk Zone (Middle)
      { type:'rect', x0:3, y0:3, x1:6,  y1:6,  fillcolor:'rgba(245,158,11,0.05)', line:{width:1, color:'rgba(245,158,11,0.2)', dash:'dot'} },
      // Low Risk Zone (Bottom Left)
      { type:'rect', x0:0, y0:0, x1:3,  y1:3,  fillcolor:'rgba(16,185,129,0.03)', line:{width:1, color:'rgba(16,185,129,0.1)', dash:'dot'} },
    ],
    annotations: [
      { x:8.5, y:10.5, text:'CRITICAL BLOCKERS', showarrow:false, font:{size:11, weight:'bold', color:'rgba(239,68,68,0.7)', letterSpacing:'2px'} },
      { x:4.5, y:5.5,  text:'NEGOTIATION ZONES', showarrow:false, font:{size:10, weight:'bold', color:'rgba(245,158,11,0.5)', letterSpacing:'1px'} },
      { x:1.5, y:1.5,  text:'MARKET STANDARD',   showarrow:false, font:{size:10, weight:'bold', color:'rgba(16,185,129,0.4)', letterSpacing:'1px'} },
    ],
  };

  Plotly.newPlot('risk-plot', traces, layout, {
    responsive: true,
    displayModeBar: false,
  });

  document.getElementById('risk-plot').on('plotly_click', ev => {
    const pt = ev.points[0];
    if (pt && pt.customdata) selectEntry(pt.customdata);
  });
}

// ── Clause list (sidebar) ─────────────────────────────────────────────────────
function renderClauseList(data) {
  // Group by clause_id, take worst rating per clause
  const byClause = {};
  data.forEach(e => {
    const order = { Red:0, Amber:1, Green:2 };
    if (!byClause[e.clause_id] || order[e.rating] < order[byClause[e.clause_id].rating]) {
      byClause[e.clause_id] = e;
    }
  });
  const entries = Object.values(byClause).sort((a,b) => b.y_impact - a.y_impact);

  const html = entries.map(e => {
    const bv = e.benchmark_verdict || '';
    const bc = bv === 'aggressive' ? 'bench-agg' : bv === 'lenient' ? 'bench-len' : bv === 'standard' ? 'bench-std' : 'bench-na';
    return `<div class="clause-card" id="cc-${e.clause_id}" onclick="selectEntry(getEntry('${e.clause_id}'))">
      <div class="cc-header">
        <span class="cc-id">§ ${e.clause_id}</span>
        <span class="rating-dot" style="background:${RATING_COLORS[e.rating]||'#64748b'}"></span>
        <span style="font-size:.72rem;font-weight:600;color:${RATING_COLORS[e.rating]||'#64748b'}">${e.rating}</span>
        <span class="cc-agent">${(e.agent_source||'').replace(/_/g,' ')}</span>
      </div>
      <div class="cc-reason">${(e.reason||'').slice(0,120)}${(e.reason||'').length>120?'…':''}</div>
      ${bv ? `<span class="cc-bench ${bc}">${bv}</span>` : ''}
    </div>`;
  }).join('');

  document.getElementById('clause-list').innerHTML = html || '<div class="empty"><p>No clauses.</p></div>';
}

function getEntry(clauseId) {
  if (!_data) return null;
  const order = { Red:0, Amber:1, Green:2 };
  return _data.filter(e => e.clause_id === clauseId)
    .sort((a,b) => (order[a.rating]||2) - (order[b.rating]||2))[0] || null;
}

// ── Select entry → detail panel ───────────────────────────────────────────────
function selectEntry(entry) {
  if (!entry) return;
  _selected = entry;

  // Highlight card
  document.querySelectorAll('.clause-card').forEach(c => c.classList.remove('selected'));
  const cc = document.getElementById(`cc-${entry.clause_id}`);
  if (cc) cc.classList.add('selected');

  const rating   = entry.rating || 'Green';
  const rColor   = RATING_COLORS[rating] || '#64748b';
  const bv       = entry.benchmark_verdict || '';
  const bc       = bv === 'aggressive' ? 'bench-agg' : bv === 'lenient' ? 'bench-len' : bv === 'standard' ? 'bench-std' : 'bench-na';
  const redline  = entry.suggested_redline || '';
  const showRL   = redline && !redline.includes('unavailable');
  const comps    = entry.compromise_options || [];

  const compHtml = comps.length ? `
    <div class="detail-section">
      <div class="ds-label">⚖ Mediator Compromise Options</div>
      <div class="compromise-grid">
        ${comps.map((c,i) => `
          <div class="comp-option">
            <div style="font-size:.65rem;font-weight:700;color:var(--accent);margin-bottom:.4rem">Option ${i+1}</div>
            <div class="comp-text">${(c.compromise_text||'').slice(0,200)}${(c.compromise_text||'').length>200?'…':''}</div>
            <div style="font-size:.65rem;color:var(--muted);margin-bottom:.4rem;font-style:italic">${c.rationale||''}</div>
            <div class="score-bars">
              ${scoreBar('Buyer Risk ↓', c.buyer_risk_reduction, '#10b981')}
              ${scoreBar('Vendor Cost', c.vendor_effort_cost, '#818cf8')}
              ${scoreBar('Deal Speed', c.deal_speed_score, '#f59e0b')}
            </div>
          </div>`).join('')}
      </div>
    </div>` : '';

  document.getElementById('detail-empty').style.display = 'none';
  document.getElementById('detail-content').style.display = '';
  document.getElementById('detail-content').innerHTML = `
    <div class="detail-card">
      <div class="detail-section">
        <div style="display:flex;align-items:center;gap:.6rem;flex-wrap:wrap">
          <span style="font-size:1rem;font-weight:700">Clause ${entry.clause_id}</span>
          <span class="risk-badge" style="background:${rColor}22;color:${rColor};border-color:${rColor}44">${rating}</span>
          <span style="font-size:.7rem;font-family:monospace;color:var(--muted)">${entry.rule_id||''}</span>
          ${bv ? `<span class="cc-bench ${bc}">${bv}</span>` : ''}
        </div>
      </div>

      <div class="detail-section">
        <div class="ds-label">Agent Finding</div>
        <div class="ds-text">${entry.reason || '—'}</div>
        <div style="font-size:.65rem;color:var(--muted);margin-top:.25rem">
          ${(entry.agent_source||'').replace(/_/g,' ')} ·
          Likelihood ${entry.x_likelihood}/10 · Impact ${entry.y_impact}/10
          ${entry.comparison_note ? `· ${entry.comparison_note}` : ''}
        </div>
      </div>

      ${showRL ? `
      <div class="detail-section">
        <div class="ds-label">✏ Suggested Redline</div>
        <div class="redline-box">${redline}</div>
        <div class="actions" style="margin-top:.5rem">
          <button class="btn-accept" onclick="submitOverride('accept')">✓ Accept</button>
          <button class="btn-reject" onclick="submitOverride('reject')">✕ Reject</button>
          <button class="btn-edit"   onclick="openEdit()">✎ Edit</button>
        </div>
        <div id="edit-area" style="display:none;margin-top:.5rem">
          <textarea id="edit-text" rows="4" style="width:100%;background:#0a0f1e;border:1px solid var(--border);color:var(--text);border-radius:.4rem;padding:.5rem;font-size:.78rem;resize:vertical;font-family:inherit">${redline}</textarea>
          <div class="actions" style="margin-top:.4rem">
            <button class="btn-accept" onclick="submitOverride('edit')">Save Edit</button>
            <button class="btn-plain"  onclick="cancelEdit()">Cancel</button>
          </div>
        </div>
      </div>` : ''}

      ${compHtml}
    </div>`;
}

function scoreBar(label, val, color) {
  const pct = Math.min(100, Math.max(0, ((val||0)/5)*100));
  return `<div class="score-row">
    <span class="score-label">${label}</span>
    <div class="score-bar-bg"><div class="score-bar-fill" style="width:${pct}%;background:${color}"></div></div>
    <span style="color:${color};font-weight:700;width:16px;text-align:right">${val||0}</span>
  </div>`;
}

function openEdit()   { document.getElementById('edit-area').style.display = '' }
function cancelEdit() { document.getElementById('edit-area').style.display = 'none' }

async function submitOverride(action) {
  if (!_selected || !_contractId) return;
  const note = action === 'edit'
    ? (document.getElementById('edit-text')?.value || '') : '';
  try {
    await fetch(`${API}/api/override`, {
      method: 'POST',
      headers: { 'Content-Type':'application/json' },
      body: JSON.stringify({
        contract_id:    _contractId,
        clause_id:      _selected.clause_id,
        human_override: action,
        override_by:    'reviewer',
        override_note:  note,
      }),
    });
    showToast(`Clause ${_selected.clause_id} marked: ${action}`);
    loadAudit();
    if (action === 'edit') cancelEdit();
  } catch(e) {
    showToast('Failed to save override.');
  }
}

// ── Mediator sidebar ──────────────────────────────────────────────────────────
function renderMediatorList(data) {
  const withComps = data.filter(e => e.compromise_options && e.compromise_options.length);
  if (!withComps.length) {
    document.getElementById('mediator-list').innerHTML =
      '<div class="empty"><h3>No compromise suggestions</h3><p>Run pipeline with a valid NIM key to generate mediator options.</p></div>';
    return;
  }
  const html = withComps.map(e => `
    <div class="clause-card" onclick="selectEntry(${JSON.stringify(e).replace(/"/g,'&quot;')})">
      <div class="cc-header">
        <span class="cc-id">§ ${e.clause_id}</span>
        <span style="font-size:.7rem;color:var(--accent)">${e.compromise_options.length} option(s)</span>
      </div>
      ${e.compromise_options.map((c,i) => `
        <div style="font-size:.7rem;color:var(--muted);margin:.3rem 0 .1rem">Option ${i+1}:</div>
        <div style="font-size:.72rem;color:#94a3b8;line-height:1.3">${(c.compromise_text||'').slice(0,100)}…</div>
        <div style="display:flex;gap:.5rem;margin-top:.35rem;flex-wrap:wrap">
          ${scoreBar('Buyer Risk ↓',c.buyer_risk_reduction,'#10b981')}
        </div>`).join('')}
    </div>`).join('');
  document.getElementById('mediator-list').innerHTML = html;
}

// ── Sidebar tab switch ────────────────────────────────────────────────────────
function switchSideTab(tab) {
  document.getElementById('tab-clauses').classList.toggle('active', tab==='clauses');
  document.getElementById('tab-mediator').classList.toggle('active', tab==='mediator');
  document.getElementById('side-clauses').style.display  = tab==='clauses'  ? '' : 'none';
  document.getElementById('side-mediator').style.display = tab==='mediator' ? '' : 'none';
}

// ── Audit trail ───────────────────────────────────────────────────────────────
async function loadAudit() {
  if (!_contractId) return;
  try {
    const res = await fetch(`${API}/api/audit/${_contractId}`);
    const json = await res.json();
    const trail = json.trail || [];
    document.getElementById('audit-count').textContent = trail.length ? `(${trail.length})` : '';
    if (!trail.length) {
      document.getElementById('audit-empty').style.display = '';
      document.getElementById('audit-rows').innerHTML = '';
      return;
    }
    document.getElementById('audit-empty').style.display = 'none';
    document.getElementById('audit-rows').innerHTML = trail.slice().reverse().map(r => {
      const ts = (r.timestamp||'').replace('T',' ').slice(0,19);
      const action = r.action || '';
      const aColor = action==='override' ? '#f59e0b' : action==='redline' ? '#38bdf8' : action==='rating' ? '#818cf8' : '#94a3b8';
      const detail = r.human_override
        ? `Human: <b>${r.human_override}</b>${r.override_note ? ' — '+r.override_note.slice(0,60) : ''}`
        : r.reason || (r.extra_json ? '('+action+')' : '');
      return `<div class="audit-row">
        <span class="audit-ts">${ts}</span>
        <span class="audit-badge" style="color:${aColor}">${action}</span>
        <span class="audit-badge">${r.clause_id||'—'}</span>
        <span class="audit-reason">${detail.toString().slice(0,100)}</span>
      </div>`;
    }).join('');
  } catch(e) { /* server may not be running */ }
}

function toggleAudit() {
  const toggle = document.getElementById('audit-toggle');
  const body   = document.getElementById('audit-body');
  const isOpen = body.classList.contains('open');
  toggle.classList.toggle('open', !isOpen);
  body.classList.toggle('open', !isOpen);
}

// ── Toast ─────────────────────────────────────────────────────────────────────
function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 3000);
}

// ── Start ─────────────────────────────────────────────────────────────────────
init();
