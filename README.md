# GS-1000 계산기

브라운 계산기에서 영감을 받은 디자인의 계산기 프로젝트입니다.
사칙연산에 퍼센트 자동 판단, `=` 반복 계산, 그리고 x²·√·1/x·^·ln·log·π·e 공학용 기능을 갖추고 있습니다.

| 파일 | 설명 |
|---|---|
| `calculator.py` | 파이썬(tkinter) 계산기 — 공학용 기능 포함, `--test` 자체 검증 내장 |
| `calculator.html` | 브라우저용 계산기 — 설치 없이 더블클릭으로 실행 |
| `.vscode/` | VS Code 실행·디버그 설정과 확장 추천 |
| `requirements.txt` | exe 빌드에 쓰는 도구(PyInstaller) 목록 |

## VS Code에서 실행하기

1. VS Code에서 이 폴더 열기 — **파일 > 폴더 열기** (또는 탐색기에서 폴더 우클릭 > Code로 열기)
2. 오른쪽 아래 추천 확장 알림이 뜨면 **Python** 확장 설치
3. `calculator.py` 를 열고 오른쪽 위 **▶**(또는 `F5`)로 실행 — `F5` 누르면 "계산기 실행 (GUI)" / "계산기 로직 테스트" 중 선택할 수 있습니다
4. 터미널에서 직접: `python calculator.py --test` (계산 로직 28건 자동 검증)

## exe 파일로 만들기

```powershell
python -m pip install pyinstaller
python -m PyInstaller --onefile --windowed --name Calculator calculator.py
# 완성 파일: dist/Calculator.exe
```

## Git & GitHub에 올리기

### 방법 1 — VS Code 화면에서 (권장)

1. 왼쪽 **소스 제어(Source Control)** 아이콘 클릭 → **리포지토리 초기화(Initialize Repository)** 클릭
2. 변경 파일 목록에서 **+(모두 스테이징)** → 위쪽 입력창에 커밋 메시지(예: `첫 커밋: GS-1000 계산기`) 입력 → **커밋**
3. **분치 게시(Publish Branch)** 버튼 클릭 → 브라우저로 GitHub 로그인 → 저장소 이름 확인 → **GitHub에 저장소가 자동 생성되고 업로드됩니다**

### 방법 2 — 명령줄에서

처음 1회만 본인 정보 등록:

```bash
git config --global user.name "본인 이름"
git config --global user.email "본인 GitHub 이메일"
```

업로드:

```bash
git init -b main
git add .
git commit -m "첫 커밋: GS-1000 계산기"
git remote add origin https://github.com/<본인아이디>/calculator.git
git push -u origin main
```

> GitHub 저장소는 github.com 로그인 > **New repository** > 이름 `calculator`, 공개/비공개 선택 > 생성(README 추가 **안 함**)으로 미리 만들어 두면 됩니다.
> 방법 1의 "Publish Branch"는 이 과정을 버튼 한 번으로 대신 해 줍니다.

## 문제 해결

- `python` 명령이 먹지 않음 → python.org 설치 시 **"Add python.exe to PATH"** 체크, 또는 `py calculator.py` 로 실행
- `pip` 이 인식 안 됨 → `python -m pip install ...` 형태로 실행
- 첫 exe 실행 시 "Windows가 PC를 보호했습니다" → **추가 정보 > 실행** (서명 없는 프로그램의 정상 안내)
- VS Code에서 파이썬을 못 찾음 → `Ctrl+Shift+P` > "Python: Select Interpreter" > 설치된 Python 3.x 선택
