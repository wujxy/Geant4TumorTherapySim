#!/usr/bin/env python3
"""Convert final_report.md into the existing UCAS LaTeX report template."""

from __future__ import annotations

import re
import sys
from pathlib import Path


FIGURE_WIDTHS = {
    "g4tsg_offscreen_zb_png_1.png": "0.90",
    "Q1_body_tumor_xz_section.png": "0.90",
    "Q1_gamma_energy_heatmap_grid.png": "0.88",
    "Q1_proton_energy_heatmap_grid.png": "0.95",
    "Q1_region_dose_comparison.png": "0.82",
    "Q2_geometry_mixed_cell_layout.png": "0.80",
}

WIDE_FIGURES = {
    "F2_forced_capture_quantitative.png": "0.92",
    "F3_forced_capture_singlecell_distribution.png": "0.98",
    "F4_therapy_comparison_projected_maps.png": "0.98",
    "Q2_biased_ppm_projected_maps.png": "0.98",
    "Q2_tumor_depth_projected_maps.png": "0.98",
}


def escape_text(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in text)


def convert_inline(text: str) -> str:
    tokens: list[str] = []

    def protect(value: str) -> str:
        token = f"@@TOKEN{len(tokens)}@@"
        tokens.append(value)
        return token

    text = re.sub(r"`([^`]+)`", lambda m: protect(r"\texttt{" + escape_text(m.group(1)) + "}"), text)
    text = re.sub(r"\$([^$\n]+)\$", lambda m: protect("$" + m.group(1) + "$"), text)
    text = re.sub(
        r"\[([^\]]+)\]\((https?://[^)]+)\)",
        lambda m: protect(r"\href{" + m.group(2).removesuffix("#") + "}{" + convert_inline(m.group(1)) + "}"),
        text,
    )
    text = re.sub(r"<(https?://[^>]+)>", lambda m: protect(r"\url{" + m.group(1) + "}"), text)
    text = re.sub(r"\*\*([^*]+)\*\*", lambda m: protect(r"\textbf{" + convert_inline(m.group(1)) + "}"), text)
    text = re.sub(r"\*([^*]+)\*", lambda m: protect(r"\textit{" + convert_inline(m.group(1)) + "}"), text)
    text = escape_text(text)
    for index, value in enumerate(tokens):
        text = text.replace(f"@@TOKEN{index}@@", value)
    return text


def is_table_separator(line: str) -> bool:
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def convert_table(lines: list[str], start: int) -> tuple[list[str], int]:
    rows: list[list[str]] = []
    index = start
    while index < len(lines) and lines[index].lstrip().startswith("|"):
        if not is_table_separator(lines[index]):
            rows.append([cell.strip() for cell in lines[index].strip().strip("|").split("|")])
        index += 1

    columns = max(len(row) for row in rows)
    spec = " ".join([r">{\raggedright\arraybackslash}X"] * columns)
    output = [
        r"\begin{table}[H]",
        r"    \centering",
        r"    \footnotesize",
        rf"    \begin{{tabularx}}{{\textwidth}}{{{spec}}}",
        r"        \toprule",
    ]
    for row_index, row in enumerate(rows):
        cells = row + [""] * (columns - len(row))
        output.append("        " + " & ".join(convert_inline(cell) for cell in cells) + r" \\")
        if row_index == 0:
            output.append(r"        \midrule")
    output.extend([r"        \bottomrule", r"    \end{tabularx}", r"\end{table}", ""])
    return output, index


def convert_figure(line: str, figure_index: int) -> list[str]:
    match = re.fullmatch(r"!\[([^\]]+)\]\(([^)]+)\)", line.strip())
    if not match:
        raise ValueError(f"Invalid figure line: {line}")
    caption, path = match.groups()
    caption = re.sub(r"^图\s+\d+\s*", "", caption)
    filename = Path(path).name
    width = WIDE_FIGURES.get(filename, FIGURE_WIDTHS.get(filename, "0.95"))
    placement = "[H]" if filename == "Q1_body_tumor_xz_section.png" else "[!htbp]"
    options = rf"width={width}\textwidth"
    if filename == "g4tsg_offscreen_zb_png_1.png":
        options += ",trim=90 200 100 210,clip"
    return [
        rf"\begin{{figure}}{placement}",
        r"    \centering",
        rf"    \includegraphics[{options}]{{\detokenize{{{filename}}}}}",
        rf"    \caption{{{convert_inline(caption)}}}",
        rf"    \label{{fig:report-{figure_index}}}",
        r"\end{figure}",
        "",
    ]


