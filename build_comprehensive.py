#!/usr/bin/env python3
"""
Build a comprehensive LaTeX document for each subject that has a tex/ folder.

Strategy: Use a curated per-subject preamble (superset of all packages and macros
used in that subject's lectures), extract the document body from each lecture .tex,
and assemble into one comprehensive document.
"""

import os
import re
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

SUBJECT_FULL_NAMES = {
    "AMR": "Autonomous and Mobile Robotics",
    "EAI": "Embodied AI",
    "NN":  "Neural Networks",
    "RL":  "Reinforcement Learning",
}

SKIP_FILES = {"lecture03_notes.tex"}

AUTHOR = "Vittorio Cava"
YEAR   = "A.Y.~2026/27"


# ── Per-subject preambles ──────────────────────────────────────────────
# Each preamble is the complete content between \documentclass and \begin{document}.
# Carefully assembled from every lecture file of that subject.

PREAMBLE_AMR = r"""
\usepackage[margin=2.4cm]{geometry}
\usepackage[utf8]{inputenc}
\usepackage[expansion=false]{microtype}
\usepackage{amsmath,amssymb,amsthm}
\usepackage{booktabs,array,enumitem,xcolor,float}
\usepackage{graphicx}
\usepackage{tikz}
\usetikzlibrary{arrows.meta,calc,decorations.markings,angles,quotes,positioning,patterns}
\usepackage{pgfplots}
\pgfplotsset{compat=1.16}
\usepackage[most]{tcolorbox}
\usepackage[colorlinks=true,linkcolor=blue!50!black,urlcolor=blue!50!black]{hyperref}

\setlength{\parskip}{4pt}
\setlength{\parindent}{0pt}

% ---------- macros ----------
\newcommand{\R}{\mathbb{R}}
\newcommand{\W}{\mathcal{W}}
\newcommand{\C}{\mathcal{C}}
\newcommand{\SO}{\mathrm{SO}}
\newcommand{\SE}{\mathrm{SE}}
\newcommand{\Sph}{\mathbb{S}}
\newcommand{\norm}[1]{\lVert #1\rVert}
\newcommand{\pts}[1]{\emph{(notes p.~#1)}}

% TikZ helpers (AMR02)
\newcommand{\photobox}[2]{\fbox{\parbox[c][#1][c]{0.29\linewidth}{\centering
  \color{red!70!black}\textbf{[Blank --- insert image]}\par\scriptsize\color{black}#2}}}
\newcommand{\com}[1]{\begin{scope}[shift={(#1)}]\draw[fill=white,thick] (0,0) circle (0.13);
  \fill (0,0) -- (0.13,0) arc (0:90:0.13) -- cycle;
  \fill (0,0) -- (-0.13,0) arc (180:270:0.13) -- cycle;\end{scope}}
\newcommand{\zmpmark}[1]{\begin{scope}[shift={(#1)}]\draw[red!70!black,very thick]
  (-0.12,-0.12)--(0.12,0.12) (-0.12,0.12)--(0.12,-0.12);\end{scope}}
\newcommand{\fixedwheel}[2]{\begin{scope}[shift={(#1)},rotate=#2]
  \draw[fill=gray!30] (-0.3,-0.07) rectangle (0.3,0.07);\end{scope}}
\newcommand{\orientwheel}[2]{\begin{scope}[shift={(#1)},rotate=#2]
  \draw[pattern=north east lines] (-0.3,-0.07) rectangle (0.3,0.07);
  \fill (0,0) circle (1pt);\end{scope}}
\newcommand{\casterwheel}[2]{\begin{scope}[shift={(#1)},rotate=#2]
  \draw (0,0)--(-0.4,0); \draw[fill=white] (-0.6,-0.06) rectangle (-0.2,0.06);
  \fill (0,0) circle (1.5pt);\end{scope}}
\newcommand{\ghostwheel}[2]{\begin{scope}[shift={(#1)},rotate=#2]
  \draw[dashed,gray] (-0.3,-0.07) rectangle (0.3,0.07);\end{scope}}

% ---------- theorem environments ----------
\theoremstyle{definition}
\newtheorem{definition}{Definition}[section]
\newtheorem{example}[definition]{Example}
\newtheorem{algorithm}[definition]{Algorithm}
\theoremstyle{plain}
\newtheorem{lemma}[definition]{Lemma}
\newtheorem{theorem}[definition]{Theorem}
\newtheorem{proposition}[definition]{Proposition}
\newtheorem{corollary}[definition]{Corollary}

\tcbset{
  thmbox/.style={enhanced,breakable,colback=gray!4,colframe=gray!60!black,
    boxrule=0.6pt,arc=2pt,left=6pt,right=6pt,top=4pt,bottom=4pt}
}
\tcolorboxenvironment{definition}{thmbox}
\tcolorboxenvironment{example}{thmbox}
\tcolorboxenvironment{algorithm}{thmbox}
\tcolorboxenvironment{lemma}{thmbox}
\tcolorboxenvironment{proposition}{thmbox}
\tcolorboxenvironment{theorem}{thmbox}
\tcolorboxenvironment{corollary}{thmbox}

\newtcolorbox{intuition}{enhanced,breakable,colback=blue!5,colframe=blue!55!black,
  fonttitle=\bfseries,title={Intuition},boxrule=0.6pt,arc=2pt,
  left=6pt,right=6pt,top=3pt,bottom=3pt}
"""

