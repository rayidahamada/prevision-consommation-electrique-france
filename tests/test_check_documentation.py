"""Tests synthétiques du contrôle rédactionnel ; aucun changement de documentation réelle."""

from contextlib import redirect_stdout, redirect_stderr
import io
import hashlib
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from scripts.check_documentation import check_repository, exit_code, inspect_text, main, untracked_paths


class DocumentationTests(unittest.TestCase):
    def test_readme_roles_and_apostrophes_block(self):
        text = "# Projet\nL’utilisateur doit décider.\nL'étudiant attend ChatGPT et l'assistant.\nLa mission demandée est finie.\n"
        findings = inspect_text(Path("README.md"), text)
        self.assertEqual({f.rule for f in findings}, {"DOC001", "DOC002", "DOC003", "DOC004", "DOC005"})
        self.assertTrue(all(f.severity == "ERROR" for f in findings))
        self.assertEqual(findings[0].line, 2)
        self.assertEqual(exit_code(findings), 1)

    def test_agents_rules_are_exempt(self):
        self.assertEqual(inspect_text(Path("AGENTS.md"), "L'utilisateur attend ChatGPT. Validation humaine avant git add."), [])

    def test_scientific_terms_and_codex_provenance_allowed(self):
        text = "Codex : échec réseau daté. Validation chronologique des modèles.\nUne hypothèse reste non confirmée."
        self.assertEqual(inspect_text(Path("README.md"), text), [])

    def test_internal_git_approval_readme_only(self):
        text = "Validation humaine requise avant toute mise en index."
        findings = inspect_text(Path("README.md"), text)
        self.assertEqual([f.rule for f in findings], ["DOC006"])
        self.assertEqual(exit_code(findings), 1)
        self.assertEqual(inspect_text(Path("reports/historique.md"), text), [])

    def test_technical_fences_and_explicit_quotations_ignored(self):
        text = "# Guide\n```text\nl'utilisateur : ChatGPT\n```\nExpression à éviter : « l'étudiant ».\nCitation technique : \"l'assistant\".\n"
        self.assertEqual(inspect_text(Path("README.md"), text), [])

    def test_plain_quote_does_not_hide_real_dialogue(self):
        findings = inspect_text(Path("README.md"), "« l'utilisateur » doit autoriser la suite.")
        self.assertEqual(exit_code(findings), 1)

    def test_historical_state_not_reported_as_current(self):
        text = "# Rapport historique — 2026-11-04\nMission 007 non commencée.\nLes fichiers sont encore non suivis.\n"
        self.assertEqual(inspect_text(Path("reports/audit.md"), text), [])

    def test_historical_attribution_warning_never_blocking(self):
        findings = inspect_text(Path("reports/audit.md"), "# Rapport historique — 2026-11-04\nL'utilisateur a signalé un échec.\n")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].severity, "WARNING")
        self.assertEqual(exit_code(findings), 0)

    def test_uncontextualized_stale_readme_blocks(self):
        findings = inspect_text(Path("README.md"), "Les fichiers sont encore non suivis.")
        self.assertEqual([f.rule for f in findings], ["DOC007"])
        self.assertEqual(findings[0].severity, "ERROR")
        self.assertEqual(exit_code(findings), 1)

    def test_doc008_blocks_readme_even_with_historical_header(self):
        findings = inspect_text(Path("README.md"), "# Rapport historique — 2026-11-04\nMission 007 non commencée.\n")
        self.assertEqual([f.rule for f in findings], ["DOC008"])
        self.assertEqual(findings[0].severity, "ERROR")
        self.assertEqual(exit_code(findings), 1)

    def test_doc009_readme_remains_warning(self):
        findings = inspect_text(Path("README.md"), "Analyse locale du 4 novembre 2026.")
        self.assertEqual([f.rule for f in findings], ["DOC009"])
        self.assertEqual(findings[0].severity, "WARNING")
        self.assertEqual(exit_code(findings), 0)

    def test_stale_reports_and_python_remain_warnings(self):
        text = "Les fichiers sont encore non suivis. Mission 007 non commencée."
        for path, content in [("reports/current.md", text), ("src/template.py", "text = " + repr(text))]:
            with self.subTest(path=path):
                findings = inspect_text(Path(path), content)
                self.assertEqual({f.rule for f in findings}, {"DOC007", "DOC008"})
                self.assertTrue(all(f.severity == "WARNING" for f in findings))
                self.assertEqual(exit_code(findings), 0)

    def test_real_untracked_inventory_cli_and_ignored_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "--quiet", str(root)], check=True, capture_output=True)
            contents = {
                ".gitignore": "ignored.md\nignored.py\n",
                "README.md": "Les fichiers sont encore non suivis.\n",
                "new.md": "L'utilisateur attend.\n",
                "new.py": '"""Documentation technique neutre."""\n',
                "ignored.md": "ChatGPT attend.\n",
                "ignored.py": '"""ChatGPT attend."""\n',
                "observations.json": '{}\n',
            }
            for name, text in contents.items():
                (root / name).write_text(text, encoding="utf-8")

            def hashes():
                return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in root.rglob("*") if p.is_file()}

            before = hashes()
            self.assertEqual(set(untracked_paths(root)), {Path("README.md"), Path("new.md"), Path("new.py")})
            self.assertEqual(check_repository(root), (0, []))
            checked, findings = check_repository(root, include_untracked=True)
            self.assertEqual(checked, 3)
            self.assertEqual({f.path for f in findings}, {"README.md", "new.md"})
            self.assertEqual(exit_code(findings), 1)
            # Les chemins explicites restent prioritaires, même pour un fichier ignoré demandé volontairement.
            checked, explicit = check_repository(root, ["ignored.md"], include_untracked=True)
            self.assertEqual(checked, 4)
            self.assertIn("ignored.md", {f.path for f in explicit})
            with patch("scripts.check_documentation.ROOT", root):
                output = io.StringIO()
                with redirect_stdout(output):
                    self.assertEqual(main([]), 0)
                    self.assertEqual(main(["--include-untracked"]), 1)
                self.assertIn("ERROR DOC007", output.getvalue())
                self.assertIn("README.md:1", output.getvalue())
                # Deuxième cas réel de README : DOC008 doit également bloquer la commande.
                (root / "README.md").write_text("Mission 007 non commencée.\n", encoding="utf-8")
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(main(["--include-untracked"]), 1)
                (root / "README.md").write_text(contents["README.md"], encoding="utf-8")
            self.assertEqual(hashes(), before)
            self.assertFalse((root / ".git/index").exists())

    def test_python_docstrings_comments_templates_and_line_numbers(self):
        code = ('"""Module technique."""\n'
                '# ChatGPT attend.\n'
                'def report():\n'
                '    return """Rapport\n'
                "L'utilisateur a confirmé.\n"
                'Mission 007 non commencée.\n'
                '"""\n')
        findings = inspect_text(Path("src/report.py"), code)
        self.assertEqual({f.line for f in findings}, {2, 5, 6})
        self.assertTrue(all(f.severity == "WARNING" for f in findings))

    def test_python_implicit_concatenation_physical_line(self):
        code = 'text = ("Rapport "\n        "ChatGPT décide.")\n'
        findings = inspect_text(Path("src/report.py"), code)
        self.assertEqual([f.line for f in findings], [2])
        escaped = 'text = "Rapport\\nChatGPT décide."\n'
        self.assertEqual([f.line for f in inspect_text(Path("src/report.py"), escaped)], [1])

    def test_python_fixture_exempt_but_docstring_checked(self):
        code = '"""ChatGPT pilote ce test."""\nfixture = "L\'utilisateur attend."\n'
        findings = inspect_text(Path("tests/test_fixture.py"), code)
        self.assertEqual([f.line for f in findings], [1])

    def test_invalid_python_not_silently_skipped(self):
        with self.assertRaises(SyntaxError):
            inspect_text(Path("src/broken.py"), "def broken(")

    def test_repository_uses_inventory_and_never_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            readme = root / "README.md"
            readme.write_text("Documentation neutre.\n", encoding="utf-8")
            extra = root / "new.md"
            extra.write_text("L'utilisateur attend.\n", encoding="utf-8")
            original = {p: p.read_bytes() for p in (readme, extra)}
            with patch("scripts.check_documentation.tracked_paths", return_value=[Path("README.md")]):
                checked, findings = check_repository(root)
                self.assertEqual((checked, findings), (1, []))
                checked, findings = check_repository(root, ["new.md"])
                self.assertEqual(checked, 2)
                self.assertEqual(len(findings), 1)
                with self.assertRaises(ValueError):
                    check_repository(root, ["../outside.md"])
                with self.assertRaises(ValueError):
                    check_repository(root, ["observations.json"])
            for p, content in original.items():
                self.assertEqual(p.read_bytes(), content)

    def test_command_exit_on_failure_and_warning(self):
        with patch("scripts.check_documentation.check_repository", side_effect=OSError("test failure")):
            with redirect_stderr(io.StringIO()):
                self.assertEqual(main([]), 2)
        warnings = inspect_text(Path("reports/audit.md"), "L'utilisateur a confirmé.")
        with patch("scripts.check_documentation.check_repository", return_value=(1, warnings)):
            with redirect_stdout(io.StringIO()):
                self.assertEqual(main([]), 0)


if __name__ == "__main__":
    unittest.main()
