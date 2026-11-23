"""精神科病棟 身体急変サポート：Excel版を生成する。
   node tools/export.js → python3 tools/build.py の順に実行。"""
import json, os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter as CL

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, 'data.json'), encoding='utf-8'))
OUT = os.path.join(HERE, '..', 'excel', '身体急変サポート.xlsx')
FN = 'Arial'; ACC = '23395B'
F_IN = PatternFill('solid', fgColor='FFF2CC'); F_OUT = PatternFill('solid', fgColor='E2E8F2'); F_HEAD = PatternFill('solid', fgColor=ACC)
F_SUB = PatternFill('solid', fgColor='EEF1F5'); F_RED = PatternFill('solid', fgColor='FBE3E0'); F_AMB = PatternFill('solid', fgColor='FBEFD9'); F_GRN = PatternFill('solid', fgColor='E1F1E7'); F_NIGHT = PatternFill('solid', fgColor='E7E6F6')
thin = Side(style='thin', color='C9D2D9'); BOX = Border(left=thin, right=thin, top=thin, bottom=thin)
WRAP = Alignment(wrap_text=True, vertical='top'); CEN = Alignment(horizontal='center', vertical='center', wrap_text=True)
def ft(**k): return Font(name=FN, **k)
def Q(s): return '"' + str(s).replace('"', '""') + '"'
J = lambda parts, sep='、': '_xlfn.TEXTJOIN(' + Q(sep) + ',TRUE,' + ','.join(parts) + ')' if parts else '""'

wb = Workbook(); USE = wb.active; USE.title = '使い方'
LIST = wb.create_sheet('リスト'); _l = {}
def lst(opts):
    k = tuple(opts)
    if k not in _l:
        c = CL(len(_l) + 1)
        for i, o in enumerate(opts): LIST[f'{c}{i+1}'] = o
        _l[k] = f"'リスト'!${c}$1:${c}${len(opts)}"
    return _l[k]
class DV:
    def __init__(s, ws): s.ws, s.m = ws, {}
    def add(s, opts, cell):
        r = lst(opts)
        if r not in s.m:
            d = DataValidation(type='list', formula1='=' + r, allow_blank=True); s.ws.add_data_validation(d); s.m[r] = d
        s.m[r].add(cell)

def setw(ws, widths):
    for k, w in widths.items(): ws.column_dimensions[k].width = w
def head(ws, r, text, cols=10, big=True):
    c = ws.cell(r, 1, text); c.font = ft(bold=True, color='FFFFFF' if big else ACC, size=12 if big else 10)
    for i in range(1, cols + 1): ws.cell(r, i).fill = F_HEAD if big else F_SUB
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=cols)
def inp(ws, ref, fmt=None):
    c = ws[ref]; c.fill = F_IN; c.border = BOX; c.font = ft(); c.alignment = WRAP
    if fmt: c.number_format = fmt
    return c
def out(ws, ref, val, bold=True, fill=F_OUT):
    c = ws[ref]; c.value = val; c.fill = fill; c.font = ft(bold=bold); c.alignment = WRAP; c.border = BOX
    return c

MAIN = '急変シート'
SHEETS = {}   # k -> (sheet name, refs)
SHORT = {'fever':'発熱','resp':'呼吸困難','cons':'意識障害','chest':'胸痛','abd':'腹痛・イレウス','fall':'転倒・頭部打撲','seiz':'けいれん','shock':'ショック','arrh':'不整脈・失神','gib':'消化管出血','glu':'血糖異常','intake':'摂取不良・脱水','nms':'悪性症候群','water':'水中毒・低Na','choke':'窒息・誤嚥','dvt':'下肢腫脹DVT','urine':'尿閉・乏尿','od':'過量服薬・誤飲'}

# ================= メインシート =================
M = wb.create_sheet(MAIN); dvm = DV(M)
setw(M, {'A': 22, 'B': 15, 'C': 9, 'D': 9, 'E': 8, 'F': 8, 'G': 9, 'H': 8, 'I': 8, 'J': 8, 'K': 15, 'L': 8, 'M': 9, 'N': 8})
for k in 'OPQRSTUVWXYZ': M.column_dimensions[k].hidden = True
M['A1'] = '精神科病棟 身体急変サポート'; M['A1'].font = ft(size=15, bold=True, color=ACC); M.merge_cells('A1:N1')
M['A2'] = '黄色＝入力、水色＝自動計算。症候ごとのチェックは各症候のシートで行い、判定はこのシートに集まります。'; M['A2'].font = ft(size=9, color='596579'); M.merge_cells('A2:N2')
R = {}
r = 4
M.cell(r, 1, '判定（自動）').font = ft(bold=True); M.merge_cells(f'B{r}:N{r}'); R['dec'] = f'B{r}'; M.row_dimensions[r].height = 30
r += 1; M.cell(r, 1, '判定の理由').font = ft(bold=True); M.merge_cells(f'B{r}:N{r}'); R['why'] = f'B{r}'; M.row_dimensions[r].height = 110
r += 1; M.cell(r, 1, '意向・時間帯の注意').font = ft(bold=True); M.merge_cells(f'B{r}:N{r}'); R['notes'] = f'B{r}'; M.row_dimensions[r].height = 60
M.freeze_panes = 'A7'
r = 8
head(M, r, '時間帯と施設の設定', 14); r += 1
M.cell(r, 1, '時間帯').font = ft(bold=True); inp(M, f'B{r}').value = '日中'; dvm.add(['日中', '夜間'], f'B{r}'); R['mode'] = f'$B${r}'
M.cell(r, 3, '夜間にできない検査は、各症候シートで「不可」と表示されます').font = ft(size=9, color='596579'); M.merge_cells(f'C{r}:N{r}'); r += 1
M.cell(r, 1, '検査の種類').font = ft(bold=True, size=9); M.cell(r, 2, '日中').font = ft(bold=True, size=9); M.cell(r, 3, '夜間').font = ft(bold=True, size=9); r += 1
AV = {}
for k in ['s', 'b', 'e', 'x', 'c', 'o']:
    M.cell(r, 1, D['TEST_KINDS'][k]).font = ft(size=9); M.cell(r, 1).alignment = WRAP
    for col, w in [('B', 'day'), ('C', 'night')]:
        c = inp(M, f'{col}{r}'); c.alignment = CEN
        default = (w == 'day' and k != 'o') or (w == 'night' and k == 's')
        c.value = '✓' if default else ''; dvm.add(['✓'], f'{col}{r}')
    AV[k] = f"IF('{MAIN}'!{R['mode']}=\"夜間\",'{MAIN}'!$C${r},'{MAIN}'!$B${r})=\"✓\""
    M.row_dimensions[r].height = 26 if len(D['TEST_KINDS'][k]) > 14 else 16
    r += 1