PREAMBLE_EAI = r"""
\usepackage[margin=2.4cm]{geometry}
\usepackage[utf8]{inputenc}
\usepackage{amsmath,amssymb,amsthm,mathtools,bm}
\usepackage[protrusion=true,expansion=false]{microtype}
\usepackage{booktabs,array,multirow,colortbl,tabularx,enumitem,float,listings}
\usepackage[dvipsnames]{xcolor}
\usepackage{graphicx}
\usepackage{tikz,pgfplots}
\usetikzlibrary{arrows.meta,calc,positioning,shapes.geometric,decorations.pathreplacing,fit,backgrounds,patterns}
\usepgfplotslibrary{groupplots}
\pgfplotsset{compat=1.16}
\usepackage[most]{tcolorbox}
\usepackage[font=small,labelfont=bf]{caption}
\usepackage[colorlinks=true,linkcolor=blue!50!black,citecolor=blue!50!black,urlcolor=blue!50!black]{hyperref}

\emergencystretch=2em
\setlength{\parskip}{4pt}
\setlength{\parindent}{0pt}

\newcolumntype{L}[1]{>{\raggedright\arraybackslash}p{#1}}
\newcolumntype{Y}{>{\raggedright\arraybackslash}X}

% ---------- macros (EAI02) ----------
\newcommand{\R}{\mathbb{R}}
\newcommand{\E}{\mathbb{E}}
\newcommand{\Sph}{\mathbb{S}}
\newcommand{\M}{\mathcal{M}}
\newcommand{\Surf}{\mathcal{S}}
\newcommand{\K}{\mathbf{K}}
\newcommand{\vx}{\bm{x}}
\newcommand{\vu}{\bm{u}}
\newcommand{\vn}{\bm{n}}
\newcommand{\vq}{\bm{q}}
\newcommand{\vy}{\bm{y}}
\newcommand{\vo}{\bm{o}}
\newcommand{\vd}{\bm{d}}
\newcommand{\va}{\bm{a}}
\newcommand{\vb}{\bm{b}}
\newcommand{\vc}{\bm{c}}
\newcommand{\vmu}{\bm{\mu}}
\newcommand{\vk}{\bm{k}}
\newcommand{\norm}[1]{\lVert #1\rVert}
\newcommand{\abs}[1]{\lvert #1\rvert}
\DeclareMathOperator{\dist}{dist}
\DeclareMathOperator{\clamp}{clamp}
\DeclareMathOperator{\sign}{sign}
\DeclareMathOperator*{\argmin}{arg\,min}
\newcommand{\slides}[1]{\texorpdfstring{\emph{(slides #1)}}{(slides #1)}}
\newcommand{\slr}[1]{\texorpdfstring{\emph{(slides~#1)}}{(slides #1)}}

% ---------- macros (EAI03) ----------
\newcommand{\bx}{\bm{x}}
\newcommand{\bz}{\bm{z}}
\newcommand{\beps}{\bm{\epsilon}}
\newcommand{\pv}{\mathbf{p}}
\newcommand{\xt}{\tilde{\mathbf{x}}}
\newcommand{\Rot}{\mathbf{R}}
\newcommand{\tv}{\mathbf{t}}
\newcommand{\AbsRel}{\mathrm{AbsRel}}
\newcommand{\Kinv}{\bm K^{-1}}

\newcommand{\photo}[3][2.8cm]{%
  \begin{center}\begin{tikzpicture}
  \node[draw,dashed,thick,fill=gray!8,minimum height=#1,text width=0.8\linewidth,align=center]
    {\textbf{[PHOTO PLACEHOLDER]}\\ Insert the image from \textbf{slide #2}:\\ \emph{#3}};
  \end{tikzpicture}\end{center}}
\newcommand{\phimg}[4]{%
\begin{tikzpicture}
\node[draw=black!50,dashed,fill=black!5,minimum height=#3,minimum width=#4,
      text width=\dimexpr#4-1cm\relax,align=center,inner sep=6pt]
{\textbf{IMAGE PLACEHOLDER}\\[2pt]Insert the picture from \textbf{slide #1}\\[2pt]{\small\itshape #2}};
\end{tikzpicture}}

\tikzset{box/.style={draw,rounded corners=2pt,align=center,minimum height=0.8cm,fill=blue!8,inner sep=3pt,font=\small},
  frozen/.style={box,fill=pink!40},
  arr/.style={-{Stealth[length=2mm]},thick}}

% ---------- theorem environments ----------
\theoremstyle{definition}
\newtheorem{definition}{Definition}[section]
\newtheorem{example}[definition]{Example}
\newtheorem{algorithm}[definition]{Algorithm}
\theoremstyle{plain}
\newtheorem{theorem}[definition]{Theorem}
\newtheorem{lemma}[definition]{Lemma}
\newtheorem{proposition}[definition]{Proposition}
\newtheorem{corollary}[definition]{Corollary}
\theoremstyle{remark}
\newtheorem{remark}[definition]{Remark}

\tcbset{thmbox/.style={enhanced,breakable,boxrule=0.6pt,arc=2pt,left=6pt,right=6pt,top=4pt,bottom=4pt,before skip=9pt,after skip=9pt}}
\tcolorboxenvironment{definition}{thmbox,colback=green!4!white,colframe=green!45!black}
\tcolorboxenvironment{example}{thmbox,colback=gray!7!white,colframe=gray!60!black}
\tcolorboxenvironment{algorithm}{thmbox,colback=teal!5!white,colframe=teal!55!black}
\tcolorboxenvironment{theorem}{thmbox,colback=orange!6!white,colframe=orange!70!black}
\tcolorboxenvironment{lemma}{thmbox,colback=orange!6!white,colframe=orange!70!black}
\tcolorboxenvironment{proposition}{thmbox,colback=orange!6!white,colframe=orange!70!black}
\tcolorboxenvironment{corollary}{thmbox,colback=orange!6!white,colframe=orange!70!black}
\tcolorboxenvironment{remark}{thmbox,colback=white,colframe=gray!45}

\newtcolorbox{intuition}{enhanced,breakable,colback=blue!5!white,colframe=blue!60!black,coltitle=white,
  colbacktitle=blue!60!black,fonttitle=\bfseries,title=Intuition,
  boxrule=0.6pt,arc=2pt,left=6pt,right=6pt,top=4pt,bottom=4pt,before skip=9pt,after skip=12pt}

\lstset{basicstyle=\ttfamily\small,language=Python,frame=none,backgroundcolor=\color{gray!8},
  breaklines=true,columns=fullflexible,keepspaces=true,showstringspaces=false,
  commentstyle=\color{green!40!black},keywordstyle=\color{blue!70!black},aboveskip=8pt,belowskip=8pt}

\pgfplotsset{every axis/.append style={width=0.86\linewidth,height=6.2cm,grid=major,
  grid style={gray!25},legend style={font=\small},label style={font=\small},tick label style={font=\small}}}

% ---------- boxed environments (EAI04) ----------
\newtheorem{algorithmx}[definition]{Algorithm}
\newcommand{\newboxedthm}[3]{%
  \NewDocumentEnvironment{#1}{o}{%
    \begin{tcolorbox}[enhanced,breakable,boxrule=0.6pt,arc=2pt,colframe=#3!65!black,colback=#3!5]%
    \IfNoValueTF{##1}{\begin{#2}}{\begin{#2}[##1]}}{%
    \end{#2}\end{tcolorbox}}}
\newboxedthm{Definition}{definition}{gray}
\newboxedthm{Lemma}{lemma}{orange}
\newboxedthm{Theorem}{theorem}{red}
\newboxedthm{Proposition}{proposition}{teal}
\newboxedthm{Corollary}{corollary}{purple}
\newboxedthm{Example}{example}{olive}
\newboxedthm{Algorithm}{algorithmx}{brown}
"""

