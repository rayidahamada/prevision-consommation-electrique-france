"""Contrôle rédactionnel en lecture seule des documents et gabarits suivis par Git.

Codes de sortie : 0 sans erreur bloquante (avertissements possibles), 1 avec
erreurs rédactionnelles, 2 si le contrôle n'a pas pu être effectué correctement.
Des chemins relatifs supplémentaires peuvent compléter l'inventaire Git sans ajout à l'index.
L'option --include-untracked ajoute les Markdown et Python non suivis, hors fichiers ignorés.
"""

import argparse
import ast
from dataclasses import dataclass
import io
from pathlib import Path
import re
import subprocess
import sys
import tokenize
import unicodedata


ROOT = Path(__file__).resolve().parents[1]
ROLE_RULES = (
    ("DOC001", r"\bl['’]utilisateur\b"),
    ("DOC002", r"\bl['’]étudiant\b"),
    ("DOC003", r"\bChatGPT\b"),
    ("DOC004", r"\bl['’]assistant\b"),
    ("DOC005", r"\bmission demandée\b"),
)
INTERNAL_APPROVAL = re.compile(
    r"validation\s+(?:explicite|humaine)|autorisation\s+(?:explicite|préalable)|"
    r"confirmation\s+explicite|attend(?:re|ez)\s+(?:mon|notre)\s+accord", re.I
)
GIT_ACTION = re.compile(r"\bgit\s+(?:add|commit|push)\b|mise\s+en\s+index|\bpublication\b|\bcommit\b|\bpush\b", re.I)
STALE_RULES = (
    ("DOC007", r"\b(?:encore|toujours)\s+non\s+suivis?\b|\bpas\s+encore\s+(?:versionnés?|publiés?|suivis?)\b"),
    ("DOC008", r"\bmission\s+\d+\s+non commencée\b|\bla phase\s+\d+\s+nécessite une validation distincte\b|\battente de validation avant\b"),
    ("DOC009", r"\banalyse locale du\s+\d+\s+\w+\s+20\d{2}\b"),
)
QUOTE = re.compile(r'«[^»]*»|“[^”]*”|"[^"\n]*"')
QUOTE_CONTEXT = re.compile(r"citation|message d['’]erreur|trace technique|expression à éviter|formulation citée", re.I)
HISTORY = re.compile(r"note de suivi|note de lecture|état historique|rapport historique", re.I)
DATE = re.compile(r"\b20\d{2}(?:-\d{2}-\d{2})?\b")


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    severity: str
    rule: str
    expression: str
    explanation: str


def normalized(text):
    return unicodedata.normalize("NFC", text)


def markdown_lines(text):
    """Ignorer les blocs techniques clôturés ; préserver les numéros physiques."""
    fence_char, fence_length = None, 0
    previous = ""
    for number, raw in enumerate(text.splitlines(), 1):
        line = normalized(raw)
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})(.*)$", line)
        if marker:
            chars, tail = marker.groups()
            if fence_char is None:
                fence_char, fence_length = chars[0], len(chars)
            elif chars[0] == fence_char and len(chars) >= fence_length and not tail.strip():
                fence_char = None
            continue
        if fence_char is None:
            yield number, line, previous
            previous = line


def python_lines(path, text):
    """Examiner les chaînes et commentaires sans importer ni exécuter le code.

    Les tests contiennent volontairement des fixtures et le contrôleur contient
    ses règles : pour ces fichiers, seules les docstrings et les commentaires
    sont documentaires. Ailleurs, toutes les chaînes littérales sont examinées,
    notamment les gabarits de rapports et les fragments statiques des f-strings.
    """
    tree = ast.parse(text, filename=str(path))
    doc_positions = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.body and isinstance(node.body[0], ast.Expr):
                first = node.body[0].value
                if isinstance(first, ast.Constant) and isinstance(first.value, str):
                    doc_positions.add((first.lineno, first.col_offset))
    restricted = path.parts[0] == "tests" or path.as_posix() == "scripts/check_documentation.py"
    seen = set()
    for token in tokenize.generate_tokens(io.StringIO(text).readline):
        value = None
        if token.type == tokenize.COMMENT:
            value = token.string
        elif token.type == tokenize.STRING:
            if restricted and token.start not in doc_positions:
                continue
            try:
                literal = ast.literal_eval(token.string)
            except (ValueError, SyntaxError):
                continue
            if isinstance(literal, str):
                value = literal
        # Python 3.12+ expose séparément les fragments statiques des f-strings.
        elif not restricted and tokenize.tok_name.get(token.type) == "FSTRING_MIDDLE":
            value = token.string
        if value is not None:
            for offset, line in enumerate(value.splitlines()):
                # Un saut de ligne échappé dans une chaîne sur une seule ligne
                # ne doit pas produire un numéro de ligne physique inexistant.
                entry = (min(token.start[0] + offset, token.end[0]), normalized(line), "")
                if entry not in seen:
                    seen.add(entry)
                    yield entry


