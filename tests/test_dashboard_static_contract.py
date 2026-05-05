from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
APP_JS = REPO_ROOT / "mempalace" / "dashboard_static" / "app.js"
INDEX_HTML = REPO_ROOT / "mempalace" / "dashboard_static" / "index.html"
STYLES_CSS = REPO_ROOT / "mempalace" / "dashboard_static" / "styles.css"


class DashboardStaticContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app_js = APP_JS.read_text(encoding="utf-8")
        cls.index_html = INDEX_HTML.read_text(encoding="utf-8")
        cls.styles_css = STYLES_CSS.read_text(encoding="utf-8")

    def test_index_contains_ontology_progress_and_artifact_elements(self) -> None:
        required_ids = [
            "ontologyRunState",
            "ontologyRunList",
            "ontologyRunTitle",
            "ontologyProgressBar",
            "ontologyProgressPercent",
            "ontologyArtifactList",
            "ontologyArtifactDetail",
            "ontologyPreviewList",
        ]
        for element_id in required_ids:
            with self.subTest(element_id=element_id):
                self.assertIn(f'id="{element_id}"', self.index_html)

    def test_app_uses_only_read_only_ontology_endpoints(self) -> None:
        allowed = {
            '/api/ontology/runs',
            '/api/ontology/runs/',
            '/artifacts',
            '/unresolved-preview',
        }
        self.assertIn('requestJson("/api/ontology/runs")', self.app_js)
        self.assertIn('/api/ontology/runs/${encodeURIComponent(selectedRunId)}', self.app_js)
        self.assertIn('/api/ontology/runs/${encodeURIComponent(selectedRunId)}/artifacts', self.app_js)
        self.assertIn('/api/ontology/runs/${encodeURIComponent(selectedRunId)}/unresolved-preview', self.app_js)
        forbidden_fragments = [
            '/api/ontology/runs/create',
            '/api/ontology/runs/apply',
            '/api/ontology/runs/copy',
            '/api/ontology/runs/mutate',
            '/api/ontology/runs/write',
            'method: "POST"',
            'method: "PUT"',
            'method: "PATCH"',
            'method: "DELETE"',
        ]
        for fragment in forbidden_fragments:
            with self.subTest(fragment=fragment):
                self.assertNotIn(fragment, self.app_js)
        # Sanity-check that the file only references the expected ontology read paths.
        self.assertTrue(all(fragment in self.app_js for fragment in allowed))

    def test_refresh_overview_refreshes_ontology_during_mining(self) -> None:
        self.assertIn("const tasks = [refreshOntology()];", self.app_js)
        self.assertIn("if (!state.miningActive) {", self.app_js)
        self.assertIn("tasks.push(refreshTaxonomy(), refreshDrawers());", self.app_js)
        self.assertIn("renderTaxonomy([]);", self.app_js)
        self.assertIn("renderDrawers([]);", self.app_js)
        self.assertIn("setInteractionLock(state.miningActive", self.app_js)

    def test_progress_meter_and_preview_wiring_use_metadata_only(self) -> None:
        self.assertIn("phaseProgress.processed", self.app_js)
        self.assertIn("phaseProgress.total", self.app_js)
        self.assertIn("current_phase_progress", self.app_js)
        self.assertIn("artifact.dashboard_safe", self.app_js)
        self.assertIn("artifact.privacy_level", self.app_js)
        self.assertIn("No full artifact body is fetched here.", self.app_js)
        self.assertIn("bounded unresolved preview", self.app_js.lower())
        self.assertIn("source_excerpt", self.app_js)

    def test_styles_include_ontology_layout_and_progress_meter(self) -> None:
        for token in [
            ".ontology-workbench",
            ".ontology-layout",
            ".progress-track",
            ".progress-fill",
            ".artifact-list",
            ".preview-list",
        ]:
            with self.subTest(token=token):
                self.assertIn(token, self.styles_css)


if __name__ == "__main__":
    unittest.main()