PREAMBLE_NN = r"""
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern}
\usepackage[margin=2.4cm]{geometry}
\usepackage{amsmath,amssymb,amsthm,mathtools}
\usepackage{booktabs,array,enumitem,microtype}
\usepackage{graphicx}
\usepackage{tikz,pgfplots}
\pgfplotsset{compat=1.16}
\usetikzlibrary{arrows.meta,positioning,calc,shapes.geometric,fit,decorations.pathreplacing}
\usepackage[most]{tcolorbox}
\usepackage[hidelinks]{hyperref}

\setlist{itemsep=2pt,topsep=4pt}
\setlength{\parindent}{0pt}
\setlength{\parskip}{5pt}

% ---------- macros ----------
\newcommand{\R}{\mathbb{R}}
\newcommand{\C}{\mathbb{C}}
\newcommand{\K}{\mathbb{K}}
\newcommand{\T}{^{\mathsf{T}}}
\newcommand{\Her}{^{\mathsf{H}}}
\newcommand{\pinv}{^{\#}}
\newcommand{\tr}{\operatorname{tr}}
\newcommand{\diag}{\operatorname{diag}}
\newcommand{\vecop}{\operatorname{vec}}
\newcommand{\rank}{\operatorname{rank}}
\newcommand{\ReLU}{\operatorname{ReLU}}
\newcommand{\ind}[1]{\mathbb{1}\!\left[#1\right]}
\newcommand{\slides}[1]{\texorpdfstring{\emph{(slides #1)}}{(slides #1)}}
\newcommand{\Had}{\circ}

% ---------- theorem-like environments ----------
\theoremstyle{definition}
\newtheorem{definition}{Definition}[section]
\newtheorem{example}[definition]{Example}
\newtheorem{algorithm}[definition]{Algorithm}
\newtheorem{remark}[definition]{Remark}
\theoremstyle{plain}
\newtheorem{theorem}[definition]{Theorem}
\newtheorem{lemma}[definition]{Lemma}
\newtheorem{proposition}[definition]{Proposition}
\newtheorem{corollary}[definition]{Corollary}

\tcbset{thmbox/.style={enhanced,breakable,colback=white,colframe=#1,boxrule=0.6pt,arc=2pt,
  left=6pt,right=6pt,top=3pt,bottom=3pt,before skip=9pt,after skip=9pt}}
\tcolorboxenvironment{definition}{thmbox=black!70}
\tcolorboxenvironment{theorem}{thmbox=red!60!black}
\tcolorboxenvironment{lemma}{thmbox=red!45!black}
\tcolorboxenvironment{proposition}{thmbox=red!45!black}
\tcolorboxenvironment{corollary}{thmbox=red!45!black}
\tcolorboxenvironment{example}{thmbox=green!45!black}
\tcolorboxenvironment{algorithm}{thmbox=violet!70!black}
\tcolorboxenvironment{remark}{thmbox=gray!70}

\newtcolorbox{intuition}{enhanced,breakable,colback=blue!5!white,colframe=blue!60!black,
  coltitle=white,colbacktitle=blue!60!black,fonttitle=\bfseries\small,title=Intuition,
  boxrule=0.6pt,arc=2pt,left=6pt,right=6pt,top=3pt,bottom=3pt,before skip=8pt,after skip=12pt}
"""

