"""
Real job-search service using the Adzuna API.

INDIA-FIRST JOB SEARCH

Responsibilities:
1. Search Adzuna India.
2. Search major Indian cities.
3. Prefer Indian job locations.
4. Reject clearly foreign jobs.
5. Remove duplicates.
6. Prefer Indian companies when possible.
7. Calculate resume-to-job skill matching.
8. Return JobOpportunity objects.

This service DOES NOT run the full MatchingEngine.
It performs lightweight matching specifically for
real external job postings.
"""

import re
import requests

from app.core.config import (
    ADZUNA_APP_ID,
    ADZUNA_APP_KEY,
    ADZUNA_COUNTRY,
    ADZUNA_RESULTS_PER_PAGE,
    MAX_JOB_RESULTS,
    INDIA_FIRST_JOBS,
    INDIAN_COMPANY_BOOST,
    INDIAN_LOCATION_BOOST,
)

from app.core.logger import logger

from app.jobs.job_opportunity import JobOpportunity


class JobSearchService:
    """
    Searches real job postings using Adzuna.

    Current strategy:
        INDIA FIRST

    Priority:

        Indian company + Indian location
                    ↓
        Any company + Indian location
                    ↓
        Indian company + other location

    Clearly foreign jobs are rejected.
    """

    BASE_URL = (
        "https://api.adzuna.com/v1/api/jobs"
    )

    # =========================================================
    # MAJOR INDIAN LOCATIONS
    # =========================================================

    INDIA_LOCATIONS = [
        "India",
        "Bangalore",
        "Bengaluru",
        "Hyderabad",
        "Pune",
        "Mumbai",
        "Delhi",
        "Delhi NCR",
        "Noida",
        "Gurgaon",
        "Gurugram",
        "Chennai",
        "Kolkata",
        "Ahmedabad",
        "Jaipur",
        "Chandigarh",
        "Indore",
        "Kochi",
        "Coimbatore",
        "Lucknow",
        "Bhubaneswar",
        "Thiruvananthapuram",
        "Mysore",
        "Mysuru",
        "Nagpur",
        "Surat",
        "Vadodara",
        "Visakhapatnam",
        "Patna",
        "Bhopal",
        "Ranchi",
    ]

    # =========================================================
    # FOREIGN LOCATIONS
    # =========================================================

    FOREIGN_LOCATION_KEYWORDS = [
        "united states",
        "united kingdom",
        "canada",
        "australia",
        "singapore",
        "germany",
        "france",
        "spain",
        "italy",
        "netherlands",
        "ireland",
        "europe",
        "european union",
        "latin america",
        "latam",
        "israel",
        "brazil",
        "mexico",
        "new zealand",
        "south africa",
        "usa",
        "uk",
    ]

    # =========================================================
    # INDIAN COMPANIES
    # =========================================================

    INDIAN_COMPANIES = [
        "tcs",
        "tata consultancy services",
        "infosys",
        "wipro",
        "hcltech",
        "hcl technologies",
        "tech mahindra",
        "ltimindtree",
        "lti mindtree",
        "mphasis",
        "persistent systems",
        "zoho",
        "freshworks",
        "razorpay",
        "paytm",
        "phonepe",
        "flipkart",
        "swiggy",
        "zomato",
        "meesho",
        "cred",
        "groww",
        "zerodha",
        "dream11",
        "byjus",
        "ola",
        "ola electric",
        "reliance",
        "reliance industries",
        "jio",
        "jio platforms",
        "adani",
        "walmart labs",
        "myntra",
        "ibm india",
        "amazon development centre india",
        "microsoft india",
        "google india",
        "oracle india",
        "samsung india",
        "accenture india",
        "capgemini india",
    ]

    def __init__(self):

        self.app_id = ADZUNA_APP_ID
        self.app_key = ADZUNA_APP_KEY
        self.country = ADZUNA_COUNTRY

        self.results_per_page = (
            ADZUNA_RESULTS_PER_PAGE
        )

        self.max_job_results = (
            MAX_JOB_RESULTS
        )

        self.india_first = (
            INDIA_FIRST_JOBS
        )

        self.indian_company_boost = (
            INDIAN_COMPANY_BOOST
        )

        self.indian_location_boost = (
            INDIAN_LOCATION_BOOST
        )

        logger.info(
            "JobSearchService initialized. "
            "country=%s india_first=%s",
            self.country,
            self.india_first,
        )

    # =========================================================
    # PUBLIC SEARCH
    # =========================================================

    def search(
        self,
        query,
        location=None,
        page=1,
        results_per_page=None,
        resume=None,
    ):
        """
        Search real Indian job postings.

        Returns:
            list[JobOpportunity]
        """

        if not self.app_id:
            raise RuntimeError(
                "ADZUNA_APP_ID is not configured."
            )

        if not self.app_key:
            raise RuntimeError(
                "ADZUNA_APP_KEY is not configured."
            )

        if not query:
            return []

        if results_per_page is None:
            results_per_page = (
                self.results_per_page
            )

        if self.country.lower() != "in":

            logger.warning(
                "ADZUNA_COUNTRY=%s. "
                "India-first search expects country='in'.",
                self.country,
            )

        # -----------------------------------------------------
        # Determine locations
        # -----------------------------------------------------

        if location:

            search_locations = [
                location
            ]

        else:

            search_locations = [
                "Bangalore",
                "Hyderabad",
                "Pune",
                "Mumbai",
                "Delhi NCR",
                "Noida",
                "Gurgaon",
                "Chennai",
                "Kolkata",
                "Ahmedabad",
                "Jaipur",
                "Kochi",
            ]

        url = (
            f"{self.BASE_URL}/"
            f"{self.country}/search/"
            f"{page}"
        )

        all_results = []

        # =====================================================
        # SEARCH EACH LOCATION
        # =====================================================

        for search_location in search_locations:

            params = {
                "app_id": self.app_id,
                "app_key": self.app_key,
                "results_per_page": results_per_page,
                "what": query,
                "where": search_location,
                "content-type": "application/json",
            }

            logger.info(
                "Searching Indian jobs: "
                "query='%s', location='%s'",
                query,
                search_location,
            )

            try:

                response = requests.get(
                    url,
                    params=params,
                    timeout=20,
                )

                response.raise_for_status()

                data = response.json()

            except requests.RequestException as error:

                logger.exception(
                    "Adzuna job search request failed."
                )

                raise RuntimeError(
                    f"Job search failed: {error}"
                ) from error

            except ValueError as error:

                logger.exception(
                    "Adzuna returned invalid JSON."
                )

                raise RuntimeError(
                    "Job provider returned invalid JSON."
                ) from error

            results = data.get(
                "results",
                [],
            )

            if isinstance(results, list):

                all_results.extend(
                    results
                )

        # =====================================================
        # PROCESS RESULTS
        # =====================================================

        opportunities = []

        seen_urls = set()

        for item in all_results:

            if not isinstance(item, dict):
                continue

            # -------------------------------------------------
            # Company
            # -------------------------------------------------

            company = item.get(
                "company",
                {},
            )

            if isinstance(company, dict):

                company_name = (
                    company.get(
                        "display_name",
                        "",
                    )
                    or ""
                )

            else:

                company_name = str(
                    company
                )

            # -------------------------------------------------
            # Location
            # -------------------------------------------------

            location_data = item.get(
                "location",
                {},
            )

            if isinstance(
                location_data,
                dict,
            ):

                location_name = (
                    location_data.get(
                        "display_name",
                        "",
                    )
                    or ""
                )

            else:

                location_name = str(
                    location_data
                )

            # -------------------------------------------------
            # URL
            # -------------------------------------------------

            job_url = (
                item.get(
                    "redirect_url",
                    "",
                )
                or ""
            )

            # -------------------------------------------------
            # Duplicate protection
            # -------------------------------------------------

            if job_url:

                if job_url in seen_urls:
                    continue

                seen_urls.add(
                    job_url
                )

            # -------------------------------------------------
            # Validate Indian location
            # -------------------------------------------------

            if not self._is_indian_job(
                location_name
            ):

                logger.info(
                    "Skipping foreign job: "
                    "%s | %s",
                    company_name,
                    location_name,
                )

                continue

            # -------------------------------------------------
            # Job fields
            # -------------------------------------------------

            title = (
                item.get(
                    "title",
                    "",
                )
                or ""
            )

            description = (
                item.get(
                    "description",
                    "",
                )
                or ""
            )

            # -------------------------------------------------
            # Calculate resume match
            # -------------------------------------------------

            match_information = (
                self._calculate_match(
                    resume,
                    title,
                    description,
                )
                if resume
                else {
                    "match_score": 0,
                    "matched_skills": [],
                    "missing_skills": [],
                    "why_suitable": (
                        "Resume matching is not "
                        "available for this job."
                    ),
                }
            )

            # -------------------------------------------------
            # Calculate India priority
            # -------------------------------------------------

            priority_score = (
                self._calculate_priority(
                    company_name,
                    location_name,
                )
            )

            # -------------------------------------------------
            # Create JobOpportunity
            # -------------------------------------------------

            opportunity = JobOpportunity(

                company=company_name,

                title=title,

                location=location_name,

                description=description,

                job_url=job_url,

                source="Adzuna",

                salary_min=item.get(
                    "salary_min"
                ),

                salary_max=item.get(
                    "salary_max"
                ),

                match_score=(
                    match_information[
                        "match_score"
                    ]
                ),

                matched_skills=(
                    match_information[
                        "matched_skills"
                    ]
                ),

                missing_skills=(
                    match_information[
                        "missing_skills"
                    ]
                ),

                why_suitable=[
                    match_information[
                        "why_suitable"
                    ]
                ],

                india_priority_score=(
                    priority_score
                ),

                is_indian_company=(
                    self._is_indian_company(
                        company_name
                    )
                ),
            )

            # Internal ranking metadata
            opportunity.india_priority = (
                priority_score
            )

            opportunities.append(
                opportunity
            )

        # =====================================================
        # SORT
        # =====================================================

        opportunities.sort(
            key=lambda job: (
                getattr(
                    job,
                    "match_score",
                    0,
                ),

                getattr(
                    job,
                    "india_priority_score",
                    0,
                ),

                getattr(
                    job,
                    "is_indian_company",
                    False,
                ),
            ),
            reverse=True,
        )

        # =====================================================
        # LIMIT
        # =====================================================

        opportunities = opportunities[
            : self.max_job_results
        ]

        logger.info(
            "India-first search returned %d jobs.",
            len(opportunities),
        )

        return opportunities

    # =========================================================
    # RESUME SKILL MATCHING
    # =========================================================

    @staticmethod
    def _calculate_match(
        resume,
        title,
        description,
    ):
        """
        Calculate lightweight resume-to-job matching.

        This is specifically for external job postings
        where we only have raw job text.

        Returns:
            match_score
            matched_skills
            missing_skills
            why_suitable
        """

        if not resume:

            return {
                "match_score": 0,
                "matched_skills": [],
                "missing_skills": [],
                "why_suitable": (
                    "Resume information is not available."
                ),
            }

        resume_skills = set()

        for skill in getattr(
            resume,
            "skills",
            []
        ):

            if not isinstance(
                skill,
                str
            ):
                continue

            skill = skill.strip().lower()

            if skill:

                resume_skills.add(
                    skill
                )

        job_text = (
            f"{title} {description}"
        ).lower()

        matched_skills = []
        missing_skills = []

        for skill in resume_skills:

            if (
                JobSearchService._skill_in_text(
                    skill,
                    job_text
                )
            ):

                matched_skills.append(
                    skill
                )

            else:

                missing_skills.append(
                    skill
                )

        matched_skills = sorted(
            matched_skills
        )[:10]

        missing_skills = sorted(
            missing_skills
        )[:8]

        if resume_skills:

            score = (
                len(matched_skills)
                /
                len(resume_skills)
                * 100
            )

        else:

            score = 0

        score = round(
            min(score, 100),
            1
        )

        # -----------------------------------------------------
        # Why suitable
        # -----------------------------------------------------

        if score >= 75:

            why_suitable = (
                "Strong alignment with the "
                "skills detected in your resume."
            )

        elif score >= 50:

            why_suitable = (
                "Good potential match with "
                "several relevant resume skills."
            )

        elif score >= 30:

            why_suitable = (
                "Some of your skills match this "
                "role, but additional skills may "
                "be required."
            )

        elif score > 0:

            why_suitable = (
                "A few resume skills match this "
                "job, but the overall overlap is limited."
            )

        else:

            why_suitable = (
                "No direct resume-skill overlap "
                "was detected in this job posting."
            )

        return {

            "match_score": score,

            "matched_skills":
                matched_skills,

            "missing_skills":
                missing_skills,

            "why_suitable":
                why_suitable,
        }

    # =========================================================
    # SKILL TEXT MATCHING
    # =========================================================

    @staticmethod
    def _skill_in_text(
        skill,
        text,
    ):
        """
        Safely determine whether a skill occurs in job text.

        Handles skills such as:

            Python
            C++
            C#
            .NET
            FastAPI
            Node.js
            SQL
            Java
            Docker
        """

        skill = (
            str(skill)
            .strip()
            .lower()
        )

        text = (
            str(text)
            .lower()
        )

        if not skill or not text:
            return False

        # Multi-word / symbol-heavy skills
        if (
            any(
                character in skill
                for character in [
                    "+",
                    "#",
                    ".",
                    "-",
                    "/",
                ]
            )
        ):

            return skill in text

        # Word-boundary matching
        pattern = (
            r"\b"
            + re.escape(skill)
            + r"\b"
        )

        return bool(
            re.search(
                pattern,
                text,
            )
        )

    # =========================================================
    # INDIAN JOB CHECK
    # =========================================================

    def _is_indian_job(
        self,
        location,
    ):
        """
        Return True only for jobs that appear to be
        located in India.
        """

        if not location:
            return False

        location_text = (
            str(location)
            .strip()
            .lower()
        )

        # Reject foreign locations
        for keyword in (
            self.FOREIGN_LOCATION_KEYWORDS
        ):

            if keyword in location_text:

                return False

        # Accept known Indian locations
        for indian_location in (
            self.INDIA_LOCATIONS
        ):

            if (
                indian_location.lower()
                in location_text
            ):

                return True

        # Explicit India
        if "india" in location_text:

            return True

        return False

    # =========================================================
    # INDIAN COMPANY CHECK
    # =========================================================

    def _is_indian_company(
        self,
        company,
    ):
        """
        Determine whether the company matches our
        Indian-company preference list.
        """

        if not company:
            return False

        company_text = (
            str(company)
            .strip()
            .lower()
        )

        for indian_company in (
            self.INDIAN_COMPANIES
        ):

            if (
                indian_company
                in company_text
            ):

                return True

        return False

    # =========================================================
    # PRIORITY SCORE
    # =========================================================

    def _calculate_priority(
        self,
        company,
        location,
    ):
        """
        Calculate India-first priority.

        Higher score = shown earlier.
        """

        score = 0

        if self._is_indian_job(
            location
        ):

            score += (
                self.indian_location_boost
            )

        if self._is_indian_company(
            company
        ):

            score += (
                self.indian_company_boost
            )

        return score