def bibliography() -> list[str]:
    return [
        r"\begin{thebibliography}{9}",
        "",
        r"\bibitem{nist-astar}",
        r"NIST. ASTAR: Stopping-Power and Range Tables for Helium Ions.",
        r"National Institute of Standards and Technology.",
        r"\url{https://physics.nist.gov/PhysRefData/Star/Text/ASTAR.html}",
        "",
        r"\bibitem{dartz2024}",
        r"Dartz O, Incerti S, et al.",
        r"Lithium inelastic cross-sections and their impact on micro and nano dosimetry of boron neutron capture.",
        r"\textit{Physics in Medicine and Biology}. 2024. PMID 38964312.",
        r"\url{https://pmc.ncbi.nlm.nih.gov/articles/PMC11271803/}",
        "",
        r"\bibitem{gschwind2024}",
        r"Gschwind A, et al.",
        r"Advancing lithium neutron capture therapy.",
        r"\textit{Applied Physics Letters}. 2024;124(4):043701.",
        r"\url{https://pubs.aip.org/aip/apl/article/124/4/043701/3050693/}",
        "",
        r"\bibitem{icru49}",
        r"ICRU. Stopping Powers and Ranges for Protons and Alpha Particles, Report 49.",
        r"International Commission on Radiation Units and Measurements, 1993.",
        "",
        r"\bibitem{agostinelli2003}",
        r"Agostinelli S, et al.",
        r"Geant4---a simulation toolkit.",
        r"\textit{Nuclear Instruments and Methods in Physics Research Section A}. 2003;506:250--303.",
        "",
        r"\end{thebibliography}",
    ]


def convert_body(markdown: str) -> list[str]:
    lines = markdown.splitlines()
    output: list[str] = []
    index = 0
    figure_index = 0
    in_abstract = False
    in_itemize = False

    while index < len(lines):
        line = lines[index].rstrip()
        stripped = line.strip()

        if stripped == "# Geant4 肿瘤放射治疗模拟实验报告":
            index += 1
            continue
        if stripped == "## 摘要":
            output.extend([r"\begin{abstract}", r"\sloppy"])
            in_abstract = True
            index += 1
            continue
        if in_abstract and stripped.startswith("**小组分工：**"):
            output.extend([r"\par\end{abstract}", "", r"\noindent " + convert_inline(stripped), ""])
            in_abstract = False
            index += 1
            continue
        if stripped.startswith("项目代码仓库："):
            if in_abstract:
                output.extend([r"\par\end{abstract}", ""])
                in_abstract = False
            output.extend([r"\noindent " + convert_inline(stripped), "", r"\newpage", r"\tableofcontents", r"\newpage", ""])
            index += 1
            continue
        if stripped == "## 参考文献":
            if in_itemize:
                output.extend([r"\end{itemize}", ""])
                in_itemize = False
            output.extend(bibliography())
            break
        if stripped.startswith("#### "):
            title = re.sub(r"^\d+(?:\.\d+)+\s+", "", stripped[5:])
            output.extend([rf"\subsubsection{{{convert_inline(title)}}}", ""])
            index += 1
            continue
        if stripped.startswith("### "):
            title = re.sub(r"^\d+(?:\.\d+)+\s+", "", stripped[4:])
            output.extend([rf"\subsection{{{convert_inline(title)}}}", ""])
            index += 1
            continue
        if stripped.startswith("## "):
            title = re.sub(r"^\d+\s+", "", stripped[3:])
            output.extend([rf"\section{{{convert_inline(title)}}}", ""])
            index += 1
            continue
        if stripped.startswith("!["):
            figure_index += 1
            output.extend(convert_figure(stripped, figure_index))
            index += 1
            continue
        if stripped.startswith("|"):
            table, index = convert_table(lines, index)
            output.extend(table)
            continue
        if stripped == "$$":
            math_lines: list[str] = []
            index += 1
            while index < len(lines) and lines[index].strip() != "$$":
                math_lines.append(lines[index])
                index += 1
            output.extend([r"\begin{equation}", *math_lines, r"\end{equation}", ""])
            index += 1
            continue
        if stripped.startswith("- "):
            if not in_itemize:
                output.append(r"\begin{itemize}")
                in_itemize = True
            output.append(r"    \item " + convert_inline(stripped[2:]))
            index += 1
            continue
        if in_itemize:
            output.extend([r"\end{itemize}", ""])
            in_itemize = False
        if not stripped:
            if output and output[-1] != "":
                output.append("")
            index += 1
            continue

        output.extend([convert_inline(stripped), ""])
        index += 1

    return output


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("usage: migrate_final_report_to_latex.py FINAL_REPORT EXISTING_MAIN OUTPUT")
    report_path, template_path, output_path = map(Path, sys.argv[1:])
    template = template_path.read_text(encoding="utf-8")
    preamble = template.split(r"\begin{document}", 1)[0].rstrip()
    preamble = preamble.replace("\n" + r"\usepackage{pdflscape}", "")
    if r"\emergencystretch" not in preamble:
        preamble += "\n" + r"\setlength{\emergencystretch}{3em}"
    if r"\textfloatsep" not in preamble:
        preamble += "\n" + r"\setlength{\textfloatsep}{8pt plus 2pt minus 2pt}"
        preamble += "\n" + r"\setlength{\floatsep}{8pt plus 2pt minus 2pt}"
        preamble += "\n" + r"\setlength{\intextsep}{8pt plus 2pt minus 2pt}"
    body = convert_body(report_path.read_text(encoding="utf-8"))
    document = "\n".join(
        [
            preamble,
            "",
            r"\begin{document}",
            "",
            r"\cover",
            r"\thispagestyle{empty}",
            "",
            r"\newpage",
            *body,
            "",
            r"\end{document}",
            "",
        ]
    )
    output_path.write_text(document, encoding="utf-8")


if __name__ == "__main__":
    main()
