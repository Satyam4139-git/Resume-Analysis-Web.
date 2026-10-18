import os
import unittest
from types import SimpleNamespace
from unittest import mock

os.environ.setdefault("OPENROUTER_API_KEY", "test")

from app.services.job_opportunity_service import JobOpportunityService


def job(i, title, desc="Python and SQL."):
    return {
        "title": title, "company": f"Co{i}", "location": "Pune",
        "description": desc, "url": f"https://x/{i}", "source": "Adzuna",
        "level": "", "remote": False,
    }


class FakeBoard:
    configured = True

    def __init__(self, strict, loose):
        self.strict, self.loose, self.calls = strict, loose, []

    def search(self, q, level="", limit=20, **_kw):
        self.calls.append((q, level, limit))
        return {"jobs": self.strict if level else self.loose}


class SuitableJobsTests(unittest.TestCase):

    def run_search(self, board, years, level, limit=30):
        resume = SimpleNamespace(
            skills=["Python", "SQL"], experience_years=years,
            experience_level=level, career_profile=None, summary="", experience="",
        )
        service = JobOpportunityService()
        with mock.patch("app.jobs.job_board.get_job_board", return_value=board), \
             mock.patch.object(JobOpportunityService, "_build_search_terms",
                               return_value=["python developer"]):
            return service.search_jobs(resume, limit=limit)

    def test_more_than_ten_jobs_and_default_is_not_six(self):
        strict = [job(i, "Junior Python Developer") for i in range(4)]
        loose = [job(100 + i, "Python Developer") for i in range(25)]
        out = self.run_search(FakeBoard(strict, loose), 1.5, 1)
        self.assertGreater(len(out), 10)
        self.assertEqual(len({j["job_url"] for j in out}), len(out))   # no duplicates

    def test_fallback_still_hides_jobs_far_above_the_candidate(self):
        strict = [job(1, "Intern Python")]
        loose = [job(2, "Principal Python Architect"), job(3, "Senior Python Engineer"),
                 job(4, "Python Developer")]
        out = self.run_search(FakeBoard(strict, loose), 0.3, 0)
        titles = [j["title"] for j in out]
        self.assertNotIn("Principal Python Architect", titles)
        self.assertNotIn("Senior Python Engineer", titles)
        self.assertIn("Python Developer", titles)

    def test_senior_engineer_does_not_get_junior_jobs(self):
        strict = [job(1, "Senior Python Engineer")]
        loose = [job(2, "Python Intern"), job(3, "Junior Python Developer"),
                 job(4, "Lead Python Engineer")]
        out = self.run_search(FakeBoard(strict, loose), 8, 3)
        titles = [j["title"] for j in out]
        self.assertNotIn("Python Intern", titles)
        self.assertNotIn("Junior Python Developer", titles)
        self.assertIn("Senior Python Engineer", titles)

    def test_second_search_skipped_when_enough_exact_jobs(self):
        strict = [job(i, "Junior Python Developer") for i in range(30)]
        board = FakeBoard(strict, [])
        self.run_search(board, 1.5, 1)
        self.assertEqual(len(board.calls), 1)

    def test_default_is_65_and_both_sources_are_represented(self):
        from app.services.job_opportunity_service import DEFAULT_LIMIT
        self.assertEqual(DEFAULT_LIMIT, 65)
        adz = [dict(job(i, "Python Developer"), source="Adzuna") for i in range(90)]
        joo = [dict(job(1000 + i, "Python Developer"), source="Jooble") for i in range(20)]
        out = self.run_search(FakeBoard([], adz + joo), 2, 1, limit=DEFAULT_LIMIT)
        self.assertEqual(len(out), 65)
        sources = [j["source"] for j in out]
        self.assertEqual(sources.count("Jooble"), 20)       # all 20 included
        self.assertEqual(sources.count("Adzuna"), 45)

    def test_limit_is_respected_and_internal_fields_hidden(self):
        loose = [job(i, "Python Developer") for i in range(40)]
        out = self.run_search(FakeBoard([], loose), 2, 1, limit=12)
        self.assertEqual(len(out), 12)
        self.assertNotIn("_rank", out[0])


if __name__ == "__main__":
    unittest.main()
