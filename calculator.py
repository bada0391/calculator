#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GS-1000 계산기 — 파이썬(tkinter) 버전.

브라우저용 계산기(계산기.html)와 같은 계산 규칙을 담았습니다:
  · 왼쪽부터 차례대로 계산      12 + 7 × 3 = 57
  · = 을 다시 누르면 마지막 연산 반복   7 × = = → 343
  · 퍼센트 자동 판단     200 + 10 % = 220,  200 × 10 % = 20
  · 부동소수점 오차 정리   0.1 + 0.2 = 0.3
  · 0으로 나누면 '오류' 상태 — AC로 재시작

공학용 기능:  x²  √  1/x  ^(거듭제곱)  ln  log  π  e

실행:   python3 calculator.py
테스트: python3 calculator.py --test
키보드: 숫자, + - * / ^ , Enter(=), Esc(AC), Backspace(한 자 지우기)
"""
import math
import re
import sys

SYMBOLS = {'+': '+', '-': '−', '*': '×', '/': '÷', '^': '^'}

# ── 계산 로직 (GUI와 분리된 순수 함수) ──────────────────────────────────

def fresh():
    return {'a': None, 'op': None, 'cur': '0', 'overwrite': False,
            'err': False, 'justEq': False, 'lastOp': None, 'lastB': None,
            'expr': ''}


def err_state():
    return {'a': None, 'op': None, 'cur': '0', 'overwrite': True,
            'err': True, 'justEq': False, 'lastOp': None, 'lastB': None,
            'expr': ''}


def num(s):
    try:
        return float(s)
    except ValueError:
        return 0.0


def san(x):
    """표시 오차 정리 — 소수점 12자리 유의숫자로 반올림 (0.1+0.2 → 0.3)."""
    return float(f'{x:.12g}')


def compute(a, op, b):
    try:
        if op == '+':
            r = a + b
        elif op == '-':
            r = a - b
        elif op == '*':
            r = a * b
        elif op == '/':
            r = math.nan if b == 0 else a / b
        elif op == '^':                       # 거듭제곱 (x의 y제곱)
            r = math.pow(a, b)
        else:
            r = math.nan
    except (ValueError, OverflowError, ZeroDivisionError):
        return math.nan                       # 정의되지 않음/범위 초과 → 오류 상태
    return san(r)


def _norm_exp(m, e):
    """1.230000e+05 → 1.23e+5 처럼 지수 표기를 정리."""
    if '.' in m:
        m = m.rstrip('0').rstrip('.')
    sign = e[0]
    digits = e[1:].lstrip('0') or '0'
    return f'{m}e{sign}{digits}'


def fmt(x):
    """숫자 → 화면용 문자열. 표시할 수 없으면 None (오류 처리)."""
    if x is None or not math.isfinite(x):
        return None
    if x != 0 and (abs(x) >= 1e15 or abs(x) < 1e-7):
        m, e = f'{x:.6e}'.split('e')
        return _norm_exp(m, e)
    v = san(x)
    r = repr(v)
    if 'e' in r:
        m, e = r.split('e')
        return _norm_exp(m, e)
    if v == int(v) and abs(v) < 1e15:
        return str(int(v))
    return r


def group(s):
    """세 자리마다 콤마 (지수 표기는 그대로)."""
    if s is None or re.search(r'[eE]', s):
        return s
    parts = s.split('.')
    head, tail = parts[0], parts[1] if len(parts) > 1 else None
    neg = head.startswith('-')
    if neg:
        head = head[1:]
    if len(head) > 14:      # 직접 입력 가능한 최대 14자리 초과(π, e 등) → 콤마 생략
        return s
    head = re.sub(r'\B(?=(\d{3})+(?!\d))', ',', head)
    return ('-' if neg else '') + head + ('.' + tail if tail is not None else '')


def apply_key(st, key):
    """한 개의 키를 상태에 적용해 새 상태를 돌려줍니다."""
    s = dict(st)

    if key == 'AC':
        return fresh()
    if s['err']:
        return s

    # ── 숫자 입력 ────────────────────────────────────────────────
    if len(key) == 1 and key.isdigit():
        if s['justEq']:                       # = 직후 숫자 → 새 계산 시작
            s['a'] = None; s['op'] = None; s['expr'] = ''; s['justEq'] = False
        if s['overwrite']:
            s['cur'] = key; s['overwrite'] = False
        else:
            digits = len(s['cur'].replace('-', '').replace('.', ''))
            if digits >= 14:                  # 화면에 들어가는 최대 14자리
                return s
            if s['cur'] == '0':
                s['cur'] = key
            elif s['cur'] == '-0':
                s['cur'] = '-' + key
            else:
                s['cur'] += key
        return s

    if key == '.':
        if s['justEq']:
            s['a'] = None; s['op'] = None; s['expr'] = ''
            s['justEq'] = False; s['cur'] = '0.'; s['overwrite'] = False
            return s
        if s['overwrite']:
            s['cur'] = '0.'; s['overwrite'] = False
            return s
        if '.' not in s['cur']:
            s['cur'] += '.'
        return s

    if key == '±':
        if s['cur'] in ('0', '0.'):
            return s
        if re.search(r'[eE]', s['cur']):
            f = fmt(-num(s['cur']))
            if f is not None:
                s['cur'] = f
            return s
        s['cur'] = s['cur'][1:] if s['cur'].startswith('-') else '-' + s['cur']
        return s

    if key == '%':
        if s['overwrite'] and not s['justEq']:   # %% 중복 적용 방지
            return s
        c = num(s['cur'])
        # 200 + 10 % 는 200의 10% 를 더하는 것으로 계산
        if s['op'] in ('+', '-'):
            r = san(s['a'] * c / 100)
        else:
            r = san(c / 100)
        f = fmt(r)
        if f is None:
            return err_state()
        s['cur'] = f; s['overwrite'] = True
        return s

    if key == '⌫':
        if s['overwrite']:
            return s
        s['cur'] = s['cur'][:-1]
        if s['cur'] in ('', '-', '-0'):
            s['cur'] = '0'
        return s

    # ── 공학용 단항 연산 (x², √, 1/x, ln, log) ───────────────────
    if key in ('sq', 'sqrt', 'inv', 'ln', 'log'):
        s['justEq'] = False
        s['lastOp'] = None; s['lastB'] = None
        c = num(s['cur'])
        try:
            if key == 'sq':
                r = c * c
                label = s['cur'] + '²'
            elif key == 'sqrt':
                if c < 0:
                    return err_state()
                r = math.sqrt(c)
                label = '√(' + s['cur'] + ')'
            elif key == 'inv':
                if c == 0:
                    return err_state()
                r = 1 / c
                label = '1/(' + s['cur'] + ')'
            elif key == 'ln':
                if c <= 0:
                    return err_state()
                r = math.log(c)
                label = 'ln(' + s['cur'] + ')'
            else:                                 # log (상용로그)
                if c <= 0:
                    return err_state()
                r = math.log10(c)
                label = 'log(' + s['cur'] + ')'
        except (ValueError, OverflowError):
            return err_state()
        f = fmt(san(r))
        if f is None:
            return err_state()
        if s['op'] is None:                       # 진행 중 연산이 없을 때만 수식 갱신
            s['expr'] = label
        s['cur'] = f; s['overwrite'] = True
        return s

    if key in ('pi', 'e'):                        # 상수 입력 — 숫자 입력처럼 취급
        if s['justEq']:
            s['a'] = None; s['op'] = None; s['expr'] = ''; s['justEq'] = False
        s['cur'] = repr(math.pi) if key == 'pi' else repr(math.e)
        s['overwrite'] = True
        if s['op'] is None:
            s['expr'] = 'π' if key == 'pi' else 'e'
        return s

    # ── 연산자 ───────────────────────────────────────────────────
    if key in SYMBOLS:
        s['justEq'] = False
        if s['op'] is not None and s['overwrite']:      # 연산자 교체 (9 + - → −)
            s['op'] = key
            s['expr'] = fmt(s['a']) + ' ' + SYMBOLS[key]
            return s
        if s['op'] is not None and s['a'] is not None:  # 연속 계산 (왼쪽부터)
            r = compute(s['a'], s['op'], num(s['cur']))
            f = fmt(r)
            if f is None:
                return err_state()
            s['a'] = r; s['cur'] = f; s['overwrite'] = True; s['op'] = key
            s['expr'] = f + ' ' + SYMBOLS[key]
            return s
        s['a'] = num(s['cur']); s['op'] = key; s['overwrite'] = True
        s['expr'] = fmt(s['a']) + ' ' + SYMBOLS[key]
        return s

    # ── = ────────────────────────────────────────────────────────
    if key == '=':
        if s['op'] is not None and s['a'] is not None:
            b = num(s['cur'])
            r = compute(s['a'], s['op'], b)
            f = fmt(r)
            if f is None:
                return err_state()
            s['expr'] = fmt(s['a']) + ' ' + SYMBOLS[s['op']] + ' ' + fmt(b) + ' ='
            s['lastOp'] = s['op']; s['lastB'] = b
            s['cur'] = f; s['a'] = None; s['op'] = None
            s['overwrite'] = True; s['justEq'] = True
            return s
        if s['lastOp'] is not None:               # = 반복 — 마지막 연산 재적용
            prev = s['cur']
            r = compute(num(prev), s['lastOp'], s['lastB'])
            f = fmt(r)
            if f is None:
                return err_state()
            s['expr'] = prev + ' ' + SYMBOLS[s['lastOp']] + ' ' + fmt(s['lastB']) + ' ='
            s['cur'] = f; s['overwrite'] = True; s['justEq'] = True
            return s
        s['expr'] = s['cur'] + ' ='
        return s

    return s


# ── 자체 테스트 (python3 계산기.py --test) ──────────────────────────────

def _run(keys):
    s = fresh()
    for k in keys:
        s = apply_key(s, k)
    return s


def run_tests():
    cases = [
        ('12 + 7 × 3 (왼쪽부터)',    list('12+7*3='), '57'),
        ('0.1 + 0.2 오차 제거',      list('0.1+0.2='), '0.3'),
        ('5 ÷ 0 오류',              list('5/0='), 'ERR'),
        ('7 × = 부재 피연산자',      list('7*='), '49'),
        ('7 × = = 반복 곱',         list('7*=='), '343'),
        ('5 = = 값 유지',           list('5=='), '5'),
        ('200 + 10 % = 220',       list('200+10%='), '220'),
        ('50 % = 0.5',             list('50%='), '0.5'),
        ('20 % % 중복 방지',        list('20%%'), '0.2'),
        ('백스페이스',              list('12⌫'), '1'),
        ('부호 바꾸기',              list('50±'), '-50'),
        ('음수 소수 입력',           list('2±.5'), '-2.5'),
        ('10 ÷ 4 = 2.5',           list('10/4='), '2.5'),
        ('50 + 10 % 중간값',        list('50+10%'), '5'),
        ('12 + 7 × = 연쇄 후 =',    list('12+7*='), '361'),
        ('9 x² = 81',              ['9', 'sq'], '81'),
        ('√9 = 3',                 ['9', 'sqrt'], '3'),
        ('√ 음수 → 오류',           ['9', '±', 'sqrt'], 'ERR'),
        ('1/x = 0.125',            ['8', 'inv'], '0.125'),
        ('1/0 → 오류',             ['0', 'inv'], 'ERR'),
        ('2 ^ 10 = 1024',          list('2^10='), '1024'),
        ('2^10 = = 반복 거듭제곱',   list('2^10=='), '1.267651e+30'),
        ('음수 밑 비정수 지수 → 오류', list('8±^0.5='), 'ERR'),
        ('π 상수 입력',             ['pi'], '3.141592653589793'),
        ('e 상수 → ln = 1',        ['e', 'ln'], '1'),
        ('log(100) = 2',           ['1', '0', '0', 'log'], '2'),
        ('12 + 3x² = 21',          ['1', '2', '+', '3', 'sq', '='], '21'),
    ]
    fails = 0
    for name, keys, want in cases:
        s = _run(keys)
        got = 'ERR' if s['err'] else s['cur']
        ok = (want == 'ERR' and s['err']) or got == want
        print(('ok   ' if ok else 'FAIL ') + name + ' -> ' + got)
        fails += 0 if ok else 1
    s = _run(list('9+-'))
    ok = s['op'] == '-'
    print(('ok   ' if ok else 'FAIL ') + "연산자 교체 9 + - → −  -> " + str(s['op']))
    fails += 0 if ok else 1
    print('ALL PASS' if fails == 0 else str(fails) + ' FAILED')
    return 0 if fails == 0 else 1


# ── GUI (tkinter — 파이썬 기본 라이브러리) ──────────────────────────────

def run_gui():
    import tkinter as tk

    C = {'bg': '#15171A', 'body': '#E7E1D3',
         'key': '#F7F4ED', 'key_txt': '#26231D',
         'fn': '#DAD4C6', 'fn_txt': '#57524A', 'ac_txt': '#B4472E',
         'op': '#B7BE8F', 'op_txt': '#2E3419',
         'eq': '#DD5B36', 'eq_txt': '#FFF7F1',
         'lcd': '#C9CDB7', 'lcd_txt': '#252A1E', 'lcd_sub': '#6B7060',
         'err': '#9E3A20'}
    MONO = ('Courier New', 10)
    KEY_FONT = ('Helvetica', 15, 'bold')

    root = tk.Tk()
    root.title('GS-1000 계산기')
    root.resizable(False, False)
    root.configure(bg=C['bg'])

    holder = {'state': fresh()}
    expr_var = tk.StringVar(value='')
    val_var = tk.StringVar(value='0')

    body = tk.Frame(root, bg=C['body'], padx=14, pady=12)
    body.pack(padx=20, pady=20)

    disp = tk.Frame(body, bg=C['lcd'], padx=14, pady=8)
    disp.pack(fill='x')
    tk.Label(disp, textvariable=expr_var, anchor='e', font=MONO,
             fg=C['lcd_sub'], bg=C['lcd']).pack(fill='x')
    val_lbl = tk.Label(disp, textvariable=val_var, anchor='e',
                       font=('Courier New', 26, 'bold'),
                       fg=C['lcd_txt'], bg=C['lcd'])
    val_lbl.pack(fill='x')

    grid = tk.Frame(body, bg=C['body'])
    grid.pack(pady=(12, 2))

    # (라벨, 종류) — 라벨은 화면 표시용, 내부 키는 SYMBOBS 기준('/' '*' '-')
    keys = [
        ('x²', 'sci'), ('√', 'sci'), ('1/x', 'sci'), ('^', 'sci'),
        ('π', 'sci'), ('e', 'sci'), ('ln', 'sci'), ('log', 'sci'),
        ('AC', 'fn'), ('±', 'fn'), ('%', 'fn'), ('⌫', 'fn'),
        ('7', 'num'), ('8', 'num'), ('9', 'num'), ('/', 'op'),
        ('4', 'num'), ('5', 'num'), ('6', 'num'), ('*', 'op'),
        ('1', 'num'), ('2', 'num'), ('3', 'num'), ('-', 'op'),
        ('0', 'num'), ('.', 'num'), ('=', 'eq'), ('+', 'op'),
    ]
    DISPLAY = {'/': '÷', '*': '×', '-': '−'}
    ALIAS = {'x²': 'sq', '√': 'sqrt', '1/x': 'inv', 'π': 'pi'}

    def render():
        s = holder['state']
        if s['err']:
            val_lbl.config(fg=C['err'], font=('Courier New', 20, 'bold'))
            val_var.set('오류')
            expr_var.set('0으로 나누거나 숫자 범위를 넘었어요 — AC로 다시 시작')
            return
        g = group(s['cur'])
        n = len(g)
        size = 26 if n <= 9 else (20 if n <= 12 else 16)
        val_lbl.config(fg=C['lcd_txt'], font=('Courier New', size, 'bold'))
        val_var.set(g)
        expr_var.set(s['expr'])

    def press(k):
        holder['state'] = apply_key(holder['state'], k)
        render()

    for i, (label, kind) in enumerate(keys):
        r, c = divmod(i, 4)
        text = DISPLAY.get(label, label)
        if kind == 'num':
            bg, fg, ab = C['key'], C['key_txt'], '#EBE7DC'
        elif kind == 'op':
            bg, fg, ab = C['op'], C['op_txt'], '#A8B07E'
        elif kind == 'eq':
            bg, fg, ab = C['eq'], C['eq_txt'], '#C64F2D'
        elif kind == 'sci':
            bg, fg, ab = '#DCE2E6', '#41505A', '#C6CFD5'
        else:
            bg, fg, ab = C['fn'], C['fn_txt'], '#CBC5B6'
            if label == 'AC':
                fg = C['ac_txt']
        font = ('Helvetica', 13, 'bold') if kind == 'sci' else KEY_FONT
        tk.Button(grid, text=text, font=font, bg=bg, fg=fg,
                  activebackground=ab, activeforeground=fg,
                  relief='flat', bd=0, highlightthickness=0,
                  width=4, pady=10, cursor='hand2',
                  command=lambda k=ALIAS.get(label, label): press(k)
                  ).grid(row=r, column=c, padx=3, pady=3)

    tk.Label(body, text='GS-1000', font=('Helvetica', 8),
             fg='#B8B2A4', bg=C['body']).pack(pady=(6, 0))

    def on_key(event):
        ch, ks = event.char, event.keysym
        if len(ch) == 1 and ch.isdigit():
            press(ch)
        elif ch in ('+', '-', '*', '/', '%', '.', '=', '^'):
            press(ch)
        elif ch in ('x', 'X'):
            press('*')
        elif ch == ',':
            press('.')
        elif ks in ('Return', 'KP_Enter'):
            press('=')
        elif ks in ('Escape', 'Delete'):
            press('AC')
        elif ks == 'BackSpace':
            press('⌫')

    root.bind('<Key>', on_key)
    render()
    root.mainloop()


def main(argv):
    if '--test' in argv:
        return run_tests()
    try:
        run_gui()
    except Exception as e:
        print('GUI를 띄울 수 없습니다(' + e.__class__.__name__ + '). '
              '`python3 calculator.py --test` 로 계산 로직을 검증할 수 있습니다.')
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
