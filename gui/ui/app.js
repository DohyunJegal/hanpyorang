
let api = null;

window.addEventListener('pywebviewready', () => {
  api = window.pywebview.api;
  loadLayoutSelects();
});

async function call(method, ...args) {
  if (!api) { console.warn('pywebview가 없습니다.'); return null; }
  return await api[method](...args);
}

/* 탭 전환 */
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(`tab-${btn.dataset.tab}`).classList.add('active');
    if (btn.dataset.tab === 'layout') initLayoutTab();
    if (btn.dataset.tab === 'parties') initPartiesTab();
  });
});

/* 토스트 메세지 */
function toast(msg, type = 'info', ms = 3200) {
  const icons = { success: '✓', error: '✕', info: 'ℹ' };
  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  el.innerHTML = `<span>${icons[type]}</span><span>${msg}</span>`;
  document.getElementById('toastContainer').appendChild(el);
  setTimeout(() => el.remove(), ms);
}

/* 선택한 레이아웃 불러오기 */
async function loadLayoutSelects() {
  const names = await call('get_layout_names') || ['기본'];
  ['singleLayoutSel', 'batchLayoutSel'].forEach(id => {
    const sel = document.getElementById(id);
    const prev = sel.value;
    sel.innerHTML = '';
    names.forEach(n => {
      const opt = document.createElement('option');
      opt.value = opt.textContent = n;
      sel.appendChild(opt);
    });
    if (names.includes(prev)) sel.value = prev;
  });
}

/* ========== 단일 변환 탭 ========== */
let singlePath = null;
let candDragIdx = null;

function singleSelectFile() {
  call('open_file_dialog').then(p => { if (p) setSingleFile(p); });
}
function setSingleFile(path) {
  singlePath = path;
  document.getElementById('singleFileNameText').textContent = path.split(/[\\/]/).pop();
  document.getElementById('singleDropContent').hidden = true;
  document.getElementById('singleFileBadge').hidden = false;
  document.getElementById('singleFields').hidden = true;
  singleReadPdf();
}
function singleClearFile(e) {
  e.stopPropagation();
  singlePath = null;
  document.getElementById('singleDropContent').hidden = false;
  document.getElementById('singleFileBadge').hidden = true;
  document.getElementById('singleFields').hidden = true;
}

async function singleReadPdf() {
  if (!singlePath) return;
  const status = document.getElementById('singleReadStatus');
  status.textContent = '읽는 중...';
  const res = await call('extract_pdf', singlePath);
  if (!res?.ok) {
    status.textContent = '읽기 실패';
    toast(res?.error || '읽기 실패', 'error');
    return;
  }
  status.textContent = '완료';
  renderCands(res.data.candidates || []);
  document.getElementById('fTitle').value = res.data.title || '';
  document.getElementById('fDistrict').value = res.data.district || '';
  document.getElementById('singleFields').hidden = false;
}

/* 후보자 목록 */
function renderCands(cands) {
  const list = document.getElementById('candList');
  list.innerHTML = '';
  cands.forEach((c, i) => list.appendChild(makeCandRow(c.number, c.name, i)));
}
function makeCandRow(num, name, idx) {
  const row = document.createElement('div');
  row.className = 'cand-row'; row.draggable = true; row.dataset.idx = idx;
  row.innerHTML = `
    <span class="drag-handle">⠿</span>
    <input class="field-input" style="width:60px;" value="${esc(num)}" placeholder="번호">
    <input class="field-input flex-1" value="${esc(name)}" placeholder="이름">
    <button onclick="this.closest('.cand-row').remove()"
            class="text-slate-300 hover:text-red-500 text-xl leading-none px-1 border-none bg-transparent cursor-pointer">×</button>
  `;
  row.addEventListener('dragstart', e => { candDragIdx = idx; row.classList.add('dragging'); e.dataTransfer.effectAllowed='move'; });
  row.addEventListener('dragend', () => { row.classList.remove('dragging'); document.querySelectorAll('.cand-row').forEach(r=>r.classList.remove('drag-target')); });
  row.addEventListener('dragover', e => { e.preventDefault(); document.querySelectorAll('.cand-row').forEach(r=>r.classList.remove('drag-target')); row.classList.add('drag-target'); });
  row.addEventListener('drop', e => {
    e.preventDefault();
    const toIdx = parseInt(row.dataset.idx);
    if (candDragIdx === null || candDragIdx === toIdx) return;
    const cands = getCands();
    cands.splice(toIdx, 0, cands.splice(candDragIdx, 1)[0]);
    renderCands(cands);
  });
  return row;
}
function addCandidate() { renderCands([...getCands(), { number: '', name: '' }]); }
function getCands() {
  return [...document.querySelectorAll('#candList .cand-row')].map(r => ({
    number: r.querySelectorAll('input')[0].value,
    name:   r.querySelectorAll('input')[1].value,
  }));
}