PREAMBLE_RL = r"""
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage[margin=2.4cm]{geometry}
\usepackage{amsmath,amssymb,amsthm,mathtools,bm}
\usepackage{xcolor}
\usepackage{booktabs,array,enumitem}
\usepackage{microtype}
\usepackage{graphicx}
\usepackage{tikz}
\usetikzlibrary{arrows.meta,positioning,calc,shapes.geometric,shapes.misc,fit,backgrounds,decorations.pathreplacing}
\usepackage{pgfplots}
\usepackage{float}
\usepgfplotslibrary{groupplots,fillbetween}
\pgfplotsset{compat=1.16}
\usepackage[most]{tcolorbox}
\usepackage[labelfont=bf,font=small]{caption}
\usepackage[colorlinks=true,linkcolor=blue!50!black,urlcolor=blue!50!black,citecolor=blue!50!black]{hyperref}

\emergencystretch=2em
\setlist[itemize]{itemsep=2pt,topsep=3pt}
\setlist[enumerate]{itemsep=2pt,topsep=3pt}
\setlength{\parskip}{4pt}
\setlength{\parindent}{0pt}

% ---------- macros ----------
\newcommand{\E}{\mathbb{E}}
\newcommand{\Prob}{\mathbb{P}}
\newcommand{\PP}{\mathbb{P}}
\newcommand{\Reg}{\mathrm{Regret}}
\newcommand{\Unif}{\mathrm{Unif}}
\newcommand{\ind}{\mathbf{1}}
\newcommand{\rh}{\hat{\mathbf{r}}}
\newcommand{\calA}{\mathcal{A}}
\newcommand{\calX}{\mathcal{X}}
\newcommand{\Norm}{\mathcal{N}}
\DeclareMathOperator*{\argmax}{arg\,max}
\DeclareMathOperator{\Var}{Var}
\newcommand{\slides}[1]{\emph{(slides #1)}}
\newcommand{\slr}[1]{\texorpdfstring{\emph{(slides #1)}}{(slides #1)}}
\newcommand{\cS}{\mathcal{S}}
\newcommand{\cA}{\mathcal{A}}
\newcommand{\Rmax}{R_{\max}}

\newcommand{\slideplaceholder}[3][3.6cm]{%
  \begin{center}\begin{tikzpicture}
  \node[draw=gray,dashed,thick,fill=gray!6,minimum width=0.82\linewidth,minimum height=#1,
        align=center,text=gray!60!black,text width=0.74\linewidth]
        {\textbf{[Insert figure from slide #2]}\\[2pt]\small #3};
  \end{tikzpicture}\end{center}}

% ---------- theorem environments ----------
\theoremstyle{plain}
\newtheorem{theorem}{Theorem}[section]
\newtheorem{lemma}[theorem]{Lemma}
\newtheorem{proposition}[theorem]{Proposition}
\newtheorem{corollary}[theorem]{Corollary}
\theoremstyle{definition}
\newtheorem{definition}[theorem]{Definition}
\newtheorem{example}[theorem]{Example}
\newtheorem{algorithm}[theorem]{Algorithm}
\theoremstyle{remark}
\newtheorem*{remark}{Remark}

\tcbset{thmbox/.style={enhanced,breakable,boxrule=0.6pt,arc=2pt,left=7pt,right=7pt,top=4pt,bottom=4pt,
  before skip=9pt,after skip=9pt}}
\tcolorboxenvironment{theorem}{thmbox,colback=red!3,colframe=red!55!black}
\tcolorboxenvironment{lemma}{thmbox,colback=orange!4,colframe=orange!70!black}
\tcolorboxenvironment{proposition}{thmbox,colback=teal!4,colframe=teal!60!black}
\tcolorboxenvironment{corollary}{thmbox,colback=magenta!3,colframe=magenta!50!black}
\tcolorboxenvironment{definition}{thmbox,colback=black!3,colframe=black!60}
\tcolorboxenvironment{example}{thmbox,colback=yellow!7,colframe=yellow!45!black}
\tcolorboxenvironment{algorithm}{thmbox,colback=violet!4,colframe=violet!60!black}

\newtcolorbox{intuition}[1][]{enhanced,breakable,colback=blue!4,colframe=blue!55!black,
  coltitle=white,fonttitle=\bfseries\small,title={Intuition #1},boxrule=0.6pt,arc=3pt,
  left=7pt,right=7pt,top=3pt,bottom=3pt,before skip=9pt,after skip=11pt,
  attach boxed title to top left={yshift=-2mm,xshift=4mm},boxed title style={colback=blue!55!black,arc=2pt}}
"""

