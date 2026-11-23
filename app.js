"use strict";
/* ================= 定数 ================= */
const AVPU = ['A 清明（普段どおり）', 'C 新たな混乱・普段と違う', 'V 呼びかけに反応', 'P 痛みに反応', 'U 反応なし'];
const ADM = ['任意入院', '医療保護入院', '措置入院', '応急入院', 'その他'];
const CPR = ['心肺蘇生を希望（フルコード）', 'DNAR（心肺蘇生をしない）', '未確認'];
const WISH = ['搬送を含め積極的な治療を希望', '院内でできる範囲の治療を希望', '苦痛の緩和を中心に', '未確認'];
const DDX_ST = ['可能性高い', '保留', '否定的'];
const DECISIONS = ['救急搬送（119番）', '救急病院へ直接連絡して搬送', '当日中の転院・受診を相談', '院内で治療を継続（再評価）', '院内で緩和ケア・看取り'];
const STEP_T = [['背景', '患者の背景・普段の状態・本人と家族の意向'], ['バイタル', 'バイタルを記録するとNEWS2を自動計算'], ['症候', '症候ごとのレッドフラッグと搬送基準'], ['検査', 'この時間帯にできる検査と結果'], ['鑑別', '高齢者・認知症・向精神薬を踏まえた鑑別'], ['初期対応', '院内でできる初期対応'], ['判断', '搬送か院内継続か'], ['記録', '判断と連絡の記録']];
const LABS = [
 ['wbc', '白血球（/μL）', v => v < 3000 ? ['warn', '白血球減少'] : v >= 20000 ? ['crit', '著明な白血球増加'] : v > 12000 ? ['warn', '白血球増加'] : null],
 ['neu', '好中球（/μL）', v => v < 500 ? ['crit', '高度の好中球減少（クロザピンは直ちに中止）'] : v < 1500 ? ['warn', '好中球減少（クロザピンは中止基準）'] : null],
 ['hb', 'Hb（g/dL）', v => v < 7 ? ['crit', '高度の貧血'] : v < 8 ? ['warn', '貧血'] : null],
 ['plt', '血小板（万/μL）', v => v < 2 ? ['crit', '高度の血小板減少'] : v < 5 ? ['warn', '血小板減少'] : null],
 ['crp', 'CRP（mg/dL）', v => v >= 10 ? ['warn', '炎症反応の高値'] : null],
 ['na', 'Na（mEq/L）', v => v < 120 ? ['crit', '高度の低Na'] : v < 130 ? ['warn', '低Na'] : v >= 160 ? ['crit', '高度の高Na'] : v > 150 ? ['warn', '高Na'] : null],
 ['k', 'K（mEq/L）', v => v >= 6 ? ['crit', '高K（心電図を確認）'] : v > 5.5 ? ['warn', '高K'] : v < 2.5 ? ['crit', '高度の低K'] : v < 3 ? ['warn', '低K（QT延長に注意）'] : null],
 ['bun', 'BUN（mg/dL）', v => v >= 40 ? ['warn', 'BUN高値（脱水・出血・腎障害）'] : null],
 ['cr', 'Cr（mg/dL）', v => v >= 2 ? ['warn', '腎機能低下（普段の値と比較）'] : null],
 ['ck', 'CK（U/L）', v => v >= 5000 ? ['crit', 'CK著明高値（横紋筋融解・悪性症候群）'] : v >= 1000 ? ['warn', 'CK高値'] : null],
 ['ast', 'AST（U/L）', v => v >= 200 ? ['warn', '肝機能障害'] : null],
 ['tbil', '総ビリルビン（mg/dL）', v => v >= 3 ? ['warn', '黄疸（胆道感染・閉塞を考える）'] : null],
 ['nh3', 'アンモニア（μg/dL）', v => v >= 100 ? ['warn', '高アンモニア血症（バルプロ酸・肝硬変）'] : null],
 ['li', 'リチウム（mEq/L）', v => v >= 1.5 ? ['crit', 'リチウム中毒域'] : v > 1.2 ? ['warn', 'リチウム高値'] : null],
 ['lac', '乳酸（mmol/L）', v => v >= 4 ? ['crit', '乳酸著明高値（ショック・腸管虚血）'] : v > 2 ? ['warn', '乳酸高値'] : null]
];
const QUAL = [['trop', 'トロポニン', ['陰性', '陽性']], ['dd', 'D-ダイマー', ['基準値内', '高値']]];
const ECG_F = ['洞調律・著変なし', 'ST上昇', 'ST低下・陰性T', '新たな左脚ブロック', '心房細動', '房室ブロック', '洞性頻脈', '洞性徐脈', 'QRS延長', '心室性期外収縮の多発'];

/* ================= 状態 ================= */
const LS = 'psyacute.v1';
let DB = {eps: {}, cur: null, step: 0, mode: 'auto', avail: {day: {s: 1, b: 1, e: 1, x: 1, c: 1}, night: {s: 1}}};
try { const r = localStorage.getItem(LS); if (r) DB = Object.assign(DB, JSON.parse(r)); } catch (e) {}
let E = null, step = DB.step || 0, delArm = null;
const save = () => { if (E) { E.updated = new Date().toISOString(); DB.eps[E.id] = E; DB.cur = E.id; } DB.step = step; try { localStorage.setItem(LS, JSON.stringify(DB)); } catch (e) {} };
function blank(id) { return {id, p: {}, vit: [], sym: [], chk: {}, ddx: {}, tests: {}, labs: {}, ecg: {f: []}, needs: [], dec: {}}; }
function nowLocal() { const d = new Date(), p = n => String(n).padStart(2, '0'); return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()) + 'T' + p(d.getHours()) + ':' + p(d.getMinutes()); }
function newId() { return '急変-' + nowLocal().replace(/[-:]/g, '').replace('T', '-').slice(2); }
function sample() {
 const e = blank('サンプル（架空）'); e.sample = true;
 Object.assign(e.p, {age: '82', sex: '女性', ward: '認知症治療病棟', adm: '医療保護入院', dx: 'アルツハイマー型認知症（BPSD）', st: ['認知症', '嚥下障害・とろみ食', '糖尿病'], meds: ['抗精神病薬', 'インスリン・SU薬'], medsText: 'クエチアピン 25mg 夕、グリメピリド 1mg 朝、酸化マグネシウム 330mg 3錠分3', base: '車椅子で全介助。会話は単語程度、表情で意思表示。食事はとろみで半量程度', cpr: 'DNAR（心肺蘇生をしない）', wish: '院内でできる範囲の治療を希望', kp: '長女（日中の連絡先あり）', psy: '夜間に大声。拘束なし。点滴は自己抜去の恐れあり'});
 e.vit = [{t: '2026-11-23T21:10', rr: '22', spo2: '93', o2: '空気', hr: '104', sbp: '128', dbp: '70', temp: '38.4', avpu: AVPU[0], glu: '142'}];
 e.sym = ['fever']; e.chk = {'fever:ask': ['咳・痰の増加、むせ'], 'fever:stay': ['血圧・意識が保たれている']};
 return e;
}
function load(e) { E = e; ['vit', 'sym', 'needs'].forEach(k => { if (!Array.isArray(E[k])) E[k] = []; }); ['p', 'chk', 'ddx', 'tests', 'labs', 'dec'].forEach(k => { E[k] = E[k] || {}; }); E.ecg = E.ecg || {f: []}; }