/* 드롭존 */
const dz = document.getElementById('singleDropZone');
dz.addEventListener('click', e => {
  if (e.target.closest('button')) return;
  if (!singlePath) singleSelectFile();
});
dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('drag-over'); });
dz.addEventListener('dragleave', () => dz.classList.remove('drag-over'));
dz.addEventListener('drop', e => {
  e.preventDefault(); dz.classList.remove('drag-over');
  const f = e.dataTransfer.files[0];
  if (f?.name.endsWith('.pdf')) setSingleFile(f.path || f.name);
});


async function singleConvert() {
  const dir = 'output';
  const layoutName = document.getElementById('singleLayoutSel').value;
  const ballot = {
    title: document.getElementById('fTitle').value,
    district: document.getElementById('fDistrict').value,
    candidates: getCands(),
  };
  const btn = document.getElementById('btnConvert');
  btn.textContent = '변환 중...'; btn.disabled = true;
  const res = await call('convert_single', ballot, dir, layoutName);
  btn.textContent = '변환'; btn.disabled = false;
  if (res?.ok) toast(`저장 완료: ${res.path}`, 'success', 5000);
  else toast(res?.error || '변환 실패', 'error');
}

/* ========== 다중 변환 탭 ========== */
let batchFiles = [];

function batchAddFiles() {
  call('open_files_dialog').then(paths => {
    if (!paths) return;
    paths.forEach(p => { if (!batchFiles.includes(p)) batchFiles.push(p); });
    renderBatch();
  });
}
function batchClear() { batchFiles = []; renderBatch(); }
function renderBatch(statuses = {}) {
  const list = document.getElementById('batchFileList');
  const empty = document.getElementById('batchEmpty');
  // 파일 항목 제거
  [...list.children].forEach(c => { if (c !== empty) c.remove(); });
  if (!batchFiles.length) { empty.hidden = false; return; }
  empty.hidden = true;
  batchFiles.forEach((p, i) => {
    const name = p.split(/[\\/]/).pop();
    const s = statuses[p] || { state: 'pending', msg: '' };
    const el = document.createElement('div');
    el.className = 'file-item';
    el.innerHTML = `
      <span class="dot dot-${s.state}"></span>
      <span class="flex-1 text-sm truncate" title="${esc(p)}">📄 ${esc(name)}</span>
      <span class="text-xs text-slate-400">${esc(s.msg)}</span>
      <button onclick="batchFiles.splice(${i},1);renderBatch();"
              class="ghost-btn" style="padding:3px 8px;font-size:12px;">×</button>
    `;
    list.appendChild(el);
  });
}