r += 1
head(M, r, '患者の背景と本人・家族の意向', 14); r += 1
def mfield(label, key, kind='text', opts=None, h=None):
    global r
    M.cell(r, 1, label).font = ft(bold=True); M.cell(r, 1).alignment = WRAP
    M.merge_cells(f'B{r}:N{r}'); c = inp(M, f'B{r}')
    if opts: dvm.add(opts, f'B{r}'); M.cell(r, 15)
    if h: M.row_dimensions[r].height = h
    R[key] = f'$B${r}'; r += 1
mfield('事例ID（氏名は入れない）', 'id'); mfield('年齢', 'age'); mfield('性別', 'sex', opts=['男性', '女性']); mfield('病棟・部屋', 'ward')
mfield('入院形態', 'adm', opts=['任意入院', '医療保護入院', '措置入院', '応急入院', 'その他']); mfield('精神科診断', 'dx')
mfield('既往・状態（例：' + '、'.join(D['STATES'][:5]) + '）', 'st', h=32); mfield('内服薬の詳細', 'medsText', h=45)
mfield('普段の状態（ADL・意識・会話・食事・普段の血圧）', 'base', h=45); mfield('精神症状・行動上の注意（拘束・隔離・自己抜去の恐れ）', 'psy', h=32)
mfield('心肺蘇生', 'cpr', opts=['心肺蘇生を希望（フルコード）', 'DNAR（心肺蘇生をしない）', '未確認'])
mfield('急変時の治療・搬送の意向', 'wish', opts=['搬送を含め積極的な治療を希望', '院内でできる範囲の治療を希望', '苦痛の緩和を中心に', '未確認'])
mfield('キーパーソン・連絡先', 'kp')
M.cell(r, 1, 'ハイリスクの薬（A列に✓）').font = ft(bold=True, color=ACC); r += 1
MEDREF = {}
for m in D['MEDS']:
    c = inp(M, f'A{r}'); c.alignment = CEN; dvm.add(['✓'], f'A{r}')
    M.cell(r, 2, m['n']).font = ft(); M.merge_cells(f'B{r}:N{r}')
    MEDREF[m['n']] = f"'{MAIN}'!$A${r}"; r += 1
r += 1
head(M, r, 'バイタルとNEWS2', 14); r += 1
VH = ['時刻', '呼吸数', 'SpO2', '酸素', '酸素L', 'スケール2', '収縮期', '拡張期', '心拍', '体温', '意識（ACVPU）', '血糖', 'NEWS2', 'qSOFA']
for i, h in enumerate(VH):
    c = M.cell(r, i + 1, h); c.font = ft(bold=True, size=9, color='FFFFFF'); c.fill = F_HEAD; c.alignment = CEN
r += 1; v0 = r
AVPU = ['A 清明（普段どおり）', 'C 新たな混乱・普段と違う', 'V 呼びかけに反応', 'P 痛みに反応', 'U 反応なし']
for i in range(10):
    rr = r + i
    for col in 'ABCDEFGHIJKL': inp(M, f'{col}{rr}')
    M[f'A{rr}'].number_format = 'm/d h:mm'
    dvm.add(['空気', '酸素'], f'D{rr}'); dvm.add(['✓'], f'F{rr}'); dvm.add(AVPU, f'K{rr}')
    sc = {
     'O': f'IF(B{rr}="","",IF(B{rr}<=8,3,IF(B{rr}<=11,1,IF(B{rr}<=20,0,IF(B{rr}<=24,2,3)))))',
     'P': f'IF(C{rr}="","",IF(F{rr}="✓",IF(C{rr}<=83,3,IF(C{rr}<=85,2,IF(C{rr}<=87,1,IF(OR(C{rr}<=92,D{rr}<>"酸素"),0,IF(C{rr}<=94,1,IF(C{rr}<=96,2,3)))))),IF(C{rr}<=91,3,IF(C{rr}<=93,2,IF(C{rr}<=95,1,0)))))',
     'Q': f'IF(D{rr}="","",IF(D{rr}="酸素",2,0))',
     'R': f'IF(G{rr}="","",IF(G{rr}<=90,3,IF(G{rr}<=100,2,IF(G{rr}<=110,1,IF(G{rr}<=219,0,3)))))',
     'S': f'IF(I{rr}="","",IF(I{rr}<=40,3,IF(I{rr}<=50,1,IF(I{rr}<=90,0,IF(I{rr}<=110,1,IF(I{rr}<=130,2,3))))))',
     'T': f'IF(K{rr}="","",IF(LEFT(K{rr},1)="A",0,3))',
     'U': f'IF(J{rr}="","",IF(J{rr}<=35,3,IF(J{rr}<=36,1,IF(J{rr}<=38,0,IF(J{rr}<=39,1,2)))))'}
    for col, f in sc.items(): M[f'{col}{rr}'] = '=' + f
    M[f'V{rr}'] = f'=IF(COUNT(O{rr}:U{rr})=0,"",MAX(O{rr}:U{rr}))'
    M[f'W{rr}'] = f'=IF(COUNT(O{rr}:U{rr})=0,"",ROW())'
    out(M, f'M{rr}', f'=IF(COUNT(O{rr}:U{rr})=0,"",SUM(O{rr}:U{rr}))').alignment = CEN
    out(M, f'N{rr}', f'=IF(COUNT(O{rr}:U{rr})=0,"",(N(B{rr})>=22)+AND(K{rr}<>"",LEFT(K{rr},1)<>"A")+AND(G{rr}<>"",N(G{rr})<=100))').alignment = CEN