/* ================= ユーティリティ ================= */
const $ = s => document.querySelector(s);
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
const arr = v => Array.isArray(v) ? v : [];
const num = v => (v === '' || v == null || isNaN(+v)) ? null : +v;
const SYM = Object.fromEntries(SYMS.map(s => [s.k, s]));
const fmtT = t => t ? t.replace('T', ' ').slice(5).replace('-', '/') : '';

/* 日中か夜間か */
function isNight() { if (DB.mode === 'day') return false; if (DB.mode === 'night') return true; const h = new Date().getHours(); return h < 9 || h >= 17; }
const avail = k => !!(isNight() ? DB.avail.night : DB.avail.day)[k];

/* ================= NEWS2 ================= */
function news2(v) {
 const sc = {}, rr = num(v.rr), sp = num(v.spo2), sbp = num(v.sbp), hr = num(v.hr), t = num(v.temp), o2 = v.o2 === '酸素';
 if (rr != null) sc.rr = rr <= 8 ? 3 : rr <= 11 ? 1 : rr <= 20 ? 0 : rr <= 24 ? 2 : 3;
 if (sp != null) {
  if (!v.scale2) sc.spo2 = sp <= 91 ? 3 : sp <= 93 ? 2 : sp <= 95 ? 1 : 0;
  else sc.spo2 = sp <= 83 ? 3 : sp <= 85 ? 2 : sp <= 87 ? 1 : (sp <= 92 || !o2) ? 0 : sp <= 94 ? 1 : sp <= 96 ? 2 : 3;
 }
 if (v.o2) sc.o2 = o2 ? 2 : 0;
 if (sbp != null) sc.sbp = sbp <= 90 ? 3 : sbp <= 100 ? 2 : sbp <= 110 ? 1 : sbp <= 219 ? 0 : 3;
 if (hr != null) sc.hr = hr <= 40 ? 3 : hr <= 50 ? 1 : hr <= 90 ? 0 : hr <= 110 ? 1 : hr <= 130 ? 2 : 3;
 if (v.avpu) sc.avpu = v.avpu[0] === 'A' ? 0 : 3;
 if (t != null) sc.temp = t <= 35 ? 3 : t <= 36 ? 1 : t <= 38 ? 0 : t <= 39 ? 1 : 2;
 const keys = ['rr', 'spo2', 'o2', 'sbp', 'hr', 'avpu', 'temp'], have = keys.filter(k => sc[k] != null);
 const total = have.reduce((a, k) => a + sc[k], 0), red3 = have.some(k => sc[k] === 3), complete = have.length === 7;
 const lv = total >= 7 ? 3 : total >= 5 ? 2 : red3 ? 2 : total >= 1 ? 1 : 0;
 const resp = total >= 7 ? '緊急対応：持続モニタリング、医師がすぐに診察、搬送（高次医療）を検討' :
  total >= 5 ? '至急対応：1時間ごとに観察、医師がすぐに診察、搬送を検討' :
  red3 ? '1項目が3点：1時間ごとに観察し、医師に報告' :
  total >= 1 ? '4〜6時間ごとに観察。看護師が評価し、悪化すれば医師に報告' : '12時間ごとの観察';
 const qs = (rr != null && rr >= 22 ? 1 : 0) + (v.avpu && v.avpu[0] !== 'A' ? 1 : 0) + (sbp != null && sbp <= 100 ? 1 : 0);
 return {sc, total, red3, complete, lv, resp, qsofa: qs, n: have.length};
}
const lastV = () => E.vit[E.vit.length - 1];