async function batchConvert() {
  const dir = 'output';
  if (!batchFiles.length) { toast('파일을 추가하세요.', 'error'); return; }
  const layoutName = document.getElementById('batchLayoutSel').value;
  const statuses = {};
  batchFiles.forEach(p => { statuses[p] = { state: 'loading', msg: '변환 중...' }; });
  renderBatch(statuses);
  const btn = document.getElementById('btnBatchConvert');
  btn.disabled = true;
  const results = await call('convert_batch', batchFiles, dir, layoutName);
  btn.disabled = false;
  if (!results) { toast('변환 실패', 'error'); return; }
  results.forEach((r, i) => {
    statuses[batchFiles[i]] = r.ok
      ? { state: 'success', msg: '완료' }
      : { state: 'error',   msg: r.error || '실패' };
  });
  renderBatch(statuses);
  const ok = results.filter(r => r.ok).length;
  toast(`${ok}/${results.length}개 변환 완료`, ok === results.length ? 'success' : 'info', 4000);
}

/* ========== 번역/역번역 탭  ========== */
let transTimer = null;
function onTransLeft()  { clearTimeout(transTimer); transTimer = setTimeout(doForward,  450); }
function onTransRight() { clearTimeout(transTimer); transTimer = setTimeout(doBackward, 450); }

async function doForward() {
  const text = document.getElementById('transLeft').value;
  if (!text.trim()) { document.getElementById('transRight').value = ''; return; }
  const res = await call('translate_to_braille', text);
  if (res?.ok) document.getElementById('transRight').value = res.result;
  else toast(res?.error || '변환 실패', 'error');
}
async function doBackward() {
  const text = document.getElementById('transRight').value;
  if (!text.trim()) { document.getElementById('transLeft').value = ''; return; }
  const res = await call('translate_from_braille', text);
  if (res?.ok) document.getElementById('transLeft').value = res.result;
  else toast(res?.error || '역변환 실패', 'error');
}
function clearLeft()  { document.getElementById('transLeft').value  = ''; document.getElementById('transRight').value = ''; }
function clearRight() { document.getElementById('transRight').value = ''; document.getElementById('transLeft').value  = ''; }

/* ========== 레이아웃 탭 ========== */
let allLayouts = {};
let curLayout  = '';
let rowDragIdx = null;

// 토큰 → 표시 정보
const TOKEN_INFO = {
  '선거명':  { label: '선거명',  barClass: 'bar-head',  barText: '[ 선거명 ]',   left: '52.2%', width: '47.8%' },
  '선거구':  { label: '선거구',  barClass: 'bar-head',  barText: '[ 선거구 ]',   left: '52.2%', width: '47.8%' },
  '하단멘트':{ label: '하단멘트',barClass: 'bar-head',  barText: '[ 하단멘트 ]', left: '52.2%', width: '47.8%' },
  '공백':    { label: '공백',    barClass: 'bar-empty', barText: '',             left: '0',     width: '100%' },
};
function candInfo(n) {
  return { label: `후보자${n}`, barClass: 'bar-cand', barText: `[ 후보자${n} ]`, left: '52.2%', width: '39.1%' };
}
function getTokenInfo(token) {
  if (TOKEN_INFO[token]) return TOKEN_INFO[token];
  if (token.startsWith('후보자')) return candInfo(token.slice(3));
  return { label: token, barClass: 'bar-empty', barText: token, left: '0', width: '100%' };
}

async function initLayoutTab() {
  const allNames = await call('get_layout_names') || ['기본'];
  allLayouts = {};
  for (const n of allNames) {
    const layout = await call('get_layout', n);
    allLayouts[n] = layout?.rows || [];
  }
  const editableNames = allNames.filter(n => n !== '기본');
  const dl = document.getElementById('layoutNameList');
  dl.innerHTML = '';
  editableNames.forEach(n => {
    const opt = document.createElement('option');
    opt.value = n;
    dl.appendChild(opt);
  });
  curLayout = editableNames[0] || null;
  const input = document.getElementById('layoutNameInput');
  input.value = curLayout || '';
  updateLayoutButtons();
  renderLayoutRows();
}