def inspect_text(path, text):
    """Détecter des indices rédactionnels ; aucune conclusion scientifique automatique."""
    path = Path(path)
    if path.name.casefold() == "agents.md":
        return []
    suffix = path.suffix.casefold()
    if suffix not in (".md", ".markdown", ".py"):
        return []
    is_python = suffix == ".py"
    is_readme = path.as_posix().casefold() == "readme.md"
    header = "\n".join(text.splitlines()[:35])
    historical = not is_python and not is_readme and bool(HISTORY.search(header) and DATE.search(header))
    entries = python_lines(path, text) if is_python else markdown_lines(text)
    findings = []
    for number, line, previous in entries:
        quote_ranges = [(m.start(), m.end()) for m in QUOTE.finditer(line)] if not is_python else []

        def quoted_technical(start, end):
            return (bool(QUOTE_CONTEXT.search(line + " " + previous))
                    and any(a <= start and end <= b for a, b in quote_ranges))

        for rule, pattern in ROLE_RULES:
            for match in re.finditer(pattern, line, re.I):
                if quoted_technical(*match.span()):
                    continue
                explanation = "Formulation conversationnelle à relire."
                if historical:
                    explanation += " Contexte historique : préserver la provenance et les faits."
                findings.append(Finding(path.as_posix(), number, "ERROR" if is_readme else "WARNING",
                                        rule, match.group(), explanation))
        if is_readme:
            approval = INTERNAL_APPROVAL.search(line)
            if approval and GIT_ACTION.search(line) and not quoted_technical(*approval.span()):
                findings.append(Finding(path.as_posix(), number, "ERROR", "DOC006", approval.group(),
                                        "Consigne de pilotage Git à réserver à AGENTS.md."))
        for rule, pattern in STALE_RULES:
            if historical:
                continue  # Les rapports datés conservent un état passé, pas une alerte courante.
            for match in re.finditer(pattern, line, re.I):
                if quoted_technical(*match.span()):
                    continue
                severity = "ERROR" if is_readme and rule in ("DOC007", "DOC008") else "WARNING"
                findings.append(Finding(path.as_posix(), number, severity, rule, match.group(),
                                        "État susceptible de vieillir : dater ou contextualiser le constat."))
    return findings


def tracked_paths(root):
    """Lire l'inventaire de l'index ; aucune opération d'ajout, aucune consultation réseau."""
    result = subprocess.run(["git", "-C", str(root), "ls-files", "-z"],
                            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return [Path(name.decode("utf-8")) for name in result.stdout.split(b"\0")
            if name and Path(name.decode("utf-8")).suffix.casefold() in (".md", ".markdown", ".py")]


def untracked_paths(root):
    """Lire les nouveaux fichiers sans inclure les exclusions Git ni modifier l'index."""
    result = subprocess.run(["git", "-C", str(root), "ls-files", "--others", "--exclude-standard", "-z"],
                            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return [Path(name.decode("utf-8")) for name in result.stdout.split(b"\0")
            if name and Path(name.decode("utf-8")).suffix.casefold() in (".md", ".markdown", ".py")]


def check_repository(root, extra_paths=(), include_untracked=False):
    root = Path(root).resolve()
    paths = set(tracked_paths(root))
    if include_untracked:
        paths.update(untracked_paths(root))
    for value in extra_paths:
        candidate = Path(value)
        resolved = (root / candidate).resolve()
        if not resolved.is_relative_to(root):
            raise ValueError("Un chemin supplémentaire doit rester dans le dépôt.")
        if resolved.suffix.casefold() not in (".md", ".markdown", ".py"):
            raise ValueError("Seuls les fichiers Markdown et Python peuvent être contrôlés.")
        paths.add(resolved.relative_to(root))
    findings = []
    checked = 0
    for path in sorted(paths):
        full = root / path
        if full.is_symlink() or not full.resolve().is_relative_to(root):
            raise ValueError(f"Lien externe ou symbolique non contrôlé : {path}")
        text = full.read_text(encoding="utf-8-sig")
        findings.extend(inspect_text(path, text))
        if path.name.casefold() != "agents.md" and path.suffix.casefold() in (".md", ".markdown", ".py"):
            checked += 1
    return checked, findings


def exit_code(findings):
    return int(any(f.severity == "ERROR" for f in findings))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-untracked", action="store_true",
                        help="Inclure les Markdown/Python non suivis, hors exclusions .gitignore.")
    parser.add_argument("paths", nargs="*", help="Fichiers supplémentaires non suivis, relatifs à la racine.")
    args = parser.parse_args(argv)
    try:
        checked, findings = check_repository(ROOT, args.paths, include_untracked=args.include_untracked)
    except (OSError, ValueError, SyntaxError, tokenize.TokenError, subprocess.SubprocessError) as error:
        print(f"Contrôle impossible : {error}", file=sys.stderr)
        return 2
    for finding in findings:
        print(f"{finding.path}:{finding.line}: {finding.severity} {finding.rule}: "
              f"{finding.expression!r} — {finding.explanation}")
    errors = sum(f.severity == "ERROR" for f in findings)
    warnings = sum(f.severity == "WARNING" for f in findings)
    print(f"{checked} fichiers contrôlés ; {errors} erreur(s), {warnings} avertissement(s). "
          "AGENTS.md est exempté. Aucune modification de fichier.")
    return exit_code(findings)


if __name__ == "__main__":
    sys.exit(main())