/* ================= 判定（搬送か院内か） ================= */
function chk(key) { return arr(E.chk[key]); }
function labFlags() {
 const out = [];
 LABS.forEach(([k, l, f]) => { const v = num(E.labs[k]); if (v != null) { const r = f(v); if (r) out.push([r[0], l.split('（')[0] + ' ' + v + '：' + r[1]]); } });
 const lv = lastV(), g = lv ? num(lv.glu) : null;
 if (g != null) { if (g < 70) out.push(['crit', '血糖 ' + g + '：低血糖']); else if (g >= 500) out.push(['crit', '血糖 ' + g + '：著明な高血糖']); else if (g > 300) out.push(['warn', '血糖 ' + g + '：高血糖']); }
 if (E.labs.trop === '陽性') out.push(['crit', 'トロポニン陽性']);
 if (E.labs.dd === '高値') out.push(['warn', 'D-ダイマー高値（肺塞栓・深部静脈血栓症を考える）']);
 const q = num(E.ecg.qtc); if (q != null) { if (q >= 500) out.push(['crit', 'QTc ' + q + 'ms：著明な延長']); else if (q >= 470) out.push(['warn', 'QTc ' + q + 'ms：延長']); }
 arr(E.ecg.f).forEach(f => { if (/ST上昇|左脚/.test(f)) out.push(['crit', '心電図：' + f]); else if (/ST低下|房室|QRS/.test(f)) out.push(['warn', '心電図：' + f]); });
 if (E.labs.bun && E.labs.cr && num(E.labs.cr) > 0 && num(E.labs.bun) / num(E.labs.cr) > 25) out.push(['info', 'BUN/Cr比 ' + Math.round(num(E.labs.bun) / num(E.labs.cr)) + '：脱水・上部消化管出血を考える']);
 return out;
}
function decide() {
 const R = {lv: 0, why: [], notes: []}, v = lastV(), N = v ? news2(v) : null, night = isNight();
 const up = (lv, t) => { R.lv = Math.max(R.lv, lv); R.why.push([lv, t]); };
 if (N) {
  if (N.total >= 7) up(3, 'NEWS2 ' + N.total + '点（7点以上）');
  else if (N.total >= 5) up(2, 'NEWS2 ' + N.total + '点（5〜6点）');
  else if (N.red3) up(2, 'NEWS2で1項目が3点');
  else up(1, 'NEWS2 ' + N.total + '点');
  if (N.qsofa >= 2) up(2, 'qSOFA ' + N.qsofa + '点（敗血症を疑う）');
  if (num(v.spo2) != null && num(v.spo2) < 90 && v.o2 === '酸素') up(3, '酸素投与下でSpO2 ' + v.spo2 + '%');
  if (num(v.sbp) != null && num(v.sbp) < 90) up(3, '収縮期血圧 ' + v.sbp);
  if (v.avpu && /^[PU]/.test(v.avpu)) up(3, '意識：' + v.avpu);
 }
 E.sym.forEach(k => {
  const s = SYM[k];
  chk(k + ':red').forEach(t => up(3, s.n + '：' + t));
  chk(k + ':consult').forEach(t => up(2, s.n + '：' + t));
  if (night) chk(k + ':night').forEach(t => up(2, s.n + '（夜間・検査できず）：' + t));
 });
 labFlags().forEach(([l, t]) => { if (l === 'crit') up(2, t); });
 E.needs.forEach(t => up(2, '院内で困難な処置が必要：' + t));
 /* 院内継続の条件 */
 E.sym.forEach(k => { const s = SYM[k], c = chk(k + ':stay'); if (c.length && c.length === s.stay.length && R.lv <= 1) R.notes.push(['ok', s.n + '：院内継続の条件をすべて満たしています']); });
 /* 意向 */
 const p = E.p;
 if (p.wish === '苦痛の緩和を中心に' && R.lv >= 2) R.notes.push(['info', '本人・家族の意向は「苦痛の緩和を中心に」。搬送より院内での症状緩和を軸に考えます。ただし骨折・窒息など、搬送したほうが苦痛を和らげられる場合は家族と相談してください。']);
 if (p.wish === '院内でできる範囲の治療を希望' && R.lv >= 2) R.notes.push(['info', '意向は「院内でできる範囲」。搬送が必要と判断した場合は、理由（院内では治療できないこと）を家族に説明して改めて意向を確認します。']);
 if ((!p.wish || p.wish === '未確認') && R.lv >= 2) R.notes.push(['warn', '本人・家族の意向が未確認です。キーパーソンに連絡して確認してください。待てない状況では救命を優先します。']);
 if (p.cpr === 'DNAR（心肺蘇生をしない）') R.notes.push(['info', 'DNARは「心肺蘇生をしない」意思で、搬送や治療をしないという意味ではありません。']);
 if (night && R.lv >= 1) { const na = ['b', 'e', 'x', 'c'].filter(k => !avail(k)).map(k => TEST_KINDS[k]); if (na.length) R.notes.push(['night', '夜間はこの検査ができない設定です：' + na.join('、') + '（施設の設定で変更できます）。症候ごとの「夜間の判断」を確認してください。']); }
 R.N = N;
 R.recheck = R.lv >= 3 ? '持続観察' : N ? (N.total >= 5 || N.red3 ? '1時間ごと' : N.total >= 1 ? '4〜6時間ごと（悪化時はすぐ）' : '12時間ごと') : '';
 return R;
}
const LVTXT = {3: 'すぐに搬送を検討（救急要請・救急病院へ連絡）', 2: '搬送・転院を相談（医師が診察して判断）', 1: '院内で治療を続けて再評価', 0: 'バイタルと症候を入力すると判定します'};

/* ================= 描画：部品 ================= */
function seg(key, opts, cur, cls) { return `<div class="opts">${opts.map(o => `<button type="button" class="opt ${cls || ''}" data-set="${esc(key)}" data-v="${esc(o)}" aria-pressed="${cur === o}">${esc(o)}</button>`).join('')}</div>`; }
function chips(key, opts, cur, cls) { return `<div class="opts">${opts.map(o => `<button type="button" class="opt chip ${cls || ''}" data-tog="${esc(key)}" data-v="${esc(o)}" aria-pressed="${arr(cur).includes(o)}">${esc(o)}</button>`).join('')}</div>`; }
function fld(path, label, type, extra) { const v = getP(path); const id = 'f_' + path.replace(/\W/g, '_');
 const ctl = type === 'ta' ? `<textarea id="${id}" data-in="${path}" rows="${extra || 2}">${esc(v)}</textarea>` : `<input id="${id}" data-in="${path}" type="${type}" ${type === 'number' ? 'inputmode="decimal" step="any"' : ''} value="${esc(v)}">`;
 return `<div class="fld${type === 'ta' ? ' wide' : ''}"><label class="lab" for="${id}">${esc(label)}</label>${ctl}</div>`; }
function getP(path) { const [a, b] = path.split('.'); return b === undefined ? E[a] : (E[a] || {})[b]; }
function setP(path, v) { const [a, b] = path.split('.'); if (b === undefined) E[a] = v; else { E[a] = E[a] || {}; E[a][b] = v; } }
const block = (h, body, right) => `<section class="block"><h3><span>${h}</span>${right || ''}</h3>${body}</section>`;
const W = s => `<div class="wide">${s}</div>`;