PREAMBLES = {
    "AMR": PREAMBLE_AMR,
    "EAI": PREAMBLE_EAI,
    "NN":  PREAMBLE_NN,
    "RL":  PREAMBLE_RL,
}


# ── Helpers ────────────────────────────────────────────────────────────────

def find_subjects_with_tex(base: Path) -> list[str]:
    subjects = []
    for entry in sorted(base.iterdir()):
        if entry.is_dir() and (entry / "tex").is_dir():
            subjects.append(entry.name)
    return subjects


def collect_tex_files(subject_dir: Path) -> list[Path]:
    tex_dir = subject_dir / "tex"
    files = []
    for f in sorted(tex_dir.rglob("*.tex")):
        if f.name not in SKIP_FILES:
            files.append(f)
    return files


def extract_body(tex_path: Path) -> str:
    """Extract content between \\begin{document} and \\end{document}."""
    content = tex_path.read_text(encoding="utf-8", errors="replace")
    
    m_begin = re.search(r'\\begin\{document\}', content)
    m_end   = re.search(r'\\end\{document\}', content)
    
    if not m_begin or not m_end:
        return content
    
    body = content[m_begin.end():m_end.start()].strip()
    
    # Remove \maketitle, \title{...}, \author{...}, \date{...}, \tableofcontents
    body = re.sub(r'\\maketitle\b', '', body)
    body = re.sub(r'\\tableofcontents\b', '', body)
    body = remove_braced_command(body, 'title')
    body = remove_braced_command(body, 'author')
    body = remove_braced_command(body, 'date')
    
    # Remove leading \bigskip
    body = re.sub(r'^\s*\\bigskip\s*', '\n', body)

    # Combined documents are compiled from the subject's tex/ directory, but
    # EAI source files refer to figures from the repository root.
    body = re.sub(r'(?<=\{)tex/EAI0[234]/', '', body)

    return body.strip()