function onLayoutInputChange() {
  const val = document.getElementById('layoutNameInput').value.trim();
  const prev = curLayout;
  curLayout = (val && val !== '기본') ? val : null;
  if (curLayout !== prev) renderLayoutRows();
  updateLayoutButtons();
}

function updateLayoutButtons() {
  const name = document.getElementById('layoutNameInput')?.value.trim();
  const validName = !!(name && name !== '기본');
  const isExisting = validName && allLayouts.hasOwnProperty(name);
  document.getElementById('btnSaveLayout').disabled = !validName;
  document.getElementById('btnDeleteLayout').disabled = !isExisting;
}

function renderLayoutRows() {
  const rows = allLayouts[curLayout] || [];
  const container = document.getElementById('layoutRows');
  container.innerHTML = '';
  rows.forEach((token, i) => container.appendChild(makeLayoutRow(token, i)));
  updatePreview(rows);
}

function makeLayoutRow(token, idx) {
  const info = getTokenInfo(token);
  const row = document.createElement('div');
  row.className = 'layout-row'; row.draggable = true; row.dataset.idx = idx;
  row.innerHTML = `
    <span class="drag-handle text-slate-300 text-sm cursor-grab">⠿</span>
    <span class="layout-row-label">${info.label}</span>
    <div class="layout-row-visual">
      <div class="layout-row-bar ${info.barClass}" style="left:${info.left};width:${info.width};">${info.barText}</div>
    </div>
    <button onclick="removeLayoutRow(${idx})"
            class="text-slate-300 hover:text-red-500 text-lg leading-none px-1 border-none bg-transparent cursor-pointer flex-shrink-0">×</button>
  `;
  row.addEventListener('dragstart', e => { rowDragIdx = idx; row.classList.add('dragging'); e.dataTransfer.effectAllowed='move'; });
  row.addEventListener('dragend', () => { row.classList.remove('dragging'); document.querySelectorAll('.layout-row').forEach(r=>r.classList.remove('drag-target')); });
  row.addEventListener('dragover', e => { e.preventDefault(); document.querySelectorAll('.layout-row').forEach(r=>r.classList.remove('drag-target')); row.classList.add('drag-target'); });
  row.addEventListener('drop', e => {
    e.preventDefault();
    const toIdx = parseInt(row.dataset.idx);
    if (rowDragIdx === null || rowDragIdx === toIdx) return;
    const rows = [...(allLayouts[curLayout] || [])];
    rows.splice(toIdx, 0, rows.splice(rowDragIdx, 1)[0]);
    allLayouts[curLayout] = rows;
    renderLayoutRows();
  });
  return row;
}

function removeLayoutRow(idx) {
  const rows = [...(allLayouts[curLayout] || [])];
  rows.splice(idx, 1);
  allLayouts[curLayout] = rows;
  renderLayoutRows();
}

function paletteAdd(type) {
  const rows = [...(allLayouts[curLayout] || [])];
  if (type === '후보자') {
    const used = rows.filter(t => t.startsWith('후보자'))
                     .map(t => parseInt(t.slice(3)) || 0);
    const next = (used.length ? Math.max(...used) : 0) + 1;
    rows.push(`후보자${next}`);
  } else if (type === '하단멘트') {
    if (!rows.includes('하단멘트')) rows.push('하단멘트');
    else { toast('하단멘트는 하나만 사용합니다.', 'info'); return; }
  } else if (type === '선거명' || type === '선거구') {
    if (!rows.includes(type)) rows.push(type);
    else { toast(`${type}은(는) 이미 있습니다.`, 'info'); return; }
  } else {
    rows.push(type); // 공백
  }
  allLayouts[curLayout] = rows;
  renderLayoutRows();
}


async function deleteLayout() {
  if (!curLayout) return;
  const editableCount = Object.keys(allLayouts).filter(n => n !== '기본').length;
  if (editableCount <= 1) { toast('레이아웃은 최소 1개 필요합니다.', 'error'); return; }
  if (!confirm(`'${curLayout}' 레이아웃을 삭제할까요?`)) return;
  const res = await call('delete_layout', curLayout);
  if (!res?.ok) { toast(res?.error || '삭제 실패', 'error'); return; }
  delete allLayouts[curLayout];
  await initLayoutTab();
  await loadLayoutSelects();
  toast('삭제했습니다.', 'success');
}

