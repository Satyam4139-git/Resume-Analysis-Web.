import os
import unittest
from unittest import mock

os.environ.setdefault("OPENROUTER_API_KEY", "test")

from fastapi.testclient import TestClient

from app.api.main import app
from app.api.routes import jobs as jobs_route
from app.jobs import job_board
from app.jobs.job_board import JobBoardService, level_matches


def adzuna_payload(*rows, count=None):
    results = []
    for i, (title, company, where, desc, created, predicted) in enumerate(rows):
        results.append({
            "id": str(1000 + i),
            "title": title,
            "company": {"display_name": company},
            "location": {"display_name": where},
            "description": desc,
            "redirect_url": f"https://www.adzuna.in/land/ad/{1000 + i}",
            "created": created,
            "salary_min": 600000,
            "salary_max": 900000,
            "salary_is_predicted": "1" if predicted else "0",
        })
    return {"count": count if count is not None else len(results), "results": results}


class FakeResponse:
    def __init__(self, payload, status=200):
        self.payload, self.status_code = payload, status

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests
            raise requests.HTTPError(f"{self.status_code}")

    def json(self):
        return self.payload


ROWS = (
    ("Python Developer", "TCS", "Kolkata, West Bengal", "Python, SQL and Django. 0-1 years of experience.", "2026-10-15T08:00:00Z", True),
    ("Senior Python Engineer", "Infosys", "Bangalore, Karnataka", "Lead our backend. 8+ years of experience.", "2026-10-10T08:00:00Z", False),
    ("Python Developer (Remote)", "Acme", "Remote", "Work from home. Python and AWS.", "2026-10-16T08:00:00Z", False),
    ("Junior Data Analyst", "Zoho", "Chennai", "SQL, Excel, Power BI.", "2026-09-01T08:00:00Z", False),
)