def remove_braced_command(text: str, cmd: str) -> str:
    """Remove \\cmd{...} handling nested braces, repeated as needed."""
    while True:
        m = re.search(r'\\' + cmd + r'\s*\{', text)
        if not m:
            break
        start = m.start()
        brace_pos = m.end() - 1
        depth = 1
        pos = brace_pos + 1
        while pos < len(text) and depth > 0:
            if text[pos] == '{':
                depth += 1
            elif text[pos] == '}':
                depth -= 1
            pos += 1
        text = text[:start] + text[pos:]
    return text


def get_lecture_label(tex_path: Path) -> str:
    name = tex_path.stem
    m = re.search(r'(\d+)(?:_(\d+))?$', name)
    if m:
        num = m.group(1).lstrip('0') or '0'
        sub = m.group(2)
        if sub:
            return f"Lecture {num} -- Part {sub}"
        return f"Lecture {num}"
    return name


def build_document(subject: str, tex_files: list[Path], output_dir: Path) -> Path:
    full_name = SUBJECT_FULL_NAMES.get(subject, subject)
    preamble  = PREAMBLES.get(subject, PREAMBLE_NN)  # fallback
    
    # Build graphicspath
    image_dirs = []
    seen_dirs = set()
    for tf in tex_files:
        d = str(tf.parent) + "/"
        if d not in seen_dirs:
            seen_dirs.add(d)
            image_dirs.append(d)
    graphicspath = "".join(f"{{{d}}}" for d in image_dirs)
    
    lines = []
    lines.append("\\documentclass[11pt,a4paper]{article}")
    lines.append(preamble)
    lines.append(f"\\graphicspath{{{graphicspath}}}")
    lines.append("")
    lines.append(f"\\title{{\\textbf{{{full_name}}}\\\\[6pt]\\large Comprehensive Lecture Notes}}")
    lines.append(f"\\author{{{AUTHOR}}}")
    lines.append(f"\\date{{{YEAR}}}")
    lines.append("")
    lines.append("\\begin{document}")
    lines.append("\\maketitle")
    lines.append("\\tableofcontents")
    lines.append("\\newpage")
    
    for i, tf in enumerate(tex_files):
        label = get_lecture_label(tf)
        body = extract_body(tf)
        
        lines.append("")
        lines.append(f"% {'='*70}")
        lines.append(f"% {label}")
        lines.append(f"% {'='*70}")
        lines.append(f"\\part{{{label}}}")
        lines.append("")
        lines.append(body)
        
        if i < len(tex_files) - 1:
            lines.append("")
            lines.append("\\newpage")
    
    lines.append("")
    lines.append("\\end{document}")
    
    content = "\n".join(lines)
    main_tex = output_dir / f"{subject}.tex"
    main_tex.write_text(content, encoding="utf-8")
    print(f"  ✓ Written {main_tex}")
    return main_tex