/* ================= 描画：ステップ ================= */
function stepBackground() {
 const p = E.p;
 return block('患者', fld('p.age', '年齢', 'number') + W(`<div class="lab">性別</div>${seg('p.sex', ['男性', '女性'], p.sex)}`) + fld('p.ward', '病棟・部屋', 'text') +
  W(`<div class="lab">入院形態</div>${seg('p.adm', ADM, p.adm)}`) + fld('p.dx', '精神科診断', 'text'))
 + block('既往・状態（該当をタップ）', W(chips('p.st', STATES, p.st)) + fld('p.phx', 'その他の既往・身体疾患', 'ta'))
 + block('服薬（ハイリスクの薬をタップ）', W(chips('p.meds', MEDS.map(m => m.n), p.meds)) + fld('p.medsText', '内服薬の詳細（転院時の情報提供に使用）', 'ta', 3) + fld('p.allergy', 'アレルギー', 'text'))
 + block('普段の状態（急変時の比較に）', fld('p.base', 'ADL・意識・会話・食事・普段の血圧など', 'ta', 3) + fld('p.psy', '精神症状の現状・行動上の注意（拘束・隔離、興奮時の対応、自己抜去の恐れ）', 'ta', 2))
 + block('本人・家族の意向（ACP）', W(`<div class="lab">心肺蘇生</div>${seg('p.cpr', CPR, p.cpr)}`) + W(`<div class="lab">急変時の治療・搬送</div>${seg('p.wish', WISH, p.wish)}`) + fld('p.kp', 'キーパーソン・連絡先・連絡のつく時間', 'text'));
}
function stepVitals() {
 const v = E.vit, last = lastV();
 let h = '';
 h += block('バイタルの記録', W(`<div class="rowbtns"><button type="button" class="lnk" data-act="addVit">＋ 今の時刻で記録を追加</button></div>`) + (v.length ? '' : W('<p class="note">記録を追加すると入力欄が出ます。</p>')));
 if (last) {
  const i = v.length - 1, P = 'vit' + i;
  h += block('最新の記録（' + (i + 1) + '回目）', `<div class="wide vrow">
   ${vfld(i, 't', '時刻', 'datetime-local')}${vfld(i, 'rr', '呼吸数（/分）')}${vfld(i, 'spo2', 'SpO2（%）')}${vfld(i, 'o2l', '酸素（L/分）')}
   ${vfld(i, 'sbp', '収縮期血圧')}${vfld(i, 'dbp', '拡張期血圧')}${vfld(i, 'hr', '心拍数（/分）')}${vfld(i, 'temp', '体温（℃）')}
   ${vfld(i, 'glu', '血糖（mg/dL）')}</div>
   ${W(`<div class="lab">酸素</div>${segV(i, 'o2', ['空気', '酸素'])}`)}
   ${W(`<div class="lab">意識（ACVPU）</div>${segV(i, 'avpu', AVPU)}<p class="note">認知症の方は「普段の状態」と比べ、新たな混乱・普段と違う反応があれば C にします。</p>`)}
   ${W(`<div class="opts"><button type="button" class="opt chip" data-vtog="${i}:scale2" aria-pressed="${!!last.scale2}">高二酸化炭素血症のリスクあり（COPDなど：目標SpO2 88〜92%、NEWS2のスケール2）</button></div>`)}
   ${W(`<button type="button" class="del" data-act="delVit" data-i="${i}">この記録を削除</button>`)}`);
 }
 h += `<section class="block" id="calc-news"></section>`;
 return h;
}
function vfld(i, k, l, type) { const id = `v${i}_${k}`; return `<div class="fld"><label class="lab" for="${id}">${l}</label><input id="${id}" data-vin="${i}:${k}" type="${type || 'number'}" ${type ? '' : 'inputmode="decimal" step="any"'} value="${esc(E.vit[i][k])}"></div>`; }
function segV(i, k, opts) { return `<div class="opts">${opts.map(o => `<button type="button" class="opt" data-vset="${i}:${k}" data-v="${esc(o)}" aria-pressed="${E.vit[i][k] === o}">${esc(o)}</button>`).join('')}</div>`; }
function newsHTML() {
 const v = E.vit; if (!v.length) return `<h3><span>NEWS2</span></h3><p class="note wide">バイタルを記録すると自動で計算します。</p>`;
 const N = news2(lastV()), cls = N.lv >= 3 ? 'a-crit' : N.lv === 2 ? 'a-warn' : N.lv === 1 ? 'a-info' : 'a-ok';
 let h = `<h3><span>NEWS2（最新）</span></h3><div class="wide kv"><div><div class="note">合計</div><div class="big">${N.total}</div></div><div><div class="note">qSOFA</div><div class="big">${N.qsofa}</div></div>${N.complete ? '' : '<span class="pill p-warn">未入力の項目あり（' + N.n + '/7）</span>'}</div>
  <div class="wide alert ${cls}">${esc(N.resp)}</div>`;
 const cols = [['rr', '呼吸'], ['spo2', 'SpO2'], ['o2', '酸素'], ['sbp', '血圧'], ['hr', '心拍'], ['avpu', '意識'], ['temp', '体温']];
 h += `<div class="wide scroll"><table class="vt"><thead><tr><th>時刻</th>${cols.map(c => `<th>${c[1]}</th>`).join('')}<th>血糖</th><th>NEWS2</th></tr></thead><tbody>` +
  v.map(x => { const n = news2(x); return `<tr><td>${esc(fmtT(x.t))}</td>${cols.map(([k]) => { const s = n.sc[k]; const val = k === 'o2' ? (x.o2 === '酸素' ? (x.o2l ? x.o2l + 'L' : '酸素') : x.o2 ? '空気' : '') : k === 'avpu' ? (x.avpu ? x.avpu[0] : '') : k === 'sbp' ? (x.sbp ? x.sbp + (x.dbp ? '/' + x.dbp : '') : '') : (x[k] || ''); return `<td class="${s ? 's' + s : ''}">${esc(val)}</td>`; }).join('')}<td>${esc(x.glu || '')}</td><td><b>${n.total}</b></td></tr>`; }).join('') + '</tbody></table></div>';
 h += `<p class="note wide">色：黄＝1点、橙＝2点、赤＝3点。NEWS2は急変の早期発見のための点数で、判断は必ず診察と合わせて行います。</p>`;
 return h;
}
function stepSymptoms() {
 let h = block('症候を選ぶ（複数可）', W(chips('sym', SYMS.map(s => s.n), E.sym.map(k => SYM[k].n))));
 if (!E.sym.length) return h + `<p class="note">症候を選ぶと、確認事項・レッドフラッグ・搬送の基準が表示されます。</p>`;
 const night = isNight(), meds = arr(E.p.meds);
 E.sym.forEach(k => {
  const s = SYM[k], mw = MEDS.filter(m => meds.includes(m.n) && m.w[k]).map(m => m.n + '：' + m.w[k]);
  h += `<div class="sym"><div class="t"><span>${esc(s.n)}</span><span class="pill ${lvPill(symLv(k))}">${symLvTxt(k)}</span></div>
  ${mw.length ? `<div class="alert a-warn"><b>服薬に関連した注意</b><br>${mw.map(esc).join('<br>')}</div>` : ''}
  ${grp('確認すること', k + ':ask', s.ask, '')}
  ${grp('レッドフラッグ（1つでも → すぐ搬送を検討）', k + ':red', s.red, 'red', 'r')}
  ${grp('搬送・転院を相談', k + ':consult', s.consult, 'amb', 'y')}
  ${night ? `<div class="alert a-night"><b>夜間の判断</b><br>${esc(NIGHT[k].text)}</div>${grp('夜間は検査で否定できないため搬送を相談', k + ':night', NIGHT[k].consult, 'amb', 'y')}` : ''}
  ${grp('院内で継続する条件（すべて満たすのが目安）', k + ':stay', s.stay, 'grn', 'gr')}
  <p class="note">再評価：${esc(s.recheck)}</p></div>`;
 });
 return h;
}
function grp(title, key, items, cls, gc) { return `<div class="grp"><div class="g ${gc || ''}">${esc(title)}</div>${chips('chk:' + key, items, E.chk[key], cls)}</div>`; }
function symLv(k) { return chk(k + ':red').length ? 3 : (chk(k + ':consult').length || (isNight() && chk(k + ':night').length)) ? 2 : chk(k + ':stay').length === SYM[k].stay.length ? 1 : 0; }
function symLvTxt(k) { return ['評価中', '院内継続の条件を満たす', '搬送を相談', 'すぐ搬送を検討'][symLv(k)]; }
const lvPill = l => ['p-none', 'p-ok', 'p-warn', 'p-crit'][l];
function stepTests() {
 const night = isNight(), list = [];
 E.sym.forEach(k => SYM[k].tests.forEach(t => { if (!list.includes(t)) list.push(t); }));
 let h = '';
 if (list.length) h += block('この症候で行う検査（' + (night ? '夜間' : '日中') + '）', W(`<div class="list">${list.map(t => { const kd = testKind(t), ok = avail(kd), st = E.tests[t] || ''; return `<div class="trow"><span class="pill ${ok ? 'p-ok' : night ? 'p-night' : 'p-none'}">${ok ? '可' : kd === 'o' ? '院内困難' : night ? '夜間不可' : '不可'}</span><span>${esc(t)}</span><span class="opts">${['済', '予定'].map(o => `<button type="button" class="opt" data-test="${esc(t)}" data-v="${o}" aria-pressed="${st === o}">${o}</button>`).join('')}</span></div>`; }).join('')}</div>`) +
  (night ? W(`<div class="alert a-night">夜間にできない検査は、症候の画面の「夜間の判断」に沿って、朝まで待てるか・搬送を相談するかを決めてください。</div>`) : ''), `<button type="button" class="hb" data-act="settings">施設の設定</button>`);
 else h += `<p class="note">「症候」を選ぶと、必要な検査が表示されます。</p>`;
 h += block('血液検査の結果', LABS.map(([k, l]) => fld('labs.' + k, l, 'number')).join('') + QUAL.map(([k, l, o]) => W(`<div class="lab">${l}</div>${seg('labs.' + k, o, E.labs[k])}`)).join(''));
 h += block('心電図', fld('ecg.qtc', 'QTc（ms）', 'number') + W(`<div class="lab">所見</div>${chips('ecg.f', ECG_F, E.ecg.f)}`));
 h += block('画像・その他の所見', fld('p.img', '胸部X線・CT・尿検査など', 'ta', 3));
 h += `<section class="block" id="calc-labs"></section>`;
 return h;
}
function labsHTML() { const f = labFlags(); return `<h3><span>検査値の注意</span></h3>${f.length ? W(`<div class="list">${f.map(([l, t]) => `<div class="alert a-${l}">${esc(t)}</div>`).join('')}</div>`) : W('<p class="note">結果を入力すると、注意が必要な値を表示します。</p>')}`; }
function stepDdx() {
 if (!E.sym.length) return `<p class="note">「症候」を選ぶと鑑別が表示されます。</p>`;
 return E.sym.map(k => { const s = SYM[k]; return block(s.n + 'の鑑別', W(s.ddx.map(([n, c], i) => { const key = k + ':' + i, st = E.ddx[key] || ''; return `<div class="ddx"><span class="nm">${esc(n)}</span><span class="opts">${DDX_ST.map(o => `<button type="button" class="opt ${o === '可能性高い' ? 'red' : ''}" data-ddx="${key}" data-v="${o}" aria-pressed="${st === o}">${o}</button>`).join('')}</span><span class="cl">${esc(c)}</span></div>`; }).join(''))); }).join('');
}
function stepAction() {
 let h = '';
 E.sym.forEach(k => { const s = SYM[k]; h += block(s.n + '：初期対応', W(chips('chk:' + k + ':mgmt', s.mgmt, E.chk[k + ':mgmt']))); });
 if (!E.sym.length) h += `<p class="note">「症候」を選ぶと初期対応が表示されます。</p>`;
 h += block('院内では対応できない処置が必要か（該当 → 搬送を相談）', W(chips('needs', NEEDS, E.needs, 'amb')));
 h += block('実施した処置・投薬', fld('p.acts', '時刻・内容（例：21:20 酸素2L開始、21:30 血液培養採取後セフトリアキソン点滴）', 'ta', 4));
 return h;
}
function stepDecision() { return `<section class="block" id="calc-dec"></section>`; }
function decHTML() {
 const R = decide();
 let h = `<h3><span>判定（自動）</span></h3><div class="wide alert ${['a-info', 'a-ok', 'a-warn', 'a-crit'][R.lv]}"><b>${esc(LVTXT[R.lv])}</b>${R.recheck ? `<br>再評価：${esc(R.recheck)}` : ''}</div>`;
 if (R.why.length) h += W(`<div class="lab">判定の理由</div><ul class="b">${R.why.sort((a, b) => b[0] - a[0]).map(([l, t]) => `<li><span class="pill ${lvPill(l)}">${['', '院内', '相談', '搬送'][l]}</span> ${esc(t)}</li>`).join('')}</ul>`);
 R.notes.forEach(([l, t]) => h += W(`<div class="alert a-${l}">${esc(t)}</div>`));
 const hi = []; E.sym.forEach(k => SYM[k].ddx.forEach(([n], i) => { if (E.ddx[k + ':' + i] === '可能性高い') hi.push(n); }));
 if (hi.length) h += W(`<div class="lab">可能性の高い鑑別</div><p>${esc(hi.join('、'))}</p>`);
 h += W(`<p class="note">この判定は、入力した情報をもとにした目安です。最終的な判断は診察した医師が、施設の手順・地域の救急体制・本人と家族の意向を踏まえて行ってください。</p>`);
 return h;
}
function stepRecord() {
 const d = E.dec;
 return block('判断', W(`<div class="lab">決定</div>${seg('dec.choice', DECISIONS, d.choice)}`) + fld('dec.by', '判断した医師', 'text') + fld('dec.time', '判断の時刻', 'datetime-local'))
 + block('連絡・搬送', fld('dec.dest', '搬送先・相談先（病院名・診療科・担当医）', 'text') + fld('dec.call', '連絡の時刻と内容', 'ta', 2) + fld('dec.family', '家族への連絡（時刻・相手・説明内容・意向）', 'ta', 2))
 + block('院内で継続する場合', fld('dec.recheck', '次の再評価（時刻と項目）', 'text') + fld('dec.switch', '搬送に切り替える基準（看護師と共有）', 'ta', 2) + fld('dec.order', '指示内容', 'ta', 3));
}
const STEPS = [stepBackground, stepVitals, stepSymptoms, stepTests, stepDdx, stepAction, stepDecision, stepRecord];