v1 = r + 9; r = v1 + 1
LR = f'MAX($W${v0}:$W${v1})'
ix = lambda col: f'INDEX(${col}:${col},{LR})'
R['lastRow'] = LR
M.cell(r, 1, '最新のNEWS2').font = ft(bold=True)
out(M, f'B{r}', f'=IF({LR}=0,"",{ix("M")})').alignment = CEN; R['news'] = f'$B${r}'
M.cell(r, 3, '対応').font = ft(bold=True)
M.merge_cells(f'D{r}:N{r}')
out(M, f'D{r}', f'=IF({R["news"]}="","バイタルを入力すると計算します",IF({R["news"]}>=7,"緊急対応：持続モニタリング、医師がすぐに診察、搬送を検討",IF({R["news"]}>=5,"至急対応：1時間ごとに観察、医師がすぐに診察、搬送を検討",IF({ix("V")}=3,"1項目が3点：1時間ごとに観察し医師に報告",IF({R["news"]}>=1,"4〜6時間ごとに観察。悪化すれば医師に報告","12時間ごとの観察")))))')
M.row_dimensions[r].height = 30; r += 1
M.cell(r, 2, '各項目の色の基準：NEWS2（英国王立内科医協会）。意識は認知症の方では「普段と比べて新たな混乱」があればCにする。スケール2はCOPDなど高二酸化炭素血症のリスクがある場合（目標SpO2 88〜92%）。').font = ft(size=8, color='596579'); M.merge_cells(f'B{r}:N{r}'); M[f'B{r}'].alignment = WRAP; M.row_dimensions[r].height = 26
r += 2
head(M, r, '検査値（入力すると注意を表示）', 14); r += 1
LABS = [('白血球（/μL）', [('<', 3000, 'warn', '白血球減少'), ('>=', 20000, 'crit', '著明な白血球増加'), ('>', 12000, 'warn', '白血球増加')]),
 ('好中球（/μL）', [('<', 500, 'crit', '高度の好中球減少（クロザピンは直ちに中止）'), ('<', 1500, 'warn', '好中球減少（クロザピンは中止基準）')]),
 ('Hb（g/dL）', [('<', 7, 'crit', '高度の貧血'), ('<', 8, 'warn', '貧血')]),
 ('血小板（万/μL）', [('<', 2, 'crit', '高度の血小板減少'), ('<', 5, 'warn', '血小板減少')]),
 ('CRP（mg/dL）', [('>=', 10, 'warn', '炎症反応の高値')]),
 ('Na（mEq/L）', [('<', 120, 'crit', '高度の低Na'), ('<', 130, 'warn', '低Na'), ('>=', 160, 'crit', '高度の高Na'), ('>', 150, 'warn', '高Na')]),
 ('K（mEq/L）', [('>=', 6, 'crit', '高K（心電図を確認）'), ('>', 5.5, 'warn', '高K'), ('<', 2.5, 'crit', '高度の低K'), ('<', 3, 'warn', '低K（QT延長に注意）')]),
 ('BUN（mg/dL）', [('>=', 40, 'warn', 'BUN高値（脱水・出血・腎障害）')]),
 ('Cr（mg/dL）', [('>=', 2, 'warn', '腎機能低下（普段の値と比較）')]),
 ('CK（U/L）', [('>=', 5000, 'crit', 'CK著明高値（横紋筋融解・悪性症候群）'), ('>=', 1000, 'warn', 'CK高値')]),
 ('AST（U/L）', [('>=', 200, 'warn', '肝機能障害')]),
 ('総ビリルビン（mg/dL）', [('>=', 3, 'warn', '黄疸（胆道感染・閉塞）')]),
 ('アンモニア（μg/dL）', [('>=', 100, 'warn', '高アンモニア血症（バルプロ酸・肝硬変）')]),
 ('リチウム（mEq/L）', [('>=', 1.5, 'crit', 'リチウム中毒域'), ('>', 1.2, 'warn', 'リチウム高値')]),
 ('乳酸（mmol/L）', [('>=', 4, 'crit', '乳酸著明高値'), ('>', 2, 'warn', '乳酸高値')]),
 ('QTc（ms）', [('>=', 500, 'crit', 'QTc著明延長'), ('>=', 470, 'warn', 'QTc延長')]),
 ('血糖（mg/dL）', [('<', 70, 'crit', '低血糖'), ('>=', 500, 'crit', '著明な高血糖'), ('>', 300, 'warn', '高血糖')])]
l0 = r
for name, rules in LABS:
    M.cell(r, 1, name).font = ft(bold=True)
    inp(M, f'B{r}')
    f = '""'
    for op, th, lv, t in reversed(rules): f = f'IF(B{r}{op}{th},{Q(lv + "|" + t)},{f})'
    M[f'O{r}'] = f'=IF(B{r}="","",{f})'
    M.merge_cells(f'C{r}:N{r}')
    out(M, f'C{r}', f'=IF(O{r}="","",IF(LEFT(O{r},4)="crit","【要注意】","")&MID(O{r},FIND("|",O{r})+1,99))', fill=F_OUT)
    r += 1
for name, opts, crit in [('トロポニン', ['陰性', '陽性'], '陽性'), ('D-ダイマー', ['基準値内', '高値'], None), ('心電図の所見', ['著変なし', 'ST上昇', 'ST低下・陰性T', '新たな左脚ブロック', '心房細動', '房室ブロック', 'QRS延長'], None)]:
    M.cell(r, 1, name).font = ft(bold=True); inp(M, f'B{r}'); dvm.add(opts, f'B{r}')
    if name == 'トロポニン': M[f'O{r}'] = f'=IF(B{r}="陽性","crit|トロポニン陽性","")'
    elif name == 'D-ダイマー': M[f'O{r}'] = f'=IF(B{r}="高値","warn|D-ダイマー高値（肺塞栓・深部静脈血栓症）","")'
    else: M[f'O{r}'] = f'=IF(OR(B{r}="ST上昇",B{r}="新たな左脚ブロック"),"crit|心電図："&B{r},IF(OR(B{r}="ST低下・陰性T",B{r}="房室ブロック",B{r}="QRS延長"),"warn|心電図："&B{r},""))'
    M.merge_cells(f'C{r}:N{r}'); out(M, f'C{r}', f'=IF(O{r}="","",MID(O{r},FIND("|",O{r})+1,99))')
    r += 1
l1 = r - 1
R['critLabs'] = f'COUNTIF($O${l0}:$O${l1},"crit|*")'
R['labText'] = '_xlfn.TEXTJOIN("、",TRUE,' + ','.join(f'IF(O{i}="","",MID(O{i},FIND("|",O{i})+1,99))' for i in range(l0, l1 + 1)) + ')'
R['labVals'] = '_xlfn.TEXTJOIN("、",TRUE,' + ','.join(f'IF(B{i}="","",{Q(M.cell(i,1).value.split("（")[0] + " ")}&B{i})' for i in range(l0, l1 + 1)) + ')'
M['Y2'] = '=' + R['labText']; R['labText'] = '$Y$2'
M['Y3'] = '=' + R['labVals']; R['labVals'] = '$Y$3'
M.cell(r, 1, '画像・その他の所見').font = ft(bold=True); M.merge_cells(f'B{r}:N{r}'); inp(M, f'B{r}'); M.row_dimensions[r].height = 40; R['img'] = f'$B${r}'; r += 2
head(M, r, '院内では対応できない処置（A列に✓ → 搬送を相談）', 14); r += 1
n0 = r
for t in D['NEEDS']:
    c = inp(M, f'A{r}'); c.alignment = CEN; dvm.add(['✓'], f'A{r}'); M.cell(r, 2, t).font = ft(); M.merge_cells(f'B{r}:N{r}'); r += 1