def compile_tex(tex_path: Path) -> bool:
    cwd = tex_path.parent
    cmd = ["pdflatex", "-interaction=nonstopmode", "-file-line-error", tex_path.name]
    
    for pass_num in (1, 2):
        print(f"  ⏳ pdflatex pass {pass_num}...")
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            print(f"  ⚠ pdflatex pass {pass_num} exited with code {result.returncode}")
            # Show actual errors
            for line in result.stdout.split('\n'):
                if line.startswith('!'):
                    print(f"    {line}")
            # Don't abort - some warnings cause non-zero exit but PDF is still produced
    
    pdf_path = tex_path.with_suffix('.pdf')
    if pdf_path.exists():
        size_mb = pdf_path.stat().st_size / (1024 * 1024)
        print(f"  ✓ Compiled {pdf_path.name} ({size_mb:.1f} MB)")
        return True
    else:
        print(f"  ✗ PDF not found!")
        # Print full log tail for debugging
        log_path = tex_path.with_suffix('.log')
        if log_path.exists():
            log_text = log_path.read_text(errors='replace')
            error_lines = [l for l in log_text.split('\n') if l.startswith('!')]
            for el in error_lines[:20]:
                print(f"    {el}")
        return False


def main():
    subjects = find_subjects_with_tex(BASE_DIR)
    print(f"Found subjects with tex/ folders: {subjects}\n")
    
    results = {}
    for subject in subjects:
        print(f"━━━ {subject} ({SUBJECT_FULL_NAMES.get(subject, subject)}) ━━━")
        subject_dir = BASE_DIR / subject
        tex_files = collect_tex_files(subject_dir)
        
        if not tex_files:
            print(f"  ⚠ No .tex files found, skipping")
            continue
        
        # Skip the main file itself from previous runs
        tex_files = [f for f in tex_files if f.name != f"{subject}.tex"]
        print(f"  Lecture files: {[f.name for f in tex_files]}")
        
        output_dir = subject_dir / "tex"
        main_tex = build_document(subject, tex_files, output_dir)
        success = compile_tex(main_tex)
        results[subject] = success
        print()
    
    print("━━━ Summary ━━━")
    for subject, success in results.items():
        status = "✓" if success else "✗"
        name = SUBJECT_FULL_NAMES.get(subject, subject)
        print(f"  {status} {name} → {subject}/tex/{subject}.pdf")


if __name__ == "__main__":
    main()