/* ================= 描画：全体 ================= */
function render() {
 const [t, s] = STEP_T[step];
 let h = '';
 if (E.sample) h += `<div class="alert a-info"><b>サンプル（架空の事例）</b>：操作の確認用です。「記録」→「新しい急変」から始めてください。</div>`;
 h += `<div><h2>${t}</h2><p class="lead">${esc(s)}</p></div>` + STEPS[step]();
 if (step === 7) h += `<footer>本アプリは精神科病棟での身体急変時の判断を補助するための目安です。NEWS2は英国王立内科医協会（RCP）の基準に基づきます。各症候の内容は一般的な知見をまとめたもので、施設の手順・最新のガイドライン・医師の診察に代わるものではありません。入力した内容はこの端末のブラウザ内にのみ保存されます。</footer>`;
 $('#main').innerHTML = h;
 $('#steps').innerHTML = STEP_T.map(([n], i) => `<button type="button" class="st" data-act="goto" data-i="${i}" ${i === step ? 'aria-current="step"' : ''}><span class="n">${i + 1}</span>${n}</button>`).join('');
 $('#prevBtn').disabled = step === 0; $('#nextBtn').textContent = step === 7 ? '最初へ ↺' : '次へ →';
 refresh();
 const c = document.querySelector('.st[aria-current="step"]'); if (c) c.scrollIntoView({inline: 'center', block: 'nearest'});
}
function refresh() {
 const R = decide(), b = $('#band');
 b.className = 'band lv' + R.lv;
 b.innerHTML = `<span>${esc(LVTXT[R.lv])}</span><small>${R.N ? 'NEWS2 ' + R.N.total + '点' : ''}${isNight() ? '・夜間' : ''}</small>`;
 const m = $('#modeBtn'); m.textContent = isNight() ? '夜間' : '日中'; m.className = 'hb mode' + (isNight() ? ' night' : '');
 const n = $('#calc-news'); if (n) n.innerHTML = newsHTML();
 const l = $('#calc-labs'); if (l) l.innerHTML = labsHTML();
 const d = $('#calc-dec'); if (d) d.innerHTML = decHTML();
}
function changed(full) { save(); if (full) { const y = window.scrollY; render(); window.scrollTo(0, y); } else refresh(); }
function go(i) { step = Math.max(0, Math.min(7, i)); save(); render(); window.scrollTo(0, 0); }