R['needs'] = f'COUNTIF($A${n0}:$A${r-1},"✓")'
R['needsText'] = '_xlfn.TEXTJOIN("、",TRUE,' + ','.join(f'IF(A{i}="✓",B{i},"")' for i in range(n0, r)) + ')'
r += 1
head(M, r, '実施した処置と判断の記録', 14); r += 1
for lab, key, h in [('実施した処置・投薬（時刻・内容）', 'acts', 60), ('決定', 'choice', None), ('判断した医師・時刻', 'by', None), ('搬送先・相談先', 'dest', None), ('家族への連絡', 'family', 30), ('次の再評価（院内継続の場合）', 'recheck', None), ('搬送に切り替える基準', 'switch', 30)]:
    M.cell(r, 1, lab).font = ft(bold=True); M.cell(r, 1).alignment = WRAP; M.merge_cells(f'B{r}:N{r}'); inp(M, f'B{r}')
    if key == 'choice': dvm.add(['救急搬送（119番）', '救急病院へ直接連絡して搬送', '当日中の転院・受診を相談', '院内で治療を継続（再評価）', '院内で緩和ケア・看取り'], f'B{r}')
    if h: M.row_dimensions[r].height = h
    R[key] = f'$B${r}'; r += 1
r += 1
out_rows = {}
head(M, r, '報告・転院用の文書（セルをコピー）', 14); r += 1
for lab, key, h in [('SBAR報告（看護師→医師）', 'sbar', 220), ('診療情報提供（転院依頼）', 'ref', 320)]:
    M.cell(r, 1, lab).font = ft(bold=True); M.cell(r, 1).alignment = WRAP; M.merge_cells(f'B{r}:N{r}'); M.row_dimensions[r].height = h
    out_rows[key] = f'B{r}'; r += 1
M.cell(r, 2, '本ツールは判断の補助です。最終判断は診察した医師が、施設の手順・地域の救急体制・本人と家族の意向を踏まえて行ってください。').font = ft(size=8, color='596579'); M.merge_cells(f'B{r}:N{r}')