async function saveLayout() {
  const name = document.getElementById('layoutNameInput').value.trim();
  if (!name || name === '기본') return;
  const wasNew = !(name in allLayouts) || !await call('get_layout', name);
  const rows = allLayouts[name] || [];
  const res = await call('save_layout', name, rows);
  if (!res?.ok) { toast(res?.error || '저장 실패', 'error'); return; }
  allLayouts[name] = rows;
  curLayout = name;
  // datalist 갱신
  const dl = document.getElementById('layoutNameList');
  if (![...dl.options].some(o => o.value === name)) {
    const opt = document.createElement('option');
    opt.value = name;
    dl.appendChild(opt);
  }
  updateLayoutButtons();
  await loadLayoutSelects();
  toast(wasNew ? '새 레이아웃을 저장했습니다.' : '저장했습니다.', 'success');
}

function updatePreview(rows) {
  const MARGIN = 24, HEAD_W = 22, CAND_W = 18, LINE_W = 46;
  const center = t => {
    if (t.length > HEAD_W) t = t.slice(0, HEAD_W);
    const p = Math.floor((HEAD_W - t.length) / 2);
    return (' '.repeat(MARGIN) + ' '.repeat(p) + t).padEnd(LINE_W);
  };
  const right = t => {
    if (t.length > CAND_W) t = t.slice(0, CAND_W);
    return (' '.repeat(MARGIN) + ' '.repeat(CAND_W - t.length) + t).padEnd(LINE_W);
  };
  const ruler = '1234567890'.repeat(5).slice(0, LINE_W);
  const lines = rows.map(token => {
    if (token === '공백')    return '';
    if (token === '선거명')  return center('[선거명]');
    if (token === '선거구')  return center('[선거구]');
    if (token === '하단멘트') return center('[하단멘트]');
    if (token.startsWith('후보자')) return right(`[${token}]`);
    return '';
  });
  document.getElementById('layoutPreview').textContent =
    `눈금: ${ruler}\n` + lines.map((l, i) => `${String(i+1).padStart(2)}: ${l}|`).join('\n');
}

/* ========== 정당 이름 탭 ========== */
async function initPartiesTab() {
  const data = await call('get_party_names') || {};
  renderParties(data);
}
function renderParties(data) {
  const list = document.getElementById('partyList');
  list.innerHTML = '';
  const entries = Object.entries(data);
  if (!entries.length) entries.push(['', '']);
  entries.forEach(([f, a]) => list.appendChild(makePartyRow(f, a)));
}
function makePartyRow(full = '', abbr = '') {
  const row = document.createElement('div');
  row.className = 'grid grid-cols-[1fr_24px_1fr_36px] gap-2 items-center';
  row.innerHTML = `
    <input class="field-input" placeholder="더불어민주당" value="${esc(full)}">
    <span class="text-center text-slate-400">→</span>
    <input class="field-input" placeholder="민주당" value="${esc(abbr)}">
    <button onclick="this.closest('.grid').remove()" class="ghost-btn" style="padding:5px 8px;">×</button>
  `;
  return row;
}
function addPartyRow() { document.getElementById('partyList').appendChild(makePartyRow()); }
async function saveParties() {
  const data = {};
  document.querySelectorAll('#partyList .grid').forEach(row => {
    const [f, a] = [...row.querySelectorAll('input')].map(i => i.value.trim());
    if (f && a) data[f] = a;
  });
  const res = await call('save_party_names', data);
  if (res?.ok) toast('저장했습니다.', 'success');
  else toast(res?.error || '저장 실패', 'error');
}

/* 유틸 */
function esc(s) {
  return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