/* ================= 文書 ================= */
function vitLine(x) { if (!x) return ''; const n = news2(x); return `${fmtT(x.t)} 呼吸${x.rr || '-'} SpO2 ${x.spo2 || '-'}%（${x.o2 === '酸素' ? '酸素' + (x.o2l ? x.o2l + 'L' : '') : '空気'}） 血圧${x.sbp || '-'}/${x.dbp || '-'} 心拍${x.hr || '-'} 体温${x.temp || '-'} 意識${x.avpu ? x.avpu.split(' ')[0] : '-'}${x.glu ? ' 血糖' + x.glu : ''}（NEWS2 ${n.total}点）`; }
function symNames() { return E.sym.map(k => SYM[k].n).join('、'); }
function sbar() {
 const p = E.p, R = decide(), v = lastV(), L = [];
 L.push('【SBAR報告】' + (p.ward ? p.ward + ' ' : '') + E.id);
 L.push('S（状況）：' + [p.age ? p.age + '歳' : '', p.sex || ''].join(' ') + '。' + (symNames() || '症状') + '。' + (v ? '最新 ' + vitLine(v) : ''));
 const bg = [p.dx, p.adm, arr(p.st).join('・'), arr(p.meds).length ? '服薬：' + arr(p.meds).join('・') : '', p.base ? '普段：' + p.base : '', p.cpr ? 'ACP：' + p.cpr + '／' + (p.wish || '意向未確認') : ''].filter(Boolean);
 L.push('B（背景）：' + bg.join('。'));
 const a = []; E.sym.forEach(k => { const r = chk(k + ':red'), c = chk(k + ':consult'), ask = chk(k + ':ask'); if (ask.length) a.push(SYM[k].n + '：' + ask.join('、')); if (r.length) a.push('レッドフラッグ：' + r.join('、')); if (c.length) a.push('相談事項：' + c.join('、')); });
 labFlags().forEach(([, t]) => a.push(t));
 if (R.N) a.push('NEWS2 ' + R.N.total + '点、qSOFA ' + R.N.qsofa + '点');
 L.push('A（評価）：' + (a.join('。') || '評価中'));
 L.push('R（依頼）：' + (R.lv >= 3 ? 'すぐに診察してください。搬送を検討しています。' : R.lv === 2 ? '診察と、搬送・転院の判断をお願いします。' : '診察と今後の指示をお願いします。') + (p.acts ? '　実施済み：' + p.acts.replace(/\n/g, '、') : ''));
 return L.join('\n');
}
function referral() {
 const p = E.p, R = decide(), L = [];
 L.push('【診療情報提供（急変時の転院依頼）】');
 L.push('患者：' + [p.age ? p.age + '歳' : '', p.sex || ''].join(' ') + (p.ward ? '　' + p.ward : '') + '　ID：' + E.id);
 L.push('依頼内容：' + (symNames() || '') + 'に対する精査・加療のお願い');
 L.push(''); L.push('■ 経過とバイタル');
 E.vit.forEach(x => L.push('・' + vitLine(x)));
 const fs = []; E.sym.forEach(k => { const t = [...chk(k + ':ask'), ...chk(k + ':red'), ...chk(k + ':consult')]; if (t.length) fs.push(SYM[k].n + '：' + t.join('、')); });
 if (fs.length) { L.push(''); L.push('■ 所見'); fs.forEach(x => L.push('・' + x)); }
 const lf = labFlags(), lab = LABS.filter(([k]) => num(E.labs[k]) != null).map(([k, l]) => l.split('（')[0] + ' ' + E.labs[k]);
 if (lab.length || E.ecg.qtc || arr(E.ecg.f).length || p.img) { L.push(''); L.push('■ 検査'); if (lab.length) L.push('・血液：' + lab.join('、')); if (E.ecg.qtc || arr(E.ecg.f).length) L.push('・心電図：' + [E.ecg.qtc ? 'QTc ' + E.ecg.qtc + 'ms' : '', ...arr(E.ecg.f)].filter(Boolean).join('、')); if (p.img) L.push('・その他：' + p.img.replace(/\n/g, ' ')); }
 if (isNight()) { const na = ['b', 'e', 'x', 'c'].filter(k => !avail(k)).map(k => TEST_KINDS[k]); if (na.length) L.push('・夜間のため当院では実施できない検査：' + na.join('、')); }
 const hi = []; E.sym.forEach(k => SYM[k].ddx.forEach(([n], i) => { if (E.ddx[k + ':' + i] === '可能性高い') hi.push(n); }));
 if (hi.length) { L.push(''); L.push('■ 考えられる病態：' + hi.join('、')); }
 if (p.acts) { L.push(''); L.push('■ 当院での処置'); L.push(p.acts); }
 L.push(''); L.push('■ 精神科の情報');
 L.push('・診断：' + (p.dx || '') + '　入院形態：' + (p.adm || ''));
 if (p.psy) L.push('・精神症状・行動上の注意：' + p.psy.replace(/\n/g, ' '));
 L.push('・既往・状態：' + [arr(p.st).join('、'), p.phx].filter(Boolean).join('、'));
 L.push('・内服薬：' + (p.medsText ? p.medsText.replace(/\n/g, '、') : arr(p.meds).join('、')));
 if (p.allergy) L.push('・アレルギー：' + p.allergy);
 if (p.base) L.push('・普段の状態：' + p.base.replace(/\n/g, ' '));
 L.push(''); L.push('■ 本人・家族の意向：' + (p.cpr || '未確認') + '／' + (p.wish || '未確認') + (p.kp ? '　キーパーソン：' + p.kp : ''));
 L.push('■ 当院の判断：' + (E.dec.choice || LVTXT[R.lv]));
 L.push('■ 当院の連絡先：（記入）　担当医：' + (E.dec.by || '（記入）'));
 return L.join('\n');
}
function chart() {
 const p = E.p, R = decide(), L = [];
 L.push('【身体急変 記録】' + E.id + '　' + (symNames() || ''));
 L.push('S）' + (E.sym.map(k => chk(k + ':ask').join('、')).filter(Boolean).join('／') || '（記載）'));
 const o = E.vit.map(vitLine); const lf = labFlags().map(x => x[1]); L.push('O）' + [...o, ...lf].join('／'));
 const hi = []; E.sym.forEach(k => SYM[k].ddx.forEach(([n], i) => { if (E.ddx[k + ':' + i] === '可能性高い') hi.push(n); }));
 L.push('A）' + (hi.length ? hi.join('、') + 'を疑う。' : '') + (R.N ? 'NEWS2 ' + R.N.total + '点。' : '') + '判定：' + LVTXT[R.lv] + (isNight() ? '（夜間・検査制限あり）' : ''));
 const pl = [E.dec.choice, p.acts ? p.acts.replace(/\n/g, '、') : '', E.dec.dest ? '搬送先：' + E.dec.dest : '', E.dec.recheck ? '再評価：' + E.dec.recheck : '', E.dec.switch ? '搬送に切り替える基準：' + E.dec.switch : '', E.dec.family ? '家族：' + E.dec.family : ''].filter(Boolean);
 L.push('P）' + (pl.join('／') || '（記載）'));
 return L.join('\n');
}

