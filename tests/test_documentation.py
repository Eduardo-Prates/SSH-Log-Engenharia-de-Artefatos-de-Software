import re
import unittest
from pathlib import Path
from urllib.parse import unquote

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_MARKDOWN_LINK = re.compile(r"\[[^]]+]\((?P<target>[^)]+)\)")


class DocumentationTests(unittest.TestCase):
    def test_local_markdown_links_resolve(self) -> None:
        markdown_files = [
            _PROJECT_ROOT / "README.md",
            _PROJECT_ROOT / "SPEC.md",
            _PROJECT_ROOT / "CHANGELOG.md",
            _PROJECT_ROOT / "CONTRIBUTING.md",
            *_PROJECT_ROOT.joinpath("docs").glob("*.md"),
        ]
        missing_links: list[str] = []

        for document in markdown_files:
            content = document.read_text(encoding="utf-8")
            for match in _MARKDOWN_LINK.finditer(content):
                target = unquote(match.group("target").split("#", maxsplit=1)[0])
                if not target or "://" in target or target.startswith("mailto:"):
                    continue
                if not (document.parent / target).exists():
                    missing_links.append(f"{document.name}: {target}")

        self.assertEqual(missing_links, [])

    def test_distribution_and_package_versions_match(self) -> None:
        import tomllib

        import ssh_log_sentinel

        with (_PROJECT_ROOT / "pyproject.toml").open("rb") as pyproject_file:
            distribution_version = tomllib.load(pyproject_file)["project"]["version"]

        self.assertEqual(distribution_version, ssh_log_sentinel.__version__)

    def test_distribution_declares_license_and_repository(self) -> None:
        import tomllib

        with (_PROJECT_ROOT / "pyproject.toml").open("rb") as pyproject_file:
            project = tomllib.load(pyproject_file)["project"]

        self.assertEqual(project["license"], "MIT")
        self.assertTrue((_PROJECT_ROOT / "LICENSE").is_file())
        self.assertEqual(
            project["urls"]["Repository"],
            "https://github.com/Eduardo-Prates/"
            "SSH-Log-Sentinel---Engenharia-de-Artefatos-de-Software",
        )


if __name__ == "__main__":
    unittest.main()
