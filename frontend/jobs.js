/* =========================================================
   JOB SEARCH PAGE  (public landing page)

   Talks to the backend endpoint (built in Phase 1):

     GET {API_BASE_URL}/jobs/search
         ?q=python developer
         &location=Kolkata
         &level=fresher|junior|mid|senior
         &remote=true
         &posted_within=1|7|30
         &sort=relevance|date
         &page=1
         &limit=30

   Expected response:

     {
       "jobs": [ { id, title, company, location, salary_min,
                   salary_max, posted_at, source, url,
                   description, skills, level, remote } ],
       "total": 128,
       "page": 1,
       "has_more": true
     }

   Every field is optional - the page copes with missing data.
   Old field names (job_url, matched_skills, match_score) from
   the existing JobOpportunity model are understood as well.

   Preview without a backend:  open the site with  ?demo=1
========================================================= */

(function () {
    "use strict";

    /* -----------------------------------------------------
       SETTINGS
    ----------------------------------------------------- */

    const PAGE_SIZE = 30;
    const REQUEST_TIMEOUT_MS = 15000;
    const SAVED_KEY = "careerpilot.savedJobs";
    const MAX_SAVED = 100;
    const DEMO = new URLSearchParams(window.location.search).has("demo");

    const CITIES = [
        "Remote", "Bangalore", "Hyderabad", "Pune", "Mumbai",
        "Delhi NCR", "Noida", "Gurgaon", "Chennai", "Kolkata",
        "Ahmedabad", "Jaipur", "Kochi", "Indore", "Chandigarh"
    ];

    const POPULAR_SEARCHES = [
        { label: "Python Developer", q: "python developer" },
        { label: "Data Analyst", q: "data analyst" },
        { label: "Java Developer", q: "java developer" },
        { label: "DevOps Engineer", q: "devops engineer" },
        { label: "Fresher jobs", q: "software engineer", level: "fresher" },
        { label: "Remote jobs", q: "developer", remote: true }
    ];

    /* -----------------------------------------------------
       STATE
    ----------------------------------------------------- */

    const state = {
        view: "search",          // "search" | "saved"
        params: null,            // snapshot of the last search
        jobs: [],
        total: 0,
        page: 1,
        hasMore: false,
        loading: false
    };

    let activeController = null;
    let requestCounter = 0;
    let saved = loadSaved();


    /* -----------------------------------------------------
       SMALL HELPERS
    ----------------------------------------------------- */

    function $(id) {
        return document.getElementById(id);
    }

    function make(tag, className, text) {
        const node = document.createElement(tag);
        if (className) node.className = className;
        if (text !== undefined && text !== null) node.textContent = text;
        return node;
    }

    function clear(node) {
        while (node && node.firstChild) node.removeChild(node.firstChild);
    }

    function show(node, visible) {
        if (!node) return;
        if (visible) node.removeAttribute("hidden");
        else node.setAttribute("hidden", "");
    }

    function announce(message) {
        const live = $("jx-status");
        if (live) live.textContent = message;
    }

    // Remove HTML tags safely (DOMParser never runs scripts).
    function stripHtml(value) {
        if (!value) return "";
        const doc = new DOMParser().parseFromString(String(value), "text/html");
        return (doc.body.textContent || "").replace(/\s+/g, " ").trim();
    }

    function truncate(text, max) {
        if (text.length <= max) return text;
        return text.slice(0, max).replace(/\s+\S*$/, "") + "…";
    }

    function safeUrl(value) {
        try {
            const url = new URL(String(value));
            return (url.protocol === "http:" || url.protocol === "https:")
                ? url.href : "";
        } catch (error) {
            return "";
        }
    }

    function formatNumber(value) {
        return Number(value).toLocaleString("en-IN");
    }


    /* -----------------------------------------------------
       NORMALISE ONE JOB FROM THE API
    ----------------------------------------------------- */

    function formatSalary(min, max) {
        const low = Number(min) || 0;
        const high = Number(max) || 0;
        if (!low && !high) return "";

        const lpa = (value) =>
            String(Math.round((value / 100000) * 10) / 10).replace(/\.0$/, "");

        const top = Math.max(low, high);

        if (top >= 100000) {
            if (low && high && low !== high) {
                return `₹${lpa(low)}–${lpa(high)} LPA`;
            }
            return `₹${lpa(top)} LPA`;
        }

        if (low && high && low !== high) {
            return `₹${formatNumber(low)}–${formatNumber(high)}`;
        }
        return `₹${formatNumber(top)}`;
    }

    function timeAgo(value) {
        if (!value) return "";
        const date = new Date(value);
        if (isNaN(date.getTime())) return "";

        const days = Math.floor((Date.now() - date.getTime()) / 86400000);

        if (days <= 0) return "Posted today";
        if (days === 1) return "Posted 1 day ago";
        if (days < 7) return `Posted ${days} days ago`;
        if (days < 30) {
            const weeks = Math.floor(days / 7);
            return `Posted ${weeks} week${weeks > 1 ? "s" : ""} ago`;
        }
        const months = Math.floor(days / 30);
        return `Posted ${months} month${months > 1 ? "s" : ""} ago`;
    }

    function normalizeJob(raw) {
        raw = raw || {};

        const title = String(raw.title || "").trim() || "Untitled role";
        const company = String(raw.company || "").trim();
        const location = String(raw.location || "").trim();
        const url = safeUrl(raw.url || raw.job_url || raw.link);

        const salary = raw.salary
            ? String(raw.salary)
            : formatSalary(raw.salary_min, raw.salary_max);

        const skillsSource = Array.isArray(raw.skills) && raw.skills.length
            ? raw.skills
            : (Array.isArray(raw.matched_skills) ? raw.matched_skills : []);

        const skills = skillsSource
            .map((skill) => String(skill).trim())
            .filter(Boolean)
            .slice(0, 5);

        const remote = Boolean(raw.remote) ||
            /\bremote\b|work from home|\bwfh\b/i.test(`${location} ${title}`);

        const match = Math.round(Number(raw.match_score) || 0);

        return {
            id: String(raw.id || url || `${title}|${company}|${location}`),
            title,
            company,
            location,
            url,
            salary,
            posted: timeAgo(raw.posted_at || raw.created || raw.date),
            postedAt: raw.posted_at || raw.created || raw.date || "",
            source: String(raw.source || "").trim(),
            snippet: truncate(stripHtml(raw.description || raw.snippet), 220),
            skills,
            level: String(raw.level || "").trim(),
            remote,
            match: match > 0 ? Math.min(match, 100) : 0
        };
    }


    /* -----------------------------------------------------
       SAVED JOBS  (stored in this browser)
    ----------------------------------------------------- */

    function loadSaved() {
        try {
            const data = JSON.parse(localStorage.getItem(SAVED_KEY) || "[]");
            return Array.isArray(data) ? data : [];
        } catch (error) {
            return [];
        }
    }

    function persistSaved() {
        try {
            localStorage.setItem(SAVED_KEY, JSON.stringify(saved));
        } catch (error) {
            /* storage full or blocked - saving just won't persist */
        }
    }

    function isSaved(id) {
        return saved.some((job) => job.id === id);
    }

    function toggleSaved(job) {
        if (isSaved(job.id)) {
            saved = saved.filter((item) => item.id !== job.id);
        } else {
            saved.unshift(job);
            saved = saved.slice(0, MAX_SAVED);
        }
        persistSaved();
        updateSavedCount();
    }

    function updateSavedCount() {
        const label = $("jx-saved-count");
        if (label) label.textContent = String(saved.length);
    }


    /* -----------------------------------------------------
       FORM  <->  PARAMS  <->  URL
    ----------------------------------------------------- */

    function readForm() {
        return {
            q: $("jx-q").value.trim(),
            location: $("jx-location").value.trim(),
            level: $("jx-level").value,
            remote: $("jx-remote").checked,
            posted: $("jx-posted").value,
            sort: $("jx-sort").value
        };
    }

    function writeForm(params) {
        $("jx-q").value = params.q || "";
        $("jx-location").value = params.location || "";
        $("jx-level").value = params.level || "";
        $("jx-remote").checked = Boolean(params.remote);
        $("jx-posted").value = params.posted || "";
        $("jx-sort").value = params.sort || "relevance";
    }

    function paramsFromUrl() {
        const url = new URLSearchParams(window.location.search);
        return {
            q: url.get("q") || "",
            location: url.get("location") || "",
            level: url.get("level") || "",
            remote: url.get("remote") === "1",
            posted: url.get("posted") || "",
            sort: url.get("sort") || "relevance"
        };
    }

    function pushUrl(params) {
        const url = new URLSearchParams();
        if (DEMO) url.set("demo", "1");
        if (params.q) url.set("q", params.q);
        if (params.location) url.set("location", params.location);
        if (params.level) url.set("level", params.level);
        if (params.remote) url.set("remote", "1");
        if (params.posted) url.set("posted", params.posted);
        if (params.sort && params.sort !== "relevance") {
            url.set("sort", params.sort);
        }
        const query = url.toString();
        const next = window.location.pathname + (query ? `?${query}` : "");
        try {
            window.history.pushState(null, "", next);
        } catch (error) {
            /* some hosts block history changes - ignore */
        }
    }

    function hasFilters(params) {
        return Boolean(params.level || params.remote || params.posted);
    }

    function describeSearch(params) {
        const parts = [];
        if (params.q) parts.push(`“${params.q}”`);
        if (params.location) parts.push(`in ${params.location}`);
        return parts.join(" ");
    }


    /* -----------------------------------------------------
       TALK TO THE BACKEND
    ----------------------------------------------------- */

    function apiBase() {
      return (
        typeof API_BASE_URL !== "undefined" && API_BASE_URL
            ? API_BASE_URL
            : "https://resume-analysis-web.onrender.com"
      ).replace(/\/+$/, "");
    }

    async function fetchJobs(params, page, signal) {
        if (DEMO) return demoSearch(params, page, signal);

        const query = new URLSearchParams();
        query.set("q", params.q);
        if (params.location) query.set("location", params.location);
        if (params.level) query.set("level", params.level);
        if (params.remote) query.set("remote", "true");
        if (params.posted) query.set("posted_within", params.posted);
        query.set("sort", params.sort || "relevance");
        query.set("page", String(page));
        query.set("limit", String(PAGE_SIZE));

        const timeout = new AbortController();
        const timer = setTimeout(() => timeout.abort("timeout"), REQUEST_TIMEOUT_MS);
        signal.addEventListener("abort", () => timeout.abort("cancelled"));

        let response;
        try {
            response = await fetch(
                `${apiBase()}/jobs/search?${query.toString()}`,
                { signal: timeout.signal, headers: { Accept: "application/json" } }
            );
        } catch (error) {
            if (signal.aborted) throw error;
            const slow = timeout.signal.reason === "timeout";
            throw new Error(slow
                ? "The search is taking too long. Please try again."
                : "We couldn't reach the job service. Check your internet and try again.");
        } finally {
            clearTimeout(timer);
        }

        if (!response.ok) {
            // Only a 400 carries a message meant for the visitor.
            // 404 / 500 etc. get a friendly sentence instead of server wording.
            let detail = "";
            if (response.status === 400) {
                try {
                    const body = await response.json();
                    detail = typeof body.detail === "string" ? body.detail : "";
                } catch (error) { /* not JSON */ }
            }
            throw new Error(detail || "Job search isn't available right now. Please try again in a moment.");
        }

        const data = await response.json();
        const list = Array.isArray(data) ? data : (data.jobs || data.results || []);

        return {
            jobs: list.map(normalizeJob),
            total: Number.isFinite(Number(data.total)) ? Number(data.total) : list.length,
            hasMore: typeof data.has_more === "boolean"
                ? data.has_more
                : list.length >= PAGE_SIZE
        };
    }


    /* -----------------------------------------------------
       SEARCH FLOW
    ----------------------------------------------------- */

    function startSearch(options) {
        const push = !options || options.push !== false;
        const params = readForm();

        if (!params.q && !params.location) {
            state.params = null;
            state.jobs = [];
            renderResults();
            announce("Please type a job title or skill to search.");
            const field = $("jx-q").closest(".jx-field");
            field.classList.add("jx-nudge");
            setTimeout(() => field.classList.remove("jx-nudge"), 700);
            $("jx-q").focus();
            return;
        }

        state.view = "search";
        state.params = params;
        state.page = 1;
        state.jobs = [];
        state.total = 0;
        state.hasMore = false;

        if (push) pushUrl(params);
        runSearch(1);
    }

    async function runSearch(page) {
        if (activeController) activeController.abort("cancelled");
        activeController = new AbortController();
        const controller = activeController;
        const thisRequest = ++requestCounter;

        state.loading = true;
        const firstPage = page === 1;

        if (firstPage) {
            renderResults();
            showSkeletons();
            announce("Loading jobs…");
        } else {
            setMoreButton("loading");
        }

        try {
            const result = await fetchJobs(state.params, page, controller.signal);
            if (thisRequest !== requestCounter) return;

            state.loading = false;
            state.page = page;
            state.total = result.total;
            state.hasMore = result.hasMore;
            state.jobs = firstPage ? result.jobs : state.jobs.concat(result.jobs);

            hideSkeletons();
            renderResults(firstPage ? 0 : state.jobs.length - result.jobs.length);

            if (!state.jobs.length) {
                showEmptyState();
                announce("No jobs found.");
            } else {
                announce(`Showing ${state.jobs.length} of ${state.total} jobs.`);
            }
        } catch (error) {
            if (controller.signal.aborted || thisRequest !== requestCounter) return;

            state.loading = false;
            hideSkeletons();

            if (firstPage) {
                renderResults();
                show($("jx-results-head"), false);   // no "0 jobs found" above an error
                showMessage({
                    icon: "⚠️",
                    title: "Something went wrong",
                    text: error.message || "Please try again.",
                    action: { label: "Try again", run: () => runSearch(1) }
                });
            } else {
                setMoreButton("error");
            }
            announce("Could not load jobs.");
        }
    }

    function loadMore() {
        if (state.loading || !state.hasMore) return;
        runSearch(state.page + 1);
    }


    /* -----------------------------------------------------
       RENDERING
    ----------------------------------------------------- */

    function renderHeader() {
        const heading = $("jx-count");
        const sub = $("jx-count-sub");
        const tools = $("jx-result-tools");
        if (!heading || !sub) return;

        if (state.view === "saved") {
            heading.textContent = saved.length === 1
                ? "1 saved job"
                : `${saved.length} saved jobs`;
            sub.textContent = "Saved in this browser.";
            show(tools, false);
            show($("jx-results-head"), true);
            return;
        }

        if (!state.params) {
            show($("jx-results-head"), false);
            return;
        }

        show($("jx-results-head"), true);
        show(tools, true);

        if (state.loading && !state.jobs.length) {
            heading.textContent = "Searching…";
            sub.textContent = describeSearch(state.params);
            return;
        }

        const shown = state.total || state.jobs.length;
        heading.textContent = shown === 1
            ? "1 job found"
            : `${formatNumber(shown)} jobs found`;
        sub.textContent = describeSearch(state.params);
    }

    function renderResults(fromIndex) {
        const list = $("jx-results");
        const jobs = state.view === "saved" ? saved : state.jobs;

        hideMessage();
        renderHeader();
        show($("jx-welcome"), !state.params && state.view !== "saved");

        if (fromIndex === undefined || fromIndex === 0 || state.view === "saved") {
            clear(list);
            fromIndex = 0;
        }

        jobs.slice(fromIndex).forEach((job) => list.appendChild(createCard(job)));

        if (state.view === "saved") {
            setMoreButton("hidden");
            if (!saved.length) {
                showMessage({
                    icon: "♡",
                    title: "No saved jobs yet",
                    text: "Tap “Save” on any job to keep it here for later.",
                    action: { label: "Back to search", run: leaveSavedView }
                });
            }
            return;
        }

        setMoreButton(state.hasMore ? "ready" : "hidden");
    }

    function createCard(job) {
        const card = make("article", "jx-card");

        /* title row */
        const head = make("div", "jx-card-head");
        const titleBox = make("div", "jx-card-title");
        titleBox.appendChild(make("h3", null, job.title));

        const company = make("p", "jx-company");
        company.appendChild(make("strong", null, job.company || "Company not listed"));
        if (job.location) {
            company.appendChild(make("span", "jx-dot", "•"));
            company.appendChild(make("span", null, job.location));
        }
        titleBox.appendChild(company);
        head.appendChild(titleBox);

        if (job.match) {
            const badge = make("div", "jx-match", `${job.match}%`);
            badge.appendChild(make("small", null, "match"));
            badge.title = "How well this job matches your resume";
            head.appendChild(badge);
        }
        card.appendChild(head);

        /* meta chips */
        const meta = make("ul", "jx-meta");
        const addMeta = (text, modifier) => {
            if (!text) return;
            meta.appendChild(make("li", modifier ? `jx-tag ${modifier}` : "jx-tag", text));
        };
        addMeta(job.salary ? `💰 ${job.salary}` : "", "jx-tag-salary");
        addMeta(job.remote ? "🏠 Remote" : "", "jx-tag-remote");
        addMeta(job.level ? capitalize(job.level) : "");
        addMeta(job.posted ? `🕒 ${job.posted}` : "");
        if (meta.children.length) card.appendChild(meta);

        /* snippet */
        if (job.snippet) card.appendChild(make("p", "jx-snippet", job.snippet));

        /* skills */
        if (job.skills.length) {
            const skills = make("ul", "jx-skills");
            job.skills.forEach((skill) => skills.appendChild(make("li", null, skill)));
            card.appendChild(skills);
        }

        /* actions */
        const actions = make("div", "jx-card-actions");

        if (job.url) {
            const apply = make("a", "jx-apply", "Apply now ↗");
            apply.href = job.url;
            apply.target = "_blank";
            apply.rel = "noopener noreferrer nofollow";
            apply.setAttribute("aria-label", `Apply for ${job.title} at ${job.company || "this company"} (opens in a new tab)`);
            actions.appendChild(apply);
        } else {
            const none = make("span", "jx-apply jx-apply-disabled", "Link unavailable");
            actions.appendChild(none);
        }

        const save = make("button", "jx-save");
        save.type = "button";
        const paintSave = () => {
            const on = isSaved(job.id);
            save.textContent = on ? "♥ Saved" : "♡ Save";
            save.classList.toggle("is-saved", on);
            save.setAttribute("aria-pressed", on ? "true" : "false");
            save.setAttribute("aria-label", `${on ? "Remove" : "Save"} ${job.title}`);
        };
        paintSave();
        save.addEventListener("click", () => {
            toggleSaved(job);
            paintSave();
            if (state.view === "saved") {
                renderResults();
            }
        });
        actions.appendChild(save);

        if (job.source) actions.appendChild(make("span", "jx-source", `via ${job.source}`));

        card.appendChild(actions);
        return card;
    }

    function capitalize(text) {
        return text.charAt(0).toUpperCase() + text.slice(1);
    }

    function showSkeletons() {
        const box = $("jx-skeletons");
        clear(box);
        for (let i = 0; i < 5; i++) {
            const card = make("div", "jx-skeleton");
            card.appendChild(make("div", "jx-sk-line jx-sk-title"));
            card.appendChild(make("div", "jx-sk-line jx-sk-sub"));
            card.appendChild(make("div", "jx-sk-line"));
            card.appendChild(make("div", "jx-sk-line jx-sk-short"));
            box.appendChild(card);
        }
        show(box, true);
        show($("jx-state"), false);
    }

    function hideSkeletons() {
        show($("jx-skeletons"), false);
    }

    function setMoreButton(mode) {
        const button = $("jx-more");
        if (!button) return;

        if (mode === "hidden") {
            show(button, false);
            return;
        }

        show(button, true);
        button.disabled = mode === "loading";

        if (mode === "loading") button.textContent = "Loading more jobs…";
        else if (mode === "error") button.textContent = "Couldn't load more — tap to retry";
        else button.textContent = "Load more jobs";
    }

    /* empty / error / info card */

    function showMessage(options) {
        const box = $("jx-state");
        clear(box);

        box.appendChild(make("div", "jx-state-icon", options.icon || "🔎"));
        box.appendChild(make("h3", null, options.title));
        if (options.text) box.appendChild(make("p", null, options.text));

        const row = make("div", "jx-state-actions");

        if (options.action) {
            const button = make("button", "jx-btn jx-btn-primary", options.action.label);
            button.type = "button";
            button.addEventListener("click", options.action.run);
            row.appendChild(button);
        }

        if (options.extra) {
            const button = make("button", "jx-btn", options.extra.label);
            button.type = "button";
            button.addEventListener("click", options.extra.run);
            row.appendChild(button);
        }

        if (row.children.length) box.appendChild(row);

        show(box, true);
        setMoreButton("hidden");
    }

    function hideMessage() {
        show($("jx-state"), false);
    }

    function showEmptyState() {
        const params = state.params || {};
        const action = hasFilters(params)
            ? {
                label: "Clear filters",
                run: () => {
                    $("jx-level").value = "";
                    $("jx-remote").checked = false;
                    $("jx-posted").value = "";
                    startSearch();
                }
            }
            : null;

        const extra = params.location
            ? {
                label: "Search all locations",
                run: () => {
                    $("jx-location").value = "";
                    startSearch();
                }
            }
            : null;

        showMessage({
            icon: "🧐",
            title: "No jobs found",
            text: "Try a broader title (for example “developer” instead of “senior python backend developer”), check the spelling, or remove a filter.",
            action: action || extra,
            extra: action ? extra : null
        });
    }


    /* -----------------------------------------------------
       SAVED VIEW
    ----------------------------------------------------- */

    function openSavedView() {
        state.view = "saved";
        renderResults();
        announce(`${saved.length} saved jobs.`);
        $("jx-results-head").scrollIntoView({ behavior: "smooth", block: "start" });
    }

    function leaveSavedView() {
        state.view = "search";
        if (state.params) {
            renderResults();
            if (!state.jobs.length && !state.loading) showEmptyState();
        } else {
            clear($("jx-results"));
            show($("jx-results-head"), false);
            hideMessage();
            setMoreButton("hidden");
        }
    }

    function toggleSavedView() {
        if (state.view === "saved") leaveSavedView();
        else openSavedView();
        $("jx-saved-toggle").setAttribute("aria-pressed", state.view === "saved" ? "true" : "false");
    }


    /* -----------------------------------------------------
       PAGE SWITCHING  (used by app.js)
    ----------------------------------------------------- */

    window.showJobsHome = function () {
        const home = $("jx-home");
        if (home) home.style.display = "block";

        ["login-section", "dashboard-section"].forEach((id) => {
            const node = $(id);
            if (node) node.style.display = "none";
        });

        window.scrollTo(0, 0);
    };

    window.hideJobsHome = function () {
        const home = $("jx-home");
        if (home) home.style.display = "none";
    };

    window.updateJobsAuthUI = function (user) {
        const button = $("jx-auth-button");
        if (!button) return;

        if (user) {
            const first = String(user.name || "").trim().split(/\s+/)[0];
            button.textContent = first ? `👤 ${first}` : "👤 My workspace";
            button.title = "Open your resume workspace";
            button.dataset.mode = "workspace";
        } else {
            button.textContent = "Login";
            button.title = "Sign in to analyse your resume and track applications";
            button.dataset.mode = "signin";
        }
    };


    /* -----------------------------------------------------
       DEMO DATA  (only used with ?demo=1)
    ----------------------------------------------------- */

    const DEMO_ROLES = [
        ["Python Developer", ["Python", "Django", "SQL"], "junior"],
        ["Backend Engineer", ["Python", "FastAPI", "PostgreSQL"], "mid"],
        ["Data Analyst", ["SQL", "Excel", "Power BI"], "junior"],
        ["Java Developer", ["Java", "Spring Boot", "MySQL"], "mid"],
        ["DevOps Engineer", ["Docker", "AWS", "CI/CD"], "mid"],
        ["Senior Software Engineer", ["Java", "Microservices", "AWS"], "senior"],
        ["Software Engineer Trainee", ["Python", "Java", "SQL"], "fresher"],
        ["Machine Learning Engineer", ["Python", "TensorFlow", "NumPy"], "mid"],
        ["Full Stack Developer", ["React", "Node.js", "MongoDB"], "junior"],
        ["Tech Lead", ["System Design", "Python", "Leadership"], "senior"]
    ];

    const DEMO_COMPANIES = [
        "Infosys", "TCS", "Wipro", "Zoho", "Freshworks", "Razorpay",
        "Swiggy", "Flipkart", "Paytm", "HCLTech", "Cognizant", "Capgemini"
    ];

    const DEMO_JOBS = Array.from({ length: 64 }, (_, i) => {
        const role = DEMO_ROLES[i % DEMO_ROLES.length];
        const city = CITIES[(i * 5) % CITIES.length];
        const days = (i * 3) % 35;
        const base = { fresher: 3, junior: 6, mid: 12, senior: 24 }[role[2]];
        return normalizeJob({
            id: `demo-${i}`,
            title: role[0],
            company: DEMO_COMPANIES[(i * 7) % DEMO_COMPANIES.length],
            location: city === "Remote" ? "Remote, India" : `${city}, India`,
            salary_min: (base + (i % 4)) * 100000,
            salary_max: (base + (i % 4) + 4) * 100000,
            posted_at: new Date(Date.now() - days * 86400000).toISOString(),
            source: i % 2 ? "Adzuna" : "Jooble",
            url: `https://example.com/demo-job/${i}`,
            description: `<p>We are hiring a <b>${role[0]}</b> to join our growing team. You will work with ${role[1].join(", ")} and ship features used by thousands of customers every day.</p>`,
            skills: role[1],
            level: role[2],
            remote: city === "Remote"
        });
    });

    function demoSearch(params, page, signal) {
        return new Promise((resolve, reject) => {
            const timer = setTimeout(() => {
                const words = params.q.toLowerCase().split(/\s+/).filter(Boolean);
                const place = params.location.toLowerCase();
                const maxDays = Number(params.posted) || 0;

                let list = DEMO_JOBS.filter((job) => {
                    const haystack = `${job.title} ${job.skills.join(" ")} ${job.snippet} ${job.level}`.toLowerCase();
                    if (!words.every((word) => haystack.includes(word))) return false;
                    if (place && !job.location.toLowerCase().includes(place)) return false;
                    if (params.level && job.level !== params.level) return false;
                    if (params.remote && !job.remote) return false;
                    if (maxDays) {
                        const age = (Date.now() - new Date(job.postedAt).getTime()) / 86400000;
                        if (age > maxDays) return false;
                    }
                    return true;
                });

                if (params.sort === "date") {
                    list = list.slice().sort((a, b) => new Date(b.postedAt) - new Date(a.postedAt));
                }

                const start = (page - 1) * PAGE_SIZE;
                resolve({
                    jobs: list.slice(start, start + PAGE_SIZE),
                    total: list.length,
                    hasMore: start + PAGE_SIZE < list.length
                });
            }, 700);

            signal.addEventListener("abort", () => {
                clearTimeout(timer);
                reject(new DOMException("Aborted", "AbortError"));
            });
        });
    }


    /* -----------------------------------------------------
       START UP
    ----------------------------------------------------- */

    function buildChips() {
        const box = $("jx-chips");
        clear(box);

        POPULAR_SEARCHES.forEach((item) => {
            const chip = make("button", "jx-chip", item.label);
            chip.type = "button";
            chip.addEventListener("click", () => {
                writeForm({
                    q: item.q,
                    location: $("jx-location").value.trim(),
                    level: item.level || "",
                    remote: Boolean(item.remote),
                    posted: "",
                    sort: "relevance"
                });
                startSearch();
            });
            box.appendChild(chip);
        });
    }

    function buildCityList() {
        const list = $("jx-city-list");
        clear(list);
        CITIES.forEach((city) => {
            const option = document.createElement("option");
            option.value = city;
            list.appendChild(option);
        });
    }

    function init() {
        if (!$("jx-home")) return;

        buildChips();
        buildCityList();
        updateSavedCount();
        window.updateJobsAuthUI(null);
        show($("jx-demo-banner"), DEMO);

        $("jx-form").addEventListener("submit", (event) => {
            event.preventDefault();
            startSearch();
        });

        ["jx-level", "jx-posted", "jx-sort", "jx-remote"].forEach((id) => {
            $(id).addEventListener("change", () => {
                if (state.params || $("jx-q").value.trim() || $("jx-location").value.trim()) {
                    startSearch();
                }
            });
        });

        $("jx-clear").addEventListener("click", () => {
            $("jx-level").value = "";
            $("jx-remote").checked = false;
            $("jx-posted").value = "";
            $("jx-sort").value = "relevance";
            if (state.params) startSearch();
        });

        $("jx-more").addEventListener("click", loadMore);
        $("jx-saved-toggle").addEventListener("click", toggleSavedView);

        $("jx-auth-button").addEventListener("click", (event) => {
            const mode = event.currentTarget.dataset.mode;
            if (mode === "workspace" && typeof showDashboard === "function" && currentUser) {
                showDashboard(currentUser);
            } else if (typeof showLogin === "function") {
                showLogin();
            }
            window.scrollTo(0, 0);
        });

        window.addEventListener("popstate", () => {
            const params = paramsFromUrl();
            writeForm(params);
            if (params.q || params.location) startSearch({ push: false });
        });

        const initial = paramsFromUrl();
        writeForm(initial);
        if (initial.q || initial.location) startSearch({ push: false });
    }

    document.addEventListener("DOMContentLoaded", init);
})();