class JobBoardTests(unittest.TestCase):

    def setUp(self):
        self.p = [
            mock.patch.object(job_board, "ADZUNA_APP_ID", "id"),
            mock.patch.object(job_board, "ADZUNA_APP_KEY", "key"),
            mock.patch.object(job_board, "JOOBLE_API_KEY", None),
            mock.patch.object(job_board, "ADZUNA_COUNTRY", "in"),
            mock.patch.object(job_board, "ADZUNA_COUNTRIES", "in"),
        ]
        for patcher in self.p:
            patcher.start()
        job_board._service = JobBoardService()
        jobs_route._hits.clear()
        self.client = TestClient(app)

    def tearDown(self):
        for patcher in self.p:
            patcher.stop()

    # ---- validation ----------------------------------------------------

    def test_empty_search_is_400(self):
        r = self.client.get("/jobs/search")
        self.assertEqual(r.status_code, 400)

    def test_bad_level_is_400(self):
        r = self.client.get("/jobs/search?q=python&level=ninja")
        self.assertEqual(r.status_code, 400)

    def test_no_provider_is_503(self):
        with mock.patch.object(job_board, "ADZUNA_APP_ID", None):
            job_board._service = JobBoardService()
            r = self.client.get("/jobs/search?q=python")
        self.assertEqual(r.status_code, 503)

    # ---- results -------------------------------------------------------

    @mock.patch("app.jobs.job_board.requests.get")
    def test_basic_search_shape_and_predicted_salary_hidden(self, get):
        get.return_value = FakeResponse(adzuna_payload(*ROWS, count=120))
        r = self.client.get("/jobs/search?q=python&location=Kolkata")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["total"], 120)
        self.assertTrue(data["has_more"])
        first = next(j for j in data["jobs"] if j["company"] == "TCS")
        self.assertIsNone(first["salary_min"])            # predicted -> hidden
        self.assertIn("Python", first["skills"])
        self.assertEqual(first["source"], "Adzuna")
        params = get.call_args.kwargs["params"]
        self.assertEqual(params["what"], "python")
        self.assertEqual(params["where"], "Kolkata")

    @mock.patch("app.jobs.job_board.requests.get")
    def test_fresher_filter_removes_senior_jobs(self, get):
        get.return_value = FakeResponse(adzuna_payload(*ROWS))
        titles = [j["title"] for j in self.client.get("/jobs/search?q=python&level=fresher").json()["jobs"]]
        self.assertNotIn("Senior Python Engineer", titles)
        self.assertIn("Python Developer", titles)

    @mock.patch("app.jobs.job_board.requests.get")
    def test_senior_filter_keeps_only_senior(self, get):
        get.return_value = FakeResponse(adzuna_payload(*ROWS))
        jobs = self.client.get("/jobs/search?q=python&level=senior").json()["jobs"]
        self.assertTrue(all(j["title"] != "Junior Data Analyst" for j in jobs))
        self.assertIn("Senior Python Engineer", [j["title"] for j in jobs])

    @mock.patch("app.jobs.job_board.requests.get")
    def test_remote_filter(self, get):
        get.return_value = FakeResponse(adzuna_payload(*ROWS))
        jobs = self.client.get("/jobs/search?q=python&remote=true").json()["jobs"]
        self.assertEqual([j["company"] for j in jobs], ["Acme"])
        self.assertTrue(jobs[0]["remote"])

    @mock.patch("app.jobs.job_board.requests.get")
    def test_sort_by_date(self, get):
        get.return_value = FakeResponse(adzuna_payload(*ROWS))
        jobs = self.client.get("/jobs/search?q=python&sort=date").json()["jobs"]
        dates = [j["posted_at"] for j in jobs]
        self.assertEqual(dates, sorted(dates, reverse=True))
        self.assertEqual(get.call_args.kwargs["params"]["sort_by"], "date")

    @mock.patch("app.jobs.job_board.requests.get")
    def test_posted_within_sent_to_provider(self, get):
        get.return_value = FakeResponse(adzuna_payload(*ROWS))
        self.client.get("/jobs/search?q=python&posted_within=7")
        self.assertEqual(get.call_args.kwargs["params"]["max_days_old"], 7)

    # ---- providers -----------------------------------------------------

    @mock.patch("app.jobs.job_board.requests.post")
    @mock.patch("app.jobs.job_board.requests.get")
    def test_jooble_merged_and_deduped(self, get, post):
        get.return_value = FakeResponse(adzuna_payload(*ROWS))
        post.return_value = FakeResponse({"totalCount": 40, "jobs": [
            {"id": 7, "title": "Python Developer", "company": "TCS", "location": "Kolkata, West Bengal",
             "snippet": "dup of Adzuna", "link": "https://jooble.org/jdp/1", "updated": "2026-10-15T00:00:00"},
            {"id": 8, "title": "Backend Engineer", "company": "Flipkart", "location": "Bangalore",
             "snippet": "Python and Kafka", "link": "https://jooble.org/jdp/2", "updated": "2026-10-14T00:00:00",
             "salary": "₹12 LPA"},
        ]})
        with mock.patch.object(job_board, "JOOBLE_API_KEY", "jk"):
            job_board._service = JobBoardService()
            data = self.client.get("/jobs/search?q=python").json()
        companies = [(j["company"], j["source"]) for j in data["jobs"]]
        self.assertEqual(companies.count(("TCS", "Adzuna")), 1)
        self.assertNotIn(("TCS", "Jooble"), companies)
        self.assertIn(("Flipkart", "Jooble"), companies)
        self.assertEqual(data["total"], 4 + 40)

    @mock.patch("app.jobs.job_board.requests.post", side_effect=Exception("boom"))
    @mock.patch("app.jobs.job_board.requests.get")
    def test_one_provider_failing_is_ok(self, get, _post):
        get.return_value = FakeResponse(adzuna_payload(*ROWS))
        with mock.patch.object(job_board, "JOOBLE_API_KEY", "jk"):
            job_board._service = JobBoardService()
            r = self.client.get("/jobs/search?q=python")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["jobs"])

    @mock.patch("app.jobs.job_board.requests.get", side_effect=Exception("down"))
    def test_all_providers_failing_is_503(self, _get):
        r = self.client.get("/jobs/search?q=python")
        self.assertEqual(r.status_code, 503)

    # ---- speed / safety ------------------------------------------------

    @mock.patch("app.jobs.job_board.requests.get")
    def test_repeat_search_uses_cache(self, get):
        get.return_value = FakeResponse(adzuna_payload(*ROWS))
        self.client.get("/jobs/search?q=python")
        self.client.get("/jobs/search?q=Python")
        self.assertEqual(get.call_count, 1)

    @mock.patch("app.jobs.job_board.requests.get")
    def test_rate_limit(self, get):
        get.return_value = FakeResponse(adzuna_payload(*ROWS))
        codes = [self.client.get(f"/jobs/search?q=python{i}").status_code for i in range(32)]
        self.assertEqual(codes[:30], [200] * 30)
        self.assertEqual(codes[30], 429)

    # ---- more openings: several countries -------------------------------

    @mock.patch("app.jobs.job_board.requests.get")
    def test_searches_several_countries_main_first(self, get):
        def fake(url, params=None, timeout=None):
            code = url.split("/jobs/")[1].split("/")[0]
            return FakeResponse(adzuna_payload(
                (f"Python Developer {code}", f"Co-{code}", "Anywhere", "Python.", "2026-10-15T08:00:00Z", False),
            ))
        get.side_effect = fake
        with mock.patch.object(job_board, "ADZUNA_COUNTRIES", "in,gb,us,au,ca"):
            data = self.client.get("/jobs/search?q=python").json()
        called = sorted(c.args[0].split("/jobs/")[1].split("/")[0] for c in get.call_args_list)
        self.assertEqual(called, ["gb", "in", "us"])          # capped at 3
        self.assertEqual(len(data["jobs"]), 3)
        self.assertEqual(data["jobs"][0]["company"], "Co-in")  # India first
        self.assertEqual(len({j["id"] for j in data["jobs"]}), 3)

    @mock.patch("app.jobs.job_board.requests.get")
    def test_other_countries_must_match_the_city(self, get):
        def fake(url, params=None, timeout=None):
            code = url.split("/jobs/")[1].split("/")[0]
            where = "Kolkata, West Bengal" if code == "in" else "Austin, Texas"
            return FakeResponse(adzuna_payload(
                (f"Python Developer {code}", f"Co-{code}", where, "Python.", "2026-10-15T08:00:00Z", False),
            ))
        get.side_effect = fake
        with mock.patch.object(job_board, "ADZUNA_COUNTRIES", "in,us"):
            data = self.client.get("/jobs/search?q=python&location=Kolkata").json()
        self.assertEqual([j["company"] for j in data["jobs"]], ["Co-in"])

    @mock.patch("app.jobs.job_board.requests.get")
    def test_one_country_failing_keeps_the_others(self, get):
        def fake(url, params=None, timeout=None):
            if "/gb/" in url:
                raise Exception("quota")
            return FakeResponse(adzuna_payload(*ROWS))
        get.side_effect = fake
        with mock.patch.object(job_board, "ADZUNA_COUNTRIES", "in,gb"):
            r = self.client.get("/jobs/search?q=python")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["jobs"])

    # ---- Jooble must be visible, never buried, and keys never leak ------

    @mock.patch("app.jobs.job_board.requests.post")
    @mock.patch("app.jobs.job_board.requests.get")
    def test_jooble_jobs_are_mixed_in_not_buried_at_the_bottom(self, get, post):
        adz = [(f"Python Developer {i}", f"AdzCo{i}", "Pune", "Python.", "2026-10-15T08:00:00Z", False)
               for i in range(10)]
        get.return_value = FakeResponse(adzuna_payload(*adz))
        post.return_value = FakeResponse({"totalCount": 10, "jobs": [
            {"id": i, "title": f"Python Developer J{i}", "company": f"JooCo{i}", "location": "Pune",
             "snippet": "Python.", "link": f"https://jooble.org/jdp/{i}", "updated": "2026-10-15T00:00:00"}
            for i in range(10)]})
        with mock.patch.object(job_board, "JOOBLE_API_KEY", "jk"):
            job_board._service = JobBoardService()
            data = self.client.get("/jobs/search?q=python+developer").json()
        first_six = [j["source"] for j in data["jobs"][:6]]
        self.assertEqual(first_six.count("Jooble"), 3)            # alternating
        self.assertEqual(data["sources"], {"Adzuna": 10, "Jooble": 10})

    @mock.patch("app.jobs.job_board.requests.post")
    @mock.patch("app.jobs.job_board.requests.get")
    def test_failed_provider_is_reported_without_leaking_the_key(self, get, post):
        import requests as rq
        get.return_value = FakeResponse(adzuna_payload(*ROWS))
        post.side_effect = rq.ConnectionError("failed for url: https://jooble.org/api/SECRETKEY123")
        with mock.patch.object(job_board, "JOOBLE_API_KEY", "SECRETKEY123"):
            job_board._service = JobBoardService()
            with self.assertLogs("ResumeAnalyzer", level="WARNING") as logs:
                self.client.get("/jobs/search?q=python")
            status = self.client.get("/jobs/status").json()["providers"]
        self.assertFalse(status["Jooble"]["ok"])
        self.assertTrue(status["Adzuna"]["ok"])
        self.assertTrue(status["Jooble"]["configured"])
        self.assertNotIn("SECRETKEY123", str(status))
        self.assertNotIn("SECRETKEY123", "\n".join(logs.output))

    def test_status_endpoint_shows_unconfigured_provider(self):
        data = self.client.get("/jobs/status").json()["providers"]
        self.assertTrue(data["Adzuna"]["configured"])
        self.assertFalse(data["Jooble"]["configured"])

    def test_level_matching_rules(self):
        self.assertEqual(level_matches("fresher", "Junior Python Dev", "")[0], False)
        self.assertEqual(level_matches("junior", "Python Developer", "1-3 years of experience")[0], True)
        self.assertEqual(level_matches("mid", "Python Developer", "")[0], True)       # unstated -> kept
        self.assertEqual(level_matches("fresher", "Python Dev", "5+ years of experience")[0], False)


if __name__ == "__main__":
    unittest.main()