# ================= 症候シート =================
def build_sym(s, kinds):
    name = SHORT[s['k']]
    ws = wb.create_sheet(name); dv = DV(ws); SR = {}
    setw(ws, {'A': 9, 'B': 30, 'C': 14, 'D': 14, 'E': 14, 'F': 30})
    ws['A1'] = s['n']; ws['A1'].font = ft(size=15, bold=True, color=ACC); ws.merge_cells('A1:F1')
    ws['A2'] = '該当する項目のA列に✓を付けると、「急変シート」の判定に反映されます。'; ws['A2'].font = ft(size=9, color='596579'); ws.merge_cells('A2:F2')
    ws['A3'] = '状態'; ws['A3'].font = ft(bold=True); ws.merge_cells('B3:F3'); SR['state'] = 'B3'; ws.row_dimensions[3].height = 22
    ws['A4'] = '服薬の注意'; ws['A4'].font = ft(bold=True); ws.merge_cells('B4:F4')
    meds = [m for m in D['MEDS'] if s['k'] in m['w']]
    out(ws, 'B4', '=' + J([f'IF({MEDREF[m["n"]]}="✓",{Q(m["n"] + "：" + m["w"][s["k"]])},"")' for m in meds], '／') if meds else '="（該当なし）"', bold=False, fill=F_AMB)
    ws.row_dimensions[4].height = 40
    ws.freeze_panes = 'A5'
    r = 6
    def group(title, key, items, fill):
        nonlocal r
        head(ws, r, title, 6, big=False); ws.cell(r, 1).fill = fill
        for i in range(2, 7): ws.cell(r, i).fill = fill
        r += 1; a = r
        for it in items:
            c = inp(ws, f'A{r}'); c.alignment = CEN; c.font = ft(bold=True, color='B3261E' if fill is F_RED else ACC); dv.add(['✓'], f'A{r}')
            ws.cell(r, 2, it).font = ft(); ws.cell(r, 2).alignment = WRAP; ws.merge_cells(f'B{r}:F{r}')
            ws.row_dimensions[r].height = max(16, 14 * (1 + len(it) // 40)); r += 1
        SR[key + 'N'] = f"COUNTIF('{name}'!$A${a}:$A${r-1},\"✓\")"
        SR[key + 'T'] = '_xlfn.TEXTJOIN("、",TRUE,' + ','.join(f"IF('{name}'!A{i}=\"✓\",'{name}'!B{i},\"\")" for i in range(a, r)) + ')'
        SR[key + 'Total'] = len(items)
        r += 1
    group('確認すること', 'ask', s['ask'], F_SUB)
    group('レッドフラッグ（1つでも → すぐ搬送を検討）', 'red', s['red'], F_RED)
    group('搬送・転院を相談', 'consult', s['consult'], F_AMB)
    head(ws, r, '夜間の判断（検査ができない時間帯）', 6, big=False)
    for i in range(1, 7): ws.cell(r, i).fill = F_NIGHT
    r += 1; ws.cell(r, 2, D['NIGHT'][s['k']]['text']).font = ft(); ws.cell(r, 2).alignment = WRAP; ws.merge_cells(f'B{r}:F{r}')
    ws.row_dimensions[r].height = 14 * (2 + len(D['NIGHT'][s['k']]['text']) // 42); r += 1
    group('夜間は検査で否定できないため搬送を相談（夜間のみ判定に反映）', 'night', D['NIGHT'][s['k']]['consult'], F_NIGHT)
    group('院内で継続する条件（すべて満たすのが目安）', 'stay', s['stay'], F_GRN)
    head(ws, r, '検査（A列：済・予定）', 6, big=False); r += 1
    for t, kd in zip(s['tests'], kinds):
        c = inp(ws, f'A{r}'); c.alignment = CEN; dv.add(['済', '予定'], f'A{r}')
        ws.cell(r, 2, t).font = ft(); ws.cell(r, 2).alignment = WRAP; ws.merge_cells(f'B{r}:E{r}')
        out(ws, f'F{r}', f'=IF({AV[kd]},"可","不可（"&{MAIN_MODE}&"）")' if kd != 'o' else '="院内では困難"', fill=F_OUT).alignment = CEN
        ws.row_dimensions[r].height = max(16, 14 * (1 + len(t) // 36)); r += 1
    r += 1
    head(ws, r, '鑑別（A列：可能性高い・保留・否定的）', 6, big=False); r += 1
    a = r
    for n, cl in s['ddx']:
        c = inp(ws, f'A{r}'); c.alignment = CEN; dv.add(['可能性高い', '保留', '否定的'], f'A{r}')
        ws.cell(r, 2, n).font = ft(bold=True); ws.cell(r, 2).alignment = WRAP
        ws.cell(r, 3, cl).font = ft(size=9, color='596579'); ws.cell(r, 3).alignment = WRAP; ws.merge_cells(f'C{r}:F{r}')
        ws.row_dimensions[r].height = max(18, 13 * (1 + len(cl) // 44)); r += 1
    SR['ddxT'] = '_xlfn.TEXTJOIN("、",TRUE,' + ','.join(f"IF('{name}'!A{i}=\"可能性高い\",'{name}'!B{i},\"\")" for i in range(a, r)) + ')'
    r += 1
    group('初期対応（実施したらA列に✓）', 'mgmt', s['mgmt'], F_SUB)
    ws.cell(r, 1, '再評価').font = ft(bold=True); ws.cell(r, 2, s['recheck']).font = ft(); ws.cell(r, 2).alignment = WRAP; ws.merge_cells(f'B{r}:F{r}')
    # 状態
    nightOn = f'{MAIN_MODE}="夜間"'
    st = (f'=IF({SR["redN"]}>0,"すぐ搬送を検討（レッドフラッグ "&{SR["redN"]}&"項目）",IF(OR({SR["consultN"]}>0,AND({nightOn},{SR["nightN"]}>0)),"搬送を相談",'
          f'IF({SR["stayN"]}={SR["stayTotal"]},"院内継続の条件を満たす",IF({SR["askN"]}+{SR["stayN"]}>0,"評価中","（未評価）"))))')
    out(ws, 'B3', st, fill=F_OUT)
    SR['used'] = f'({SR["askN"]}+{SR["redN"]}+{SR["consultN"]}+{SR["nightN"]}+{SR["stayN"]}+{SR["mgmtN"]}>0)'
    ws.column_dimensions['H'].hidden = True
    for i, key in enumerate(['askT', 'redT', 'consultT', 'nightT', 'ddxT', 'askN', 'redN', 'consultN', 'nightN', 'stayN', 'mgmtN', 'used']):
        ws[f'H{i+1}'] = '=' + SR[key].replace(f"'{name}'!", '')
        SR[key] = f"'{name}'!$H${i+1}"
    SR['name'] = name
    SHEETS[s['k']] = SR

MAIN_MODE = R['mode'].replace('$B$', f"'{MAIN}'!$B$")
for s, kinds in zip(D['SYMS'], D['kinds']): build_sym(s, kinds)

# ================= メインの判定式 =================
S = list(SHEETS.values())
red = '+'.join(x['redN'] for x in S); con = '+'.join(x['consultN'] for x in S); ngt = '+'.join(x['nightN'] for x in S)
lr = R['lastRow']
sp, o2, sbp, av, qs, mx = (f'INDEX($C:$C,{lr})', f'INDEX($D:$D,{lr})', f'INDEX($G:$G,{lr})', f'INDEX($K:$K,{lr})', f'INDEX($N:$N,{lr})', f'INDEX($V:$V,{lr})')
nw = R['news']
L3 = f'OR({red}>0,AND({nw}<>"",N({nw})>=7),AND({lr}>0,{o2}="酸素",{sp}<>"",N({sp})<90),AND({lr}>0,{sbp}<>"",N({sbp})<90),AND({lr}>0,OR(LEFT({av},1)="P",LEFT({av},1)="U")))'
L2 = f'OR({con}>0,AND({R["mode"]}="夜間",{ngt}>0),{R["critLabs"]}>0,{R["needs"]}>0,AND({nw}<>"",N({nw})>=5),AND({lr}>0,{mx}=3),AND({lr}>0,N({qs})>=2))'
M['X4'] = f'=IF({L3},3,IF({L2},2,IF(OR({nw}<>"",{"+".join(x["askN"] + "+" + x["stayN"] for x in S)}>0),1,0)))'
out(M, R['dec'], '=CHOOSE($X$4+1,"バイタルと症候を入力すると判定します","院内で治療を続けて再評価","搬送・転院を相談（医師が診察して判断）","すぐに搬送を検討（救急要請・救急病院へ連絡）")&IF($X$4=0,"","　再評価："&IF($X$4=3,"持続観察",IF($X$4=2,"1時間ごと","NEWS2に応じて（4〜12時間ごと）")))')
M[R['dec']].font = ft(bold=True, size=13, color='B3261E')
why = [f'IF({nw}="","","NEWS2 "&{nw}&"点、qSOFA "&{qs}&"点")']
for x in S:
    why.append(f'IF({x["redN"]}>0,{Q(x["name"] + "（レッドフラッグ）：")}&{x["redT"]},"")')
    why.append(f'IF({x["consultN"]}>0,{Q(x["name"] + "（搬送相談）：")}&{x["consultT"]},"")')
    why.append(f'IF(AND({R["mode"]}="夜間",{x["nightN"]}>0),{Q(x["name"] + "（夜間・検査できず）：")}&{x["nightT"]},"")')
    why.append(f'IF(AND({x["redN"]}+{x["consultN"]}=0,{x["stayN"]}={x["stayTotal"]}),{Q(x["name"] + "：院内継続の条件をすべて満たす")},"")')
why.append(f'IF({R["critLabs"]}>0,"検査値："&{R["labText"]},"")')
why.append(f'IF({R["needs"]}>0,"院内で困難な処置："&{R["needsText"]},"")')
out(M, R['why'], '=' + J(why, '\n'), bold=False)
notes = [f'IF(AND($X$4>=2,{R["wish"]}="苦痛の緩和を中心に"),"意向は「苦痛の緩和を中心に」：院内での症状緩和を軸に。搬送で苦痛が和らぐ場合（骨折・窒息など）は家族と相談","")',
         f'IF(AND($X$4>=2,{R["wish"]}="院内でできる範囲の治療を希望"),"意向は「院内でできる範囲」：搬送が必要なら理由を家族に説明し、改めて意向を確認","")',
         f'IF(AND($X$4>=2,OR({R["wish"]}="",{R["wish"]}="未確認")),"意向が未確認：キーパーソンに連絡して確認。待てない状況では救命を優先","")',
         f'IF({R["cpr"]}="DNAR（心肺蘇生をしない）","DNARは心肺蘇生をしない意思で、搬送や治療をしないという意味ではない","")',
         f'IF(AND($X$4>=1,{R["mode"]}="夜間"),"夜間：各症候シートの「夜間の判断」を確認","")']
out(M, R['notes'], '=' + J(notes, '\n'), bold=False)
used = [f'IF({x["used"]},{Q(x["name"])},"")' for x in S]
syms = J(used)
vline = f'IF({lr}=0,"",TEXT({ix("A")},"m/d h:mm")&" 呼吸"&{ix("B")}&" SpO2 "&{ix("C")}&"%（"&IF({ix("D")}="酸素","酸素"&{ix("E")}&"L","空気")&"） 血圧"&{ix("G")}&"/"&{ix("H")}&" 心拍"&{ix("I")}&" 体温"&{ix("J")}&" 意識"&LEFT({ix("K")},1)&IF({ix("L")}="",""," 血糖"&{ix("L")})&"（NEWS2 "&{ix("M")}&"点）")'
meds = J([f'IF({v}="✓",{Q(k)},"")' for k, v in MEDREF.items()], '・')
asks = J([f'IF({x["askN"]}>0,{Q(x["name"] + "：")}&{x["askT"]},"")' for x in S], '。')
reds = J([f'IF({x["redN"]}>0,{x["redT"]},"")' for x in S], '、')
cons = J([f'IF({x["consultN"]}>0,{x["consultT"]},"")' for x in S], '、')
ddx = J([f'{x["ddxT"]}' for x in S], '、')
HY = {}
for i, (key, f) in enumerate([('syms', syms), ('meds', meds), ('asks', asks), ('reds', reds), ('cons', cons), ('ddx', ddx), ('labText', R['labText']), ('labVals', R['labVals']), ('vline', vline)]):
    M[f'Y{4+i}'] = '=' + f; HY[key] = f'$Y${4+i}'
syms, meds, asks, reds, cons, ddx, vline = HY['syms'], HY['meds'], HY['asks'], HY['reds'], HY['cons'], HY['ddx'], HY['vline']
R['labText'], R['labVals'] = HY['labText'], HY['labVals']
P = R
sb = (f'="【SBAR報告】"&{P["ward"]}&" "&{P["id"]}&CHAR(10)&"S（状況）："&{P["age"]}&"歳 "&{P["sex"]}&"。"&{syms}&"。"&IF({lr}=0,"","最新 "&{vline})'
      f'&CHAR(10)&"B（背景）："&_xlfn.TEXTJOIN("。",TRUE,{P["dx"]},{P["adm"]},{P["st"]},IF({meds}="","","服薬："&{meds}),IF({P["base"]}="","","普段："&{P["base"]}),IF({P["cpr"]}="","","ACP："&{P["cpr"]}&"／"&{P["wish"]}))'
      f'&CHAR(10)&"A（評価）："&_xlfn.TEXTJOIN("。",TRUE,{asks},IF({reds}="","","レッドフラッグ："&{reds}),IF({cons}="","","相談事項："&{cons}),{R["labText"]},IF({nw}="","","NEWS2 "&{nw}&"点、qSOFA "&{qs}&"点"))'
      f'&CHAR(10)&"R（依頼）："&CHOOSE($X$4+1,"診察と今後の指示をお願いします。","診察と今後の指示をお願いします。","診察と、搬送・転院の判断をお願いします。","すぐに診察してください。搬送を検討しています。")&IF({P["acts"]}="","","　実施済み："&{P["acts"]})')
out(M, out_rows['sbar'], sb, bold=False)
vlines = J([f'IF(M{i}="","",TEXT(A{i},"m/d h:mm")&" 呼吸"&B{i}&" SpO2 "&C{i}&"%（"&IF(D{i}="酸素","酸素"&E{i}&"L","空気")&"） 血圧"&G{i}&"/"&H{i}&" 心拍"&I{i}&" 体温"&J{i}&" 意識"&LEFT(K{i},1)&"（NEWS2 "&M{i}&"点）")' for i in range(v0, v1 + 1)], '\n')
M['Y13'] = '=' + vlines; vlines = '$Y$13'
nightNA = J([f'IF(AND({R["mode"]}="夜間",NOT({AV[k]})),{Q(D["TEST_KINDS"][k])},"")' for k in ['b', 'e', 'x', 'c']], '、')
M['Y14'] = '=' + nightNA; nightNA = '$Y$14'
rf = (f'="【診療情報提供（急変時の転院依頼）】"&CHAR(10)&"患者："&{P["age"]}&"歳 "&{P["sex"]}&"　"&{P["ward"]}&"　ID："&{P["id"]}&CHAR(10)&"依頼内容："&{syms}&"に対する精査・加療のお願い"'
      f'&CHAR(10)&CHAR(10)&"■ 経過とバイタル"&CHAR(10)&{vlines}'
      f'&CHAR(10)&CHAR(10)&"■ 所見"&CHAR(10)&_xlfn.TEXTJOIN(CHAR(10),TRUE,{asks},IF({reds}="","","危険な所見："&{reds}),IF({cons}="","","その他："&{cons}))'
      f'&CHAR(10)&CHAR(10)&"■ 検査"&CHAR(10)&_xlfn.TEXTJOIN(CHAR(10),TRUE,{R["labVals"]},{R["img"]},IF({nightNA}="","","夜間のため当院で実施できない検査："&{nightNA}))'
      f'&IF({ddx}="","",CHAR(10)&CHAR(10)&"■ 考えられる病態："&{ddx})'
      f'&IF({P["acts"]}="","",CHAR(10)&CHAR(10)&"■ 当院での処置"&CHAR(10)&{P["acts"]})'
      f'&CHAR(10)&CHAR(10)&"■ 精神科の情報"&CHAR(10)&"診断："&{P["dx"]}&"　入院形態："&{P["adm"]}&CHAR(10)&"精神症状・行動上の注意："&{P["psy"]}&CHAR(10)&"既往・状態："&{P["st"]}&CHAR(10)&"内服薬："&IF({P["medsText"]}="",{meds},{P["medsText"]})&CHAR(10)&"普段の状態："&{P["base"]}'
      f'&CHAR(10)&CHAR(10)&"■ 本人・家族の意向："&{P["cpr"]}&"／"&{P["wish"]}&"　キーパーソン："&{P["kp"]}&CHAR(10)&"■ 当院の判断："&IF({P["choice"]}="",{R["dec"]},{P["choice"]})&CHAR(10)&"■ 当院の連絡先：（記入）　担当医："&{P["by"]}')
out(M, out_rows['ref'], rf, bold=False)

# ================= 紹介状 =================
K = wb.create_sheet('紹介状'); dvk = DV(K)
setw(K, {'A': 22, 'B': 70})
K['A1'] = '紹介状（診療情報提供書）'; K['A1'].font = ft(size=15, bold=True, color=ACC); K.merge_cells('A1:B1')
K['A2'] = '黄色を入力すると、急変シートと症候シートの内容から本文を自動で作ります。氏名・生年月日は院内の様式に貼り付けてから記入してください。'; K['A2'].font = ft(size=9, color='596579'); K.merge_cells('A2:B2'); K['A2'].alignment = WRAP
KR = {}; r = 4
PURP = ['精査・加療のお願い', '救急での診察・加療のお願い', '入院加療のお願い', '外来受診のお願い']
for lab, key, opts in [('紹介先の医療機関', 'to', None), ('診療科', 'dept', None), ('担当医（空欄なら「ご担当」）', 'doc', None), ('紹介の目的', 'purpose', PURP),
                       ('傷病名（空欄なら鑑別の「可能性高い」から自動）', 'dx', None), ('その他の連絡事項', 'extra', None),
                       ('紹介元：病院名', 'fname', None), ('紹介元：住所', 'faddr', None), ('紹介元：電話', 'ftel', None), ('紹介元：FAX', 'ffax', None)]:
    K.cell(r, 1, lab).font = ft(bold=True); K.cell(r, 1).alignment = WRAP; inp(K, f'B{r}')
    if opts: dvk.add(opts, f'B{r}'); K[f'B{r}'] = opts[0]
    if key in ('dx', 'extra'): K.row_dimensions[r].height = 36
    KR[key] = f'$B${r}'; r += 1
r += 1
K.cell(r, 1, '紹介状（このセルをコピー）').font = ft(bold=True); K.cell(r, 1).alignment = WRAP
Mq = lambda ref: f"'{MAIN}'!" + ref
P2 = {k: Mq(v) for k, v in R.items() if isinstance(v, str) and v.startswith('$')}
M['Y15'] = (f'=IF(M{v0}="","","体温"&J{v0}&"℃、心拍"&I{v0}&"/分、血圧"&G{v0}&"/"&H{v0}&"mmHg、呼吸数"&B{v0}&"/分、SpO2 "&C{v0}&"%（"&IF(D{v0}="酸素","酸素"&E{v0}&"L投与下","室内気")&"）、意識 "&MID(K{v0},3,20)&"（NEWS2 "&M{v0}&"点）")')
M['Y16'] = (f'=IF({LR}=0,"","体温"&{ix("J")}&"℃、心拍"&{ix("I")}&"/分、血圧"&{ix("G")}&"/"&{ix("H")}&"mmHg、呼吸数"&{ix("B")}&"/分、SpO2 "&{ix("C")}&"%（"&IF({ix("D")}="酸素","酸素"&{ix("E")}&"L投与下","室内気")&"）、意識 "&MID({ix("K")},3,20)&"（NEWS2 "&{ix("M")}&"点）")')
M['Y17'] = f'=IF(OR(A{v0}="",{LR}=ROW(A{v0})),"",TEXT(INDEX($A:$A,{LR}),"m月d日h時mm分"))'
dxauto = f'IF({Mq("$Y$9")}="",{Mq("$Y$4")},SUBSTITUTE({Mq("$Y$9")},"、","の疑い"&CHAR(10)&"　")&"の疑い")'
pur = f'CHOOSE(MATCH(\'紹介状\'!{KR["purpose"]},{{"精査・加療のお願い","救急での診察・加療のお願い","入院加療のお願い","外来受診のお願い"}},0),"ご精査・ご加療","救急でのご診察・ご加療","入院でのご加療","外来でのご診察")'
needsTxt = f"_xlfn.TEXTJOIN(\"、\",TRUE,{','.join(Mq(f'$B${i}') if False else f'IF({Mq(chr(36)+chr(65)+chr(36)+str(i))}=\"✓\",{Mq(chr(36)+chr(66)+chr(36)+str(i))},\"\")' for i in range(n0, n0 + len(D['NEEDS'])))})"
M['Y18'] = '=' + needsTxt
narr = (f'IF({Mq("$A$" + str(v0))}="","",TEXT({Mq("$A$" + str(v0))},"m月d日h時mm分")&"頃より、")&IF({Mq("$Y$4")}="","身体症状",{Mq("$Y$4")})&"を認めました。"'
        f'&IF({Mq("$Y$6")}="","","所見として、"&{Mq("$Y$6")}&"がみられます。")'
        f'&IF({Mq("$Y$15")}="","","バイタルサインは"&{Mq("$Y$15")}&IF({Mq("$Y$17")}="","でした。","でしたが、"&{Mq("$Y$17")}&"には"&{Mq("$Y$16")}&"となっています。"))'
        f'&IF({Mq("$Y$7")}="","","また、"&{Mq("$Y$7")}&"を認めます。")'
        f'&IF({Mq("$Y$2")}="","","検査では"&{Mq("$Y$2")}&"を認めました。")'
        f'&IF({Mq("$Y$9")}="","",{Mq("$Y$9")}&"を疑っております。")'
        f'&_xlfn.TEXTJOIN("、",TRUE,IF(AND({Mq(R["mode"])}="夜間",{Mq("$Y$14")}<>""),"夜間のため当院では"&{Mq("$Y$14")}&"が実施できず",""),IF({Mq("$Y$18")}="","",{Mq("$Y$18")}&"が必要と考えられ"))'
        f'&IF(OR(AND({Mq(R["mode"])}="夜間",{Mq("$Y$14")}<>""),{Mq("$Y$18")}<>""),"、","")&"貴院にて"&{pur}&"をお願いしたく、ご紹介申し上げます。"')
M['Y19'] = '=' + narr
P = {k: Mq(v) for k, v in R.items() if isinstance(v, str) and v.startswith('$B$')}
lt = (f'="診療情報提供書（紹介状）"&CHAR(10)&CHAR(10)&"　　　　　　　　　　　　　　　　"&TEXT(TODAY(),"yyyy年m月d日")'
      f'&CHAR(10)&IF({KR["to"]}="","（紹介先医療機関）",{KR["to"]})&CHAR(10)&IF({KR["dept"]}="","",{KR["dept"]}&"　")&IF({KR["doc"]}="","ご担当",{KR["doc"]})&" 先生　御侍史"'
      f'&CHAR(10)&CHAR(10)&"紹介元："&IF({KR["fname"]}="","（医療機関名）",{KR["fname"]})&IF({KR["faddr"]}="","",CHAR(10)&"　　　　"&{KR["faddr"]})&CHAR(10)&"　　　　電話 "&{KR["ftel"]}&IF({KR["ffax"]}="","","　FAX "&{KR["ffax"]})&CHAR(10)&"　　　　医師 "&{P["by"]}'
      f'&CHAR(10)&CHAR(10)&"患者：（氏名）　"&{P["age"]}&"歳　"&{P["sex"]}&"　（生年月日）　当院ID："&{P["id"]}'
      f'&CHAR(10)&CHAR(10)&"傷病名："&CHAR(10)&"　"&IF({KR["dx"]}="",{dxauto},{KR["dx"]})&IF({P["dx"]}="","",CHAR(10)&"　（基礎疾患）"&{P["dx"]})&CHAR(10)&"紹介目的："&{KR["purpose"]}'
      f'&CHAR(10)&CHAR(10)&"拝啓　平素より大変お世話になっております。"&CHAR(10)&"当院に"&IF({P["adm"]}="","入院中",{P["adm"]}&"中")&"の患者様について、ご紹介申し上げます。"'
      f'&CHAR(10)&CHAR(10)&"【経過】"&CHAR(10)&{Mq("$Y$19")}'
      f'&CHAR(10)&CHAR(10)&"【バイタルの推移】"&CHAR(10)&{Mq("$Y$13")}'
      f'&IF({Mq("$Y$3")}&{P["img"]}="","",CHAR(10)&CHAR(10)&"【検査所見】"&CHAR(10)&_xlfn.TEXTJOIN(CHAR(10),TRUE,{Mq("$Y$3")},{P["img"]}))'
      f'&IF({P["acts"]}="","",CHAR(10)&CHAR(10)&"【当院での処置】"&CHAR(10)&{P["acts"]})'
      f'&CHAR(10)&CHAR(10)&"【既往歴・身体の状態】"&CHAR(10)&IF({P["st"]}="","特記なし",{P["st"]})&IF({P["base"]}="","",CHAR(10)&"普段の状態："&{P["base"]})'
      f'&CHAR(10)&CHAR(10)&"【精神科的な情報】"&CHAR(10)&"診断："&{P["dx"]}&IF({P["adm"]}="","","（"&{P["adm"]}&"）")&IF({P["psy"]}="","",CHAR(10)&"留意点："&{P["psy"]})'
      f'&CHAR(10)&CHAR(10)&"【現在の処方】"&CHAR(10)&IF({P["medsText"]}="","別紙のとおり",{P["medsText"]})'
      f'&CHAR(10)&CHAR(10)&"【ご本人・ご家族の意向】"&CHAR(10)&_xlfn.TEXTJOIN("。",TRUE,{P["cpr"]},{P["wish"]})&IF({P["kp"]}="","",CHAR(10)&"キーパーソン："&{P["kp"]})'
      f'&IF({P["family"]}&{KR["extra"]}="","",CHAR(10)&CHAR(10)&"【連絡事項】"&CHAR(10)&_xlfn.TEXTJOIN(CHAR(10),TRUE,{P["family"]},{KR["extra"]}))'
      f'&CHAR(10)&CHAR(10)&"お忙しいところ恐縮ですが、ご高診のほどよろしくお願い申し上げます。"&CHAR(10)&"　　　　　　　　　　　　　　　　　　　　　　　　敬具"'
      f'&CHAR(10)&CHAR(10)&"（精神症状や入院形態に関するご質問、加療後の受け入れについては、当院までご連絡ください）"')
out(K, f'B{r}', lt, bold=False); K.row_dimensions[r].height = 600
r += 1; K.cell(r, 2, '傷病名と経過は入力内容から自動で作った文案です。送る前に必ず読み直してください。').font = ft(size=8, color='596579')

# ================= 使い方 =================
setw(USE, {'A': 3, 'B': 24, 'C': 70})
USE['B1'] = '精神科病棟 身体急変サポート（Excel版）'; USE['B1'].font = ft(size=16, bold=True, color=ACC)
rows = [('使い方', None), ('1. 急変シート', '時間帯（日中・夜間）、患者の背景・意向、ハイリスクの薬（✓）、バイタルを入力します。NEWS2は自動で計算されます。'),
 ('2. 症候のシート', '該当する症候のシートを開き、確認事項・レッドフラッグ・搬送相談・院内継続の条件にA列で✓を付けます。夜間は「夜間の判断」も確認します。'),
 ('3. 判定', '急変シートの上部に「すぐに搬送を検討／搬送・転院を相談／院内で治療を続けて再評価」と、その理由が表示されます。'),
 ('4. 報告・転院', '急変シートの下部の「SBAR報告」「診療情報提供」のセルをコピーして使います。前後に " が付いたら削除してください。'),
 ('セルの色', None), ('黄色', '入力するセル（▼が出るセルはリストから選択）'), ('水色', '自動計算（上書きしない）'),
 ('入力の例', None), ('バイタル', '時刻 11/23 21:10、呼吸数 22、SpO2 93、酸素「空気」、収縮期 128、心拍 104、体温 38.4、意識「A 清明（普段どおり）」→ NEWS2 6点'),
 ('施設の設定', '急変シートの「時間帯と施設の設定」で、日中・夜間にできる検査を✓で切り替えられます（初期値：夜間は簡易検査のみ）。'),
 ('運用', '事例ごとに「名前を付けて保存」で複製して使います。氏名は入れず院内の管理IDを使ってください。'),
 ('注意', 'NEWS2は英国王立内科医協会の基準に基づきます。症候ごとの内容は一般的な知見の要約で、施設の手順・ガイドライン・医師の診察に代わるものではありません。最終判断は診察した医師が行ってください。'),
 ('動作環境', 'Excel 2019 以降または Microsoft 365')]
r = 3
for a, b in rows:
    if b is None:
        c = USE.cell(r, 2, a); c.font = ft(bold=True, color='FFFFFF'); c.fill = F_HEAD; USE.cell(r, 3).fill = F_HEAD
    else:
        USE.cell(r, 2, a).font = ft(bold=True); t = USE.cell(r, 3, b); t.font = ft(); t.alignment = WRAP
        if a == '黄色': USE.cell(r, 2).fill = F_IN
        if a == '水色': USE.cell(r, 2).fill = F_OUT
        USE.row_dimensions[r].height = max(18, 15 * (1 + len(b) // 46))
    r += 1
r += 1; USE.cell(r, 2, 'シート一覧').font = ft(bold=True, color=ACC); r += 1
for n in [MAIN, '紹介状'] + [SHORT[s['k']] for s in D['SYMS']]:
    c = USE.cell(r, 2, n); c.hyperlink = f"#'{n}'!A1"; c.font = ft(color=ACC, underline='single'); r += 1

LIST.sheet_state = 'hidden'
wb._sheets = [USE, M, wb['紹介状']] + [wb[SHORT[s['k']]] for s in D['SYMS']] + [LIST]
wb.active = 1
os.makedirs(os.path.dirname(OUT), exist_ok=True)
wb.save(OUT); print('saved', OUT)