/* ================= モーダル ================= */
const open = h => { $('#panel').innerHTML = h; $('#modal').hidden = false; };
const close = () => { $('#modal').hidden = true; delArm = null; };
function showReport(kind) {
 kind = kind || 'sbar';
 const t = kind === 'sbar' ? sbar() : kind === 'ref' ? referral() : chart();
 open(`<h3>報告・転院用の文書</h3><div class="opts">${[['sbar', 'SBAR報告（看護師→医師）'], ['ref', '診療情報提供（転院依頼）'], ['chart', 'カルテ記録（SOAP）']].map(([k, l]) => `<button type="button" class="opt" data-act="rep" data-k="${k}" aria-pressed="${kind === k}">${l}</button>`).join('')}</div>
 <textarea class="out" id="outText" readonly>${esc(t)}</textarea>
 <div class="rowbtns"><button type="button" class="hb code" data-act="copy">コピー</button><button type="button" class="hb" data-act="close">閉じる</button><span class="note" id="cmsg" role="status"></span></div>
 <p class="note">（記入）の部分は貼り付け後に書き足してください。</p>`);
}
function showCode() {
 open(`<h3>心停止・窒息のときは</h3>
 <div class="alert a-crit"><b>反応がない・普段どおりの呼吸がない</b><ol style="margin:6px 0 0;padding-left:1.3em"><li>大声で応援を呼ぶ・救急カートとAEDを持ってきてもらう</li><li>DNARを確認（DNARなら心肺蘇生は行わず、医師に連絡）</li><li>胸骨圧迫を開始（強く・速く・絶え間なく、1分間に100〜120回）</li><li>AEDが届いたら電源を入れ、音声に従う</li><li>119番通報（または救急病院へ連絡）</li></ol></div>
 <div class="alert a-warn"><b>窒息（声が出ない・咳ができない・喉を押さえる）</b><ol style="margin:6px 0 0;padding-left:1.3em"><li>応援を呼び、咳ができれば咳を促す</li><li>背部叩打・腹部突き上げ（ハイムリック法）</li><li>吸引、可能なら喉頭鏡とマギル鉗子で除去</li><li>反応がなくなれば心肺蘇生へ</li></ol></div>
 <div class="rowbtns"><button type="button" class="hb" data-act="close">閉じる</button></div>`);
}
function showSettings() {
 const row = (w, k) => `<button type="button" class="opt chip" data-av="${w}:${k}" aria-pressed="${!!DB.avail[w][k]}">${esc(TEST_KINDS[k])}</button>`;
 open(`<h3>施設の設定</h3>
 <div class="lab">日中・夜間の切り替え</div>${['auto', 'day', 'night'].map(m => `<button type="button" class="opt" data-mode="${m}" aria-pressed="${DB.mode === m}">${{auto: '自動（9〜17時を日中）', day: '日中', night: '夜間'}[m]}</button>`).join(' ')}
 <div class="lab">日中にできる検査</div><div class="opts">${['s', 'b', 'e', 'x', 'c'].map(k => row('day', k)).join('')}</div>
 <div class="lab">夜間にできる検査</div><div class="opts">${['s', 'b', 'e', 'x', 'c'].map(k => row('night', k)).join('')}</div>
 <p class="note">夜間に心電図が取れる場合などは、ここで切り替えてください。設定はこの端末に保存されます。</p>
 <div class="rowbtns"><button type="button" class="hb" data-act="close">閉じる</button></div>`);
}
function showEps() {
 const l = Object.values(DB.eps).sort((a, b) => (b.updated || '').localeCompare(a.updated || ''));
 open(`<h3>急変の記録</h3><p class="note">記録はこの端末のブラウザ内だけに保存されます。氏名は入れず、院内の管理IDを使ってください。</p>
 <div class="rowbtns"><button type="button" class="hb code" data-act="newEp">＋ 新しい急変</button><button type="button" class="hb" data-act="settings">施設の設定</button></div>
 <div>${l.map(e => `<div class="ep"><div class="nm">${esc(e.id)}${E && e.id === E.id ? ' <span class="pill p-info">表示中</span>' : ''}<small>${esc(e.sym.map(k => SYM[k] ? SYM[k].n : '').join('、') || '症候未選択')}・${e.updated ? new Date(e.updated).toLocaleString('ja-JP', {month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit'}) : ''}</small></div><button type="button" class="hb" data-act="openEp" data-id="${esc(e.id)}">開く</button><button type="button" class="del" data-act="delEp" data-id="${esc(e.id)}">${delArm === e.id ? '本当に削除' : '削除'}</button></div>`).join('')}</div>
 <div class="rowbtns"><button type="button" class="hb" data-act="close">閉じる</button></div>`);
}

/* ================= イベント ================= */
document.addEventListener('click', ev => {
 const b = ev.target.closest('button'); if (!b) { if (ev.target === $('#modal')) close(); return; }
 const d = b.dataset;
 if (d.set) { const cur = getP(d.set); setP(d.set, cur === d.v ? '' : d.v); return changed(true); }
 if (d.tog) {
  if (d.tog === 'sym') { const k = SYMS.find(s => s.n === d.v).k, i = E.sym.indexOf(k); i < 0 ? E.sym.push(k) : E.sym.splice(i, 1); return changed(true); }
  let key = d.tog, a;
  if (key.startsWith('chk:')) { key = key.slice(4); a = arr(E.chk[key]).slice(); } else a = arr(getP(key)).slice();
  const i = a.indexOf(d.v); i < 0 ? a.push(d.v) : a.splice(i, 1);
  if (d.tog.startsWith('chk:')) E.chk[key] = a; else setP(key, a);
  b.setAttribute('aria-pressed', String(i < 0));
  const symCard = b.closest('.sym'); if (symCard) { const k = key.split(':')[0]; const pl = symCard.querySelector('.t .pill'); pl.className = 'pill ' + lvPill(symLv(k)); pl.textContent = symLvTxt(k); }
  return changed(false);
 }
 if (d.vset) { const [i, k] = d.vset.split(':'); E.vit[i][k] = E.vit[i][k] === d.v ? '' : d.v; return changed(true); }
 if (d.vtog) { const [i, k] = d.vtog.split(':'); E.vit[i][k] = !E.vit[i][k]; b.setAttribute('aria-pressed', String(!!E.vit[i][k])); return changed(false); }
 if (d.test) { E.tests[d.test] = E.tests[d.test] === d.v ? '' : d.v; return changed(true); }
 if (d.ddx) { E.ddx[d.ddx] = E.ddx[d.ddx] === d.v ? '' : d.v; return changed(true); }
 if (d.av) { const [w, k] = d.av.split(':'); DB.avail[w][k] = DB.avail[w][k] ? 0 : 1; save(); showSettings(); render(); return; }
 if (d.mode) { DB.mode = d.mode; save(); showSettings(); render(); return; }
 switch (d.act) {
  case 'next': go(step === 7 ? 0 : step + 1); break;
  case 'prev': go(step - 1); break;
  case 'goto': go(+d.i); break;
  case 'addVit': { const l = lastV(); E.vit.push({t: nowLocal(), o2: l ? l.o2 : '', o2l: l ? l.o2l : '', scale2: l ? l.scale2 : false}); changed(true); break; }
  case 'delVit': E.vit.splice(+d.i, 1); changed(true); break;
  case 'report': showReport(); break;
  case 'rep': showReport(d.k); break;
  case 'code': showCode(); break;
  case 'mode': DB.mode = isNight() ? 'day' : 'night'; save(); render(); break;
  case 'settings': showSettings(); break;
  case 'eps': delArm = null; showEps(); break;
  case 'newEp': load(blank(newId())); step = 0; save(); close(); render(); break;
  case 'openEp': load(DB.eps[d.id]); save(); close(); render(); break;
  case 'delEp': if (delArm !== d.id) { delArm = d.id; showEps(); break; } delete DB.eps[d.id]; delArm = null; if (E.id === d.id) { const r = Object.values(DB.eps); load(r[0] || sample()); render(); } save(); showEps(); break;
  case 'close': close(); break;
  case 'copy': { const t = $('#outText'), m = $('#cmsg'); try { navigator.clipboard.writeText(t.value).then(() => m.textContent = 'コピーしました', () => { t.select(); m.textContent = '全文を選択しました。長押しでコピーしてください'; }); } catch (e) { t.select(); m.textContent = '全文を選択しました。長押しでコピーしてください'; } break; }
 }
});
document.addEventListener('input', ev => {
 const t = ev.target, d = t.dataset;
 if (d.in) { setP(d.in, t.value); changed(false); }
 else if (d.vin) { const [i, k] = d.vin.split(':'); E.vit[i][k] = t.value; changed(false); }
});
document.addEventListener('keydown', e => { if (e.key === 'Escape' && !$('#modal').hidden) close(); });

/* ================= 起動 ================= */
load(DB.cur && DB.eps[DB.cur] ? DB.eps[DB.cur] : sample());
save(); render();
