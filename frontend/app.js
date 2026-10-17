// Same-origin by default: the backend serves this page, so every API call
// goes to whatever address the site was opened from (Render, localhost...).
// Only set window.__API_BASE_URL__ (before this script) if the frontend is
// hosted separately from the backend.
const API_BASE_URL = (window.__API_BASE_URL__ || "").replace(/\/+$/, "");

let currentUser = null;
let uploadedResumePath = null;
let latestAnalysisData = null;
let analysisInProgress = false;
let analysisRunId = 0;


/* =========================================================
   INITIALIZATION
========================================================= */

document.addEventListener("DOMContentLoaded", () => {
    initializeApp();
    initializeExtendedFeatures();
});


/* =========================================================
   ACCESSIBLE RESUME DROPZONE
========================================================= */

function initializeResumeDropzone(fileInput) {
    const dropzone = document.querySelector(".upload-area");
    if (!dropzone || !fileInput) return;

    ["dragenter", "dragover"].forEach((eventName) => {
        dropzone.addEventListener(eventName, (event) => {
            event.preventDefault();
            dropzone.classList.add("is-dragover");
        });
    });

    ["dragleave", "drop"].forEach((eventName) => {
        dropzone.addEventListener(eventName, (event) => {
            event.preventDefault();
            dropzone.classList.remove("is-dragover");
        });
    });

    dropzone.addEventListener("drop", (event) => {
        const file = event.dataTransfer?.files?.[0];
        if (!file) return;

        const extension = file.name.split(".").pop().toLowerCase();
        if (!["pdf", "docx"].includes(extension)) {
            alert("Please drop a PDF or DOCX resume.");
            return;
        }

        const transfer = new DataTransfer();
        transfer.items.add(file);
        fileInput.files = transfer.files;
        fileInput.dispatchEvent(new Event("change", { bubbles: true }));
    });
}


function initializeApp() {

    const loginButton =
        document.getElementById("google-login-button");

    const logoutButton =
        document.getElementById("logout-button");

    const resumeFile =
        document.getElementById("resume-file");

    const analyzeButton =
        document.getElementById("analyze-button");


    if (loginButton) {
        loginButton.addEventListener(
            "click",
            loginWithGoogle
        );
    }


    if (logoutButton) {
        logoutButton.addEventListener(
            "click",
            logout
        );
    }


    if (resumeFile) {
        resumeFile.addEventListener(
            "change",
            handleFileSelection
        );
    }

    initializeResumeDropzone(resumeFile);


    if (analyzeButton) {
        analyzeButton.addEventListener(
            "click",
            analyzeResume
        );
    }


    checkAuthentication();
}


/* =========================================================
   AUTHENTICATION
========================================================= */

async function checkAuthentication() {

    try {

        const response = await fetch(
            `${API_BASE_URL}/auth/me`,
            {
                method: "GET",
                credentials: "include"
            }
        );


        if (!response.ok) {
            showJobsHome();
            return;
        }


        const data =
            await readJsonResponse(response);


        /*
         * Support both:
         *
         * { authenticated: true, user: {...} }
         *
         * and:
         *
         * { name: "...", email: "..." }
         */

        if (data.authenticated === false) {
            showJobsHome();
            return;
        }


        currentUser =
            data.user ||
            data;


        updateUserUI(currentUser);
        updateJobsAuthUI(currentUser);
        showJobsHome();

    }
    catch (error) {

        console.error(
            "Authentication check failed:",
            error
        );

        showJobsHome();
    }
}


/* =========================================================
   GOOGLE LOGIN
========================================================= */

function loginWithGoogle() {

    window.location.href =
        `${API_BASE_URL}/auth/login`;
}


/* =========================================================
   LOGOUT
========================================================= */

async function logout() {

    try {

        await fetch(
            `${API_BASE_URL}/auth/logout`,
            {
                method: "GET",
                credentials: "include"
            }
        );

    }
    catch (error) {

        console.error(
            "Logout error:",
            error
        );
    }


    currentUser = null;
    uploadedResumePath = null;
    latestAnalysisData = null;

    updateJobsAuthUI(null);
    showJobsHome();
}


/* =========================================================
   LOGIN UI
========================================================= */

function showLogin() {

    if (typeof hideJobsHome === "function") {
        hideJobsHome();
    }

    const loginSection =
        document.getElementById(
            "login-section"
        );

    const dashboardSection =
        document.getElementById(
            "dashboard-section"
        );


    if (loginSection) {
        loginSection.style.display =
            "flex";
    }


    if (dashboardSection) {
        dashboardSection.style.display =
            "none";
    }
}


/* =========================================================
   DASHBOARD UI
========================================================= */

function showDashboard(user) {

    if (typeof hideJobsHome === "function") {
        hideJobsHome();
    }

    const loginSection =
        document.getElementById(
            "login-section"
        );

    const dashboardSection =
        document.getElementById(
            "dashboard-section"
        );


    if (loginSection) {
        loginSection.style.display =
            "none";
    }


    if (dashboardSection) {
        dashboardSection.style.display =
            "block";
    }


    updateUserUI(user);
}


function updateUserUI(user) {

    if (!user) {
        return;
    }


    const userName =
        document.getElementById(
            "user-name"
        );

    const userEmail =
        document.getElementById(
            "user-email"
        );

    const userPicture =
        document.getElementById(
            "user-picture"
        );


    if (userName) {

        userName.textContent =
            user.name ||
            user.full_name ||
            "User";
    }


    if (userEmail) {

        userEmail.textContent =
            user.email ||
            "";
    }


    if (
        userPicture &&
        user.picture
    ) {

        userPicture.src =
            user.picture;

        userPicture.style.display =
            "block";
    }
}


/* =========================================================
   FILE SELECTION
========================================================= */

function handleFileSelection(event) {

    const file =
        event.target.files[0];

    const fileNameElement =
        document.getElementById(
            "selected-file-name"
        );


    if (!file) {

        if (fileNameElement) {
            fileNameElement.textContent =
                "No file selected.";
        }

        return;
    }


    const extension =
        file.name
            .split(".")
            .pop()
            .toLowerCase();


    if (
        extension !== "pdf" &&
        extension !== "docx"
    ) {

        alert(
            "Please select a PDF or DOCX resume."
        );

        event.target.value = "";

        if (fileNameElement) {
            fileNameElement.textContent =
                "No file selected.";
        }

        return;
    }


    if (fileNameElement) {

        fileNameElement.textContent =
            `Selected file: ${file.name}`;
    }


}


/* =========================================================
   RESUME ANALYSIS
========================================================= */

async function analyzeResume() {

    if (analysisInProgress) {


        return;
    }


    const fileInput =
        document.getElementById(
            "resume-file"
        );

    const analyzeButton =
        document.getElementById(
            "analyze-button"
        );

    const companyElement =
        document.getElementById(
            "company"
        );

    const roleElement =
        document.getElementById(
            "role"
        );

    const jobDescriptionElement =
        document.getElementById(
            "job-description"
        );


    if (
        !fileInput ||
        !fileInput.files ||
        fileInput.files.length === 0
    ) {

        alert(
            "Please select your resume first."
        );

        return;
    }


    const file =
        fileInput.files[0];


    const company =
        companyElement
            ? companyElement.value.trim()
            : "";


    const role =
        roleElement
            ? roleElement.value.trim()
            : "";


    const jobDescription =
        jobDescriptionElement
            ? jobDescriptionElement.value.trim()
            : "";


    analysisInProgress = true;


    if (analyzeButton) {

        analyzeButton.disabled =
            true;

        analyzeButton.dataset.originalText =
            analyzeButton.textContent;

        analyzeButton.textContent =
            "Analyzing...";
    }


    try {

        /* =====================================================
           STEP 1 — UPLOAD RESUME
        ===================================================== */

        showLoading(
            "Uploading and reading your resume..."
        );


        const formData =
            new FormData();


        formData.append(
            "file",
            file
        );


        let uploadResponse = null;
        let uploadData = null;


        const maxAttempts = 2;


        for (
            let attempt = 1;
            attempt <= maxAttempts;
            attempt++
        ) {



            uploadResponse =
                await fetch(
                    `${API_BASE_URL}/resume/upload`,
                    {
                        method: "POST",
                        credentials: "include",
                        body: formData
                    }
                );


            if (uploadResponse.ok) {

                uploadData =
                    await readJsonResponse(
                        uploadResponse
                    );

                break;
            }


            if (
                (
                    uploadResponse.status === 502 ||
                    uploadResponse.status === 503 ||
                    uploadResponse.status === 504
                ) &&
                attempt < maxAttempts
            ) {

                console.warn(
                    "Temporary backend/AI provider error. Retrying..."
                );


                showLoading(
                    "AI provider is busy. Retrying..."
                );


                await sleep(1500);

                continue;
            }


            const errorData =
                await readJsonResponse(
                    uploadResponse
                );


            throw new Error(
                errorData.detail ||
                `Resume upload failed (${uploadResponse.status}).`
            );
        }


        if (
            !uploadData ||
            !uploadData.resume_path
        ) {

            throw new Error(
                "Backend did not return a valid resume_path."
            );
        }


        uploadedResumePath =
            uploadData.resume_path;




        /* =====================================================
           STEP 2 — ANALYSIS
        ===================================================== */

        showLoading(
            "Finding your best-matching roles and jobs..."
        );

        const runId = ++analysisRunId;

        // Slow AI tips are requested at the same time, but shown later,
        // so the main results are not held up by them.
        const aiRequest = fetch(
            `${API_BASE_URL}/analysis/ai`,
            {
                method: "POST",
                credentials: "include",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ resume_path: uploadedResumePath })
            }
        )
            .then(response => response.ok ? response.json() : null)
            .catch(() => null);

        const analysisResponse =
            await fetch(
                `${API_BASE_URL}/analysis/`,
                {
                    method: "POST",
                    credentials: "include",
                    headers: {
                        "Content-Type":
                            "application/json"
                    },
                    body: JSON.stringify({
                        resume_path:
                            uploadedResumePath,

                        company:
                            company || null,

                        role:
                            role || null,

                        job_description:
                            jobDescription || null,

                        include_ai:
                            false
                    })
                }
            );


        const analysisData =
            await readJsonResponse(
                analysisResponse
            );


        if (!analysisResponse.ok) {

            throw new Error(
                analysisData.detail ||
                `Analysis failed (${analysisResponse.status}).`
            );
        }


        latestAnalysisData =
            analysisData?.analysis ||
            analysisData?.result ||
            analysisData?.data ||
            analysisData;


        window.latestAnalysisData =
            latestAnalysisData;


        displayAnalysis(
            analysisData
        );


        hideLoading();


        aiRequest.then(extras => {

            if (runId !== analysisRunId || !latestAnalysisData) {
                return;                      // a newer analysis started
            }

            if (extras && extras.resume_improvement) {

                latestAnalysisData.ai_review = extras.ai_review;
                latestAnalysisData.resume_improvement = extras.resume_improvement;

            } else {

                latestAnalysisData.resume_improvement = {
                    improvements: [
                        "Use clear section headings (Experience, Projects, Skills, Education).",
                        "Add measurable results to every role, for example numbers, percentages or time saved.",
                        "List technical skills exactly as they appear in job descriptions.",
                        "Keep the resume to one or two pages in a simple, single-column layout."
                    ]
                };
            }

            displayAIImprovements(latestAnalysisData);
        });


        const status =
            document.getElementById(
                "resume-status"
            );


        if (status) {

            status.textContent =
                "Analysis completed successfully.";

            status.style.color =
                "green";
        }


    }
    catch (error) {

        console.error(
            "Resume analysis error:",
            error
        );


        hideLoading();


        const status =
            document.getElementById(
                "resume-status"
            );


        if (status) {

            status.textContent =
                "Analysis failed. Please try again.";

            status.style.color =
                "red";
        }


        showBackendError(
            error.message ||
            "Something went wrong."
        );
    }
    finally {

        analysisInProgress =
            false;


        if (analyzeButton) {

            analyzeButton.disabled =
                false;

            analyzeButton.textContent =
                analyzeButton.dataset.originalText ||
                "Analyze Resume";
        }
    }
}


/* =========================================================
   DISPLAY ANALYSIS
========================================================= */

function displayAnalysis(data) {

    const printButton = document.getElementById("print-report-button");

    if (printButton) {
        printButton.hidden = false;
    }

    const root =
        data?.analysis ||
        data?.result ||
        data?.data ||
        data ||
        {};


    latestAnalysisData =
        root;


    window.latestAnalysisData =
        root;




    displayCareerOpportunities(
        normalizeArray(
            root.career_opportunities
        )
    );


    displayJobPostings(
        normalizeArray(
            root.job_postings
        )
    );


    displayTargetJob(
        root.job,
        root.match_result
    );


    displayResumeSummary(
        root
    );


    displayATSScore(
        root
    );


    displayAIImprovements(
        root
    );


    displaySkillGap(
        root.skill_gap
    );


    const resultsSection =
        document.getElementById(
            "results-section"
        );


    if (resultsSection) {

        resultsSection.style.display =
            "block";


        window.scrollTo({
            top:
                resultsSection.offsetTop,
            behavior:
                "smooth"
        });
    }
}


/* =========================================================
   CAREER OPPORTUNITIES
========================================================= */

function skillChips(list, kind, max) {

    const items = normalizeArray(list)
        .map(item => String(item || "").trim())
        .filter(Boolean);

    if (!items.length) {
        return "";
    }

    const shown = items.slice(0, max || 8);
    const extra = items.length - shown.length;

    return shown
        .map(skill => `<span class="skill-tag ${kind}">${escapeHtml(skill)}</span>`)
        .join("")
        + (extra > 0 ? `<span class="skill-tag more">+${extra} more</span>` : "");
}


function matchMeter(score) {

    const value = Math.max(0, Math.min(100, Math.round(Number(score) || 0)));

    const tone = value >= 70 ? "high" : value >= 45 ? "mid" : "low";

    return `
        <div class="match-meter ${tone}" role="img" aria-label="${value}% match">
            <span class="match-value">${value}%</span>
            <span class="match-bar"><i style="width:${value}%"></i></span>
            <span class="match-caption">match</span>
        </div>
    `;
}


function reasonList(reasons) {

    const items = (Array.isArray(reasons) ? reasons : [reasons])
        .map(item => String(item || "").trim())
        .filter(Boolean);

    if (!items.length) {
        return "";
    }

    return `<ul class="reason-list">${
        items.map(text => `<li>${escapeHtml(text)}</li>`).join("")
    }</ul>`;
}


function displayCareerOpportunities(
    opportunities
) {

    const container = document.getElementById("career-opportunities");

    if (!container) {
        return;
    }

    opportunities = normalizeArray(opportunities)
        .filter(item => item && typeof item === "object");

    if (opportunities.length === 0) {

        container.innerHTML = emptyMessage(
            "We could not find matching roles yet. Add more skills to your resume and try again."
        );

        return;
    }

    container.innerHTML = `<div class="cp-grid">${
        opportunities.map(opportunity => {

            const role = opportunity.role || opportunity.title || "Career Role";

            const readiness = opportunity.readiness || "";

            const readyClass = /strong/i.test(readiness) ? "ready-strong"
                : /good/i.test(readiness) ? "ready-good"
                : /possible/i.test(readiness) ? "ready-possible"
                : "ready-develop";

            const matched = skillChips(opportunity.matched_skills || opportunity.matched, "matched", 6);

            const missing = skillChips(opportunity.missing_skills || opportunity.missing, "missing", 5);

            return `
                <article class="cp-card">
                    <header class="cp-head">
                        <div class="cp-title">
                            ${opportunity.level
                                ? `<span class="level-pill">${escapeHtml(opportunity.level)}</span>`
                                : ""}
                            <h3>${escapeHtml(role)}</h3>
                            ${readiness
                                ? `<span class="ready-pill ${readyClass}">${escapeHtml(readiness)}</span>`
                                : ""}
                        </div>
                        ${matchMeter(opportunity.match_score ?? opportunity.score ?? 0)}
                    </header>

                    ${reasonList(opportunity.why)}

                    ${matched ? `<div class="cp-skills"><strong>You have</strong><div class="skill-tags">${matched}</div></div>` : ""}

                    ${missing ? `<div class="cp-skills"><strong>To learn</strong><div class="skill-tags">${missing}</div></div>` : ""}
                </article>
            `;
        }).join("")
    }</div>`;
}


/* =========================================================
   JOB POSTINGS
========================================================= */

function displayJobPostings(
    jobs
) {

    const container = document.getElementById("job-postings");

    if (!container) {
        return;
    }

    jobs = normalizeArray(jobs).filter(item => item && typeof item === "object");

    if (jobs.length === 0) {

        container.innerHTML = emptyMessage(
            "No live openings matched your profile right now. Try the Find Jobs page to search by title or city."
        );

        return;
    }

    container.innerHTML = `<div class="cp-grid">${
        jobs.map(job => {

            const link = job.url || job.job_url || job.link || "";

            const safeLink = /^https?:\/\//i.test(link) ? link : "";

            const salary = job.salary
                || ((job.salary_min || job.salary_max)
                    ? "₹" + Math.round((job.salary_max || job.salary_min) / 100000 * 10) / 10 + " LPA"
                    : "");

            const matched = skillChips(job.matched_skills, "matched", 6);

            const missing = skillChips(job.missing_skills, "missing", 5);

            const reasons = job.level_fit
                ? [job.level_fit]
                : (Array.isArray(job.why_suitable) ? job.why_suitable.filter(r => !/^(matching|skills to develop)/i.test(r)) : []);

            return `
                <article class="cp-card job">
                    <header class="cp-head">
                        <div class="cp-title">
                            <span class="company-name">${escapeHtml(job.company || "Company")}</span>
                            <h3>${escapeHtml(job.title || job.role || "Job Opportunity")}</h3>
                            <p class="location">📍 ${escapeHtml(job.location || "Location not specified")}${
                                salary ? ` · <span class="salary">${escapeHtml(salary)}</span>` : ""}</p>
                        </div>
                        ${matchMeter(job.match_score ?? job.score ?? 0)}
                    </header>

                    ${reasonList(reasons)}

                    ${matched ? `<div class="cp-skills"><strong>You have</strong><div class="skill-tags">${matched}</div></div>` : ""}

                    ${missing ? `<div class="cp-skills"><strong>To learn</strong><div class="skill-tags">${missing}</div></div>` : ""}

                    ${safeLink
                        ? `<a class="job-link" href="${escapeAttribute(safeLink)}" target="_blank" rel="noopener noreferrer">View job →</a>`
                        : ""}
                </article>
            `;
        }).join("")
    }</div>`;
}


/* =========================================================
   TARGET JOB
========================================================= */

function displayTargetJob(
    job,
    matchResult
) {

    const container =
        document.getElementById(
            "target-job-analysis"
        );


    if (!container) {
        return;
    }


    if (
        !job &&
        !matchResult
    ) {

        container.innerHTML =
            emptyMessage(
                ""
            );

        return;
    }


    const result =
        matchResult || {};


    const overall =
        result.overall_score ??
        result.overall ??
        result.score ??
        0;


    const skill =
        result.skill_score ??
        result.skill ??
        0;


    const keyword =
        result.keyword_score ??
        result.keyword ??
        0;


    const experience =
        result.experience_score ??
        (
            typeof result.experience === "number"
                ? result.experience
                : 0
        );


    const education =
        result.education_score ??
        result.education ??
        0;


    const matchedSkills =
        normalizeArray(
            result.matched_skills ||
            result.matched
        );


    const missingSkills =
        normalizeArray(
            result.missing_skills ||
            result.missing
        );


    const companyElement =
        document.getElementById(
            "company"
        );


    const roleElement =
        document.getElementById(
            "role"
        );


    const companyName =
        job?.company ||
        companyElement?.value ||
        "Target Company";


    const roleName =
        job?.title ||
        job?.role ||
        roleElement?.value ||
        "Target Job";


    container.innerHTML = `

        <div class="target-job-card">

            <div class="target-header">

                <div>

                    <span class="company-name">
                        ${escapeHtml(companyName)}
                    </span>

                    <h3>
                        ${escapeHtml(roleName)}
                    </h3>

                </div>


                <div class="large-score">

                    ${escapeHtml(overall)}%

                    <small>
                        Match
                    </small>

                </div>

            </div>


            <div class="result-grid">

                ${scoreBox(
                    "Skills",
                    skill
                )}

                ${scoreBox(
                    "Keywords",
                    keyword
                )}

                ${scoreBox(
                    "Experience",
                    experience
                )}

                ${scoreBox(
                    "Education",
                    education
                )}

            </div>


            ${renderSkillGroup(
                "Matched Skills",
                matchedSkills,
                "matched"
            )}


            ${renderSkillGroup(
                "Missing Skills",
                missingSkills,
                "missing"
            )}

        </div>
    `;
}


/* =========================================================
   RESUME SUMMARY
========================================================= */

function displayResumeSummary(
    data
) {

    const container =
        document.getElementById(
            "resume-analysis-summary"
        );


    if (!container) {
        return;
    }


    const resume =
        data.resume ||
        data.resume_data ||
        data.parsed_resume ||
        {};


    const name =
        resume.name ||
        "Resume";


    const email =
        resume.email ||
        "";


    const phone =
        resume.phone ||
        "";


    const summary =
        resume.summary ||
        data.summary ||
        "No professional summary available.";


    /*
     * IMPORTANT FIX
     *
     * Backend may return:
     *
     * experience: "Business Data Analyst at ..."
     *
     * OR:
     *
     * experience: [...]
     *
     * Therefore NEVER directly call:
     *
     * experience.map(...)
     *
     * without normalization.
     */

    const experience =
        normalizeExperience(
            resume.experience ||
            data.experience
        );


    const education =
        normalizeArray(
            resume.education ||
            data.education
        );


    const skills =
        normalizeArray(
            resume.skills ||
            data.skills
        );


    const projects =
        normalizeArray(
            resume.projects ||
            data.projects
        );


    container.innerHTML = `

        <div class="summary-card">

            <div class="summary-header">

                <div>

                    <h3>
                        ${escapeHtml(name)}
                    </h3>

                    ${
                        email
                            ? `
                                <p>
                                    ✉ ${escapeHtml(email)}
                                </p>
                              `
                            : ""
                    }

                    ${
                        phone
                            ? `
                                <p>
                                    ☎ ${escapeHtml(phone)}
                                </p>
                              `
                            : ""
                    }

                </div>

            </div>


            <div class="summary-block">

                <h4>
                    Professional Summary
                </h4>

                <p>
                    ${escapeHtml(summary)}
                </p>

            </div>


            ${
                skills.length
                    ? `
                        <div class="summary-block">

                            <h4>
                                Technical Skills
                            </h4>

                            <div class="skill-tags">

                                ${skills
                                    .map(
                                        skill =>
                                            `
                                            <span class="skill-tag additional">
                                                ${escapeHtml(skill)}
                                            </span>
                                            `
                                    )
                                    .join("")}

                            </div>

                        </div>
                      `
                    : ""
            }


            ${
                experience.length
                    ? `
                        <div class="summary-block">

                            <h4>
                                Professional Experience
                            </h4>

                            <div class="experience-list">

                                ${experience
                                    .map(
                                        item =>
                                            `
                                            <div class="experience-item">

                                                ${
                                                    item.title
                                                        ? `
                                                            <h4>
                                                                ${escapeHtml(item.title)}
                                                            </h4>
                                                          `
                                                        : ""
                                                }

                                                ${
                                                    item.company
                                                        ? `
                                                            <strong>
                                                                ${escapeHtml(item.company)}
                                                            </strong>
                                                          `
                                                        : ""
                                                }

                                                ${
                                                    item.dates
                                                        ? `
                                                            <span>
                                                                ${escapeHtml(item.dates)}
                                                            </span>
                                                          `
                                                        : ""
                                                }

                                                <p>
                                                    ${escapeHtml(
                                                        item.description ||
                                                        item.text ||
                                                        ""
                                                    )}
                                                </p>

                                            </div>
                                            `
                                    )
                                    .join("")}

                            </div>

                        </div>
                      `
                    : ""
            }


            ${
                education.length
                    ? `
                        <div class="summary-block">

                            <h4>
                                Education
                            </h4>

                            <div class="education-list">

                                ${education
                                    .map(
                                        item => {

                                            if (
                                                typeof item ===
                                                "string"
                                            ) {
                                                return `
                                                    <p>
                                                        ${escapeHtml(item)}
                                                    </p>
                                                `;
                                            }


                                            return `
                                                <div class="education-item">

                                                    <h4>
                                                        ${escapeHtml(
                                                            item.degree ||
                                                            item.qualification ||
                                                            "Education"
                                                        )}
                                                    </h4>

                                                    ${
                                                        item.field
                                                            ? `
                                                                <p>
                                                                    ${escapeHtml(item.field)}
                                                                </p>
                                                              `
                                                            : ""
                                                    }

                                                    ${
                                                        item.institution
                                                            ? `
                                                                <strong>
                                                                    ${escapeHtml(item.institution)}
                                                                </strong>
                                                              `
                                                            : ""
                                                    }

                                                    ${
                                                        item.dates
                                                            ? `
                                                                <span>
                                                                    ${escapeHtml(item.dates)}
                                                                </span>
                                                              `
                                                            : ""
                                                    }

                                                </div>
                                            `;
                                        }
                                    )
                                    .join("")}

                            </div>

                        </div>
                      `
                    : ""
            }


            ${
                projects.length
                    ? `
                        <div class="summary-block">

                            <h4>
                                Projects
                            </h4>

                            <ul>

                                ${projects
                                    .map(
                                        project =>
                                            `
                                            <li>
                                                ${escapeHtml(
                                                    typeof project === "string"
                                                        ? project
                                                        : JSON.stringify(project)
                                                )}
                                            </li>
                                            `
                                    )
                                    .join("")}

                            </ul>

                        </div>
                      `
                    : ""
            }

        </div>
    `;
}


/* =========================================================
   ATS SCORE
========================================================= */

function displayATSScore(
    data
) {

    const container =
        document.getElementById(
            "ats-score"
        );


    if (!container) {
        return;
    }


    const report =
        data.ats_report ||
        data.ats ||
        data.ats_result ||
        {};


    const score =
        Number(
            report.score ??
            data.ats_score ??
            0
        );


    const grade =
        report.grade ||
        calculateATSGrade(
            score
        );


    const strengths =
        normalizeArray(
            report.strengths
        );


    const weaknesses =
        normalizeArray(
            report.weaknesses
        );


    const improvements =
        normalizeArray(
            report.improvements
        );


    const breakdown =
        report.score_breakdown ||
        {};


    container.innerHTML = `

        <div class="ats-card">

            <div class="ats-main">

                <div class="ats-score-circle">

                    <span>
                        ${score.toFixed(1)}
                    </span>

                    <small>
                        / 100
                    </small>

                </div>


                <div>

                    <h3>
                        ATS Compatibility
                    </h3>

                    <div class="ats-grade">
                        Grade:
                        ${escapeHtml(grade)}
                    </div>

                    <p>
                        ${escapeHtml(
                            getATSMessage(score)
                        )}
                    </p>

                </div>

            </div>


            ${
                Object.keys(breakdown).length
                    ? `
                        <div class="ats-breakdown">

                            <h3>
                                Score Breakdown
                            </h3>

                            <div class="result-grid">

                                ${Object.entries(
                                    breakdown
                                )
                                .map(
                                    ([key, value]) =>
                                        scoreBox(
                                            formatLabel(key),
                                            value
                                        )
                                )
                                .join("")}

                            </div>

                        </div>
                      `
                    : ""
            }


            ${
                strengths.length
                    ? `
                        <div class="ats-suggestions">

                            <h3>
                                ✅ Strengths
                            </h3>

                            <ul>

                                ${strengths
                                    .map(
                                        item =>
                                            `
                                            <li>
                                                ${escapeHtml(item)}
                                            </li>
                                            `
                                    )
                                    .join("")}

                            </ul>

                        </div>
                      `
                    : ""
            }


            ${
                weaknesses.length
                    ? `
                        <div class="ats-suggestions">

                            <h3>
                                ⚠️ Problems Detected
                            </h3>

                            <ul>

                                ${weaknesses
                                    .map(
                                        item =>
                                            `
                                            <li>
                                                ${escapeHtml(item)}
                                            </li>
                                            `
                                    )
                                    .join("")}

                            </ul>

                        </div>
                      `
                    : ""
            }


            <div class="ats-suggestions">

                <h3>
                    ✦ ATS Improvement Suggestions
                </h3>

                ${
                    improvements.length
                        ? `
                            <ol>

                                ${improvements
                                    .map(
                                        item =>
                                            `
                                            <li>
                                                ${escapeHtml(item)}
                                            </li>
                                            `
                                    )
                                    .join("")}

                            </ol>
                          `
                        : `
                            <ul>

                                <li>
                                    Add job-specific keywords naturally.
                                </li>

                                <li>
                                    Use clear standard section headings.
                                </li>

                                <li>
                                    Quantify achievements using measurable results.
                                </li>

                                <li>
                                    Avoid unnecessary graphics and complex formatting.
                                </li>

                            </ul>
                          `
                }

            </div>

        </div>
    `;
}


/* =========================================================
   ATS HELPERS
========================================================= */

function calculateATSGrade(
    score
) {

    if (score >= 90) {
        return "A+";
    }

    if (score >= 80) {
        return "A";
    }

    if (score >= 70) {
        return "B";
    }

    if (score >= 60) {
        return "C";
    }

    if (score >= 50) {
        return "D";
    }

    return "F";
}


function getATSMessage(
    score
) {

    if (score >= 90) {
        return "Excellent ATS compatibility.";
    }

    if (score >= 80) {
        return "Very strong ATS compatibility.";
    }

    if (score >= 70) {
        return "Good ATS compatibility, but there is room for improvement.";
    }

    if (score >= 60) {
        return "Moderate ATS compatibility. Improve keywords and resume structure.";
    }

    return "Low ATS compatibility. Significant resume improvements are recommended.";
}


/* =========================================================
   AI IMPROVEMENTS
========================================================= */

function displayAIImprovements(
    data
) {

    const container =
        document.getElementById(
            "ai-improvements"
        );

    if (!container) {
        return;
    }


    /*
     * --------------------------------------------------------
     * NORMALIZE IMPROVEMENT DATA
     * --------------------------------------------------------
     */

    if (data?.resume_improvement?.pending) {

        container.innerHTML = `
            <div class="ai-pending" role="status">
                <span class="spinner" aria-hidden="true"></span>
                <div>
                    <strong>Writing personalised tips for your resume...</strong>
                    <p>Your results above are ready. These tips take a little longer and will appear here by themselves.</p>
                </div>
            </div>`;

        return;
    }

    const source =
        data?.resume_improvement ||
        data?.ai_improvements ||
        data?.improvements ||
        data?.improvement ||
        data ||
        {};


    let improvements = [];


    /*
     * --------------------------------------------------------
     * STANDARD AI IMPROVEMENT ARRAYS
     * --------------------------------------------------------
     */

    if (Array.isArray(source)) {

        improvements =
            source;

    }


    else if (
        source &&
        typeof source === "object"
    ) {

        improvements =
            normalizeArray(
                source.improvements ||
                source.suggestions ||
                source.recommendations ||
                source.feedback
            );


        /*
         * ----------------------------------------------------
         * IMPROVEMENT RESULT FALLBACK STRUCTURE
         *
         * Backend returns:
         *
         * improved_summary
         * improved_skills
         * improved_projects
         * keywords_to_add
         * ats_tips
         * ----------------------------------------------------
         */

        if (improvements.length === 0) {

            if (
                source.improved_summary
            ) {

                improvements.push({
                    category:
                        "Professional Summary",
                    text:
                        source.improved_summary
                });

            }


            if (
                source.improved_skills
            ) {

                const skills =
                    Array.isArray(
                        source.improved_skills
                    )
                        ? source.improved_skills.join(
                            ", "
                        )
                        : String(
                            source.improved_skills
                        );

                if (skills.trim()) {

                    improvements.push({
                        category:
                            "Skills",
                        text:
                            "Review and prioritize these skills for the target role: " +
                            skills
                    });

                }

            }


            if (
                source.improved_projects
            ) {

                let projectsText = "";

                if (
                    Array.isArray(
                        source.improved_projects
                    )
                ) {

                    projectsText =
                        source.improved_projects
                            .map(
                                project => {

                                    if (
                                        typeof project ===
                                        "string"
                                    ) {
                                        return project;
                                    }

                                    if (
                                        project &&
                                        typeof project ===
                                        "object"
                                    ) {
                                        return (
                                            project.title ||
                                            project.name ||
                                            project.description ||
                                            JSON.stringify(
                                                project
                                            )
                                        );
                                    }

                                    return String(
                                        project
                                    );
                                }
                            )
                            .join(
                                " | "
                            );

                }
                else {

                    projectsText =
                        String(
                            source.improved_projects
                        );

                }


                if (
                    projectsText.trim()
                ) {

                    improvements.push({
                        category:
                            "Projects",
                        text:
                            "Strengthen your project descriptions by clearly showing the technology used, your contribution, and measurable results."
                    });

                }

            }


            /*
             * ------------------------------------------------
             * KEYWORDS TO ADD
             * ------------------------------------------------
             */

            const keywords =
                normalizeArray(
                    source.keywords_to_add
                );


            keywords.forEach(
                keyword => {

                    if (
                        keyword === null ||
                        keyword === undefined
                    ) {
                        return;
                    }

                    const value =
                        typeof keyword === "string"
                            ? keyword
                            : (
                                keyword.keyword ||
                                keyword.name ||
                                keyword.text ||
                                keyword.suggestion ||
                                JSON.stringify(
                                    keyword
                                )
                            );

                    if (
                        value &&
                        String(value).trim()
                    ) {

                        improvements.push({
                            category:
                                "ATS Keywords",
                            text:
                                String(value)
                        });

                    }

                }
            );


            /*
             * ------------------------------------------------
             * ATS TIPS
             * ------------------------------------------------
             */

            const atsTips =
                normalizeArray(
                    source.ats_tips
                );


            atsTips.forEach(
                tip => {

                    if (
                        tip === null ||
                        tip === undefined
                    ) {
                        return;
                    }

                    const value =
                        typeof tip === "string"
                            ? tip
                            : (
                                tip.text ||
                                tip.suggestion ||
                                tip.description ||
                                JSON.stringify(
                                    tip
                                )
                            );

                    if (
                        value &&
                        String(value).trim()
                    ) {

                        improvements.push({
                            category:
                                "ATS Optimization",
                            text:
                                String(value)
                        });

                    }

                }
            );

        }

    }


    /*
     * --------------------------------------------------------
     * REMOVE DUPLICATES
     * --------------------------------------------------------
     */

    const uniqueImprovements = [];

    const seen =
        new Set();


    improvements.forEach(
        item => {

            let text = "";
            let category = "Improvement";


            if (
                typeof item === "string"
            ) {

                text =
                    item;

            }

            else if (
                item &&
                typeof item === "object"
            ) {

                category =
                    item.category ||
                    item.type ||
                    item.title ||
                    "Improvement";

                text =
                    item.text ||
                    item.suggestion ||
                    item.description ||
                    item.feedback ||
                    item.message ||
                    item.value ||
                    "";

            }


            if (
                text === null ||
                text === undefined
            ) {
                return;
            }


            text =
                String(
                    text
                ).trim();


            if (!text) {
                return;
            }


            const key =
                `${category}|${text}`.toLowerCase();


            if (
                seen.has(key)
            ) {
                return;
            }


            seen.add(key);


            uniqueImprovements.push({
                category:
                    String(
                        category
                    ),
                text:
                    text
            });

        }
    );


    /*
     * --------------------------------------------------------
     * EMPTY STATE
     * --------------------------------------------------------
     */

    if (
        uniqueImprovements.length === 0
    ) {

        container.innerHTML =
            emptyMessage(
                "No AI improvement suggestions available."
            );

        return;
    }


    /*
     * --------------------------------------------------------
     * RENDER
     * --------------------------------------------------------
     */

    container.innerHTML = `

        <div class="improvement-card">

            <div class="improvement-header">

                <h3>
                    Resume Improvement Suggestions
                </h3>

                <p>
                    Practical recommendations to improve your resume, ATS compatibility, and job relevance.
                </p>

            </div>


            <ul class="improvement-list">

                ${uniqueImprovements
                    .map(
                        item =>
                            `
                            <li class="improvement-item">

                                <strong>
                                    ${escapeHtml(
                                        item.category
                                    )}
                                </strong>

                                <span>
                                    ${escapeHtml(
                                        item.text
                                    )}
                                </span>

                            </li>
                            `
                    )
                    .join("")}

            </ul>

        </div>

    `;
}


function displaySkillGap(
    skillGap
) {

    const container =
        document.getElementById(
            "skill-gap-analysis"
        );


    if (!container) {
        return;
    }


    if (
        !skillGap ||
        typeof skillGap !== "object"
    ) {

        container.innerHTML =
            emptyMessage(
                "Skill gap analysis is not available."
            );

        return;
    }


    const score =
        Number(
            skillGap.score ??
            skillGap.skill_score ??
            0
        );


    const targetRole =
        skillGap.target_role ||
        document.getElementById(
            "role"
        )?.value ||
        "Target Role";


    const matched =
        normalizeArray(
            skillGap.matched ||
            skillGap.matched_skills
        );


    const partial =
        normalizeArray(
            skillGap.partial ||
            skillGap.partial_skills
        );


    const missing =
        normalizeArray(
            skillGap.missing ||
            skillGap.missing_skills
        );


    const additional =
        normalizeArray(
            skillGap.additional ||
            skillGap.additional_skills
        );


    const priorityGaps =
        normalizeArray(
            skillGap.priority_gaps
        );


    const actions =
        normalizeArray(
            skillGap.recommended_actions
        );


    container.innerHTML = `

        <div class="skill-gap-card">

            <div class="skill-gap-header">

                <div>

                    <h3>
                        ◎ ${escapeHtml(targetRole)}
                    </h3>

                    <p>
                        Resume skill compatibility with this target role.
                    </p>

                </div>


                <div class="skill-score">

                    ${escapeHtml(score)}%

                </div>

            </div>


            ${renderSkillGroup(
                "Matched Skills",
                matched,
                "matched"
            )}


            ${renderSkillGroup(
                "Partial Skills",
                partial,
                "partial"
            )}


            ${renderSkillGroup(
                "Missing Skills",
                missing,
                "missing"
            )}


            ${renderSkillGroup(
                "Additional Skills",
                additional,
                "additional"
            )}


            ${
                priorityGaps.length
                    ? `
                        <div class="priority-section">

                            <h3>
                                ⚠ Priority Skill Gaps
                            </h3>

                            ${priorityGaps
                                .map(
                                    gap => {

                                        if (
                                            typeof gap ===
                                            "string"
                                        ) {
                                            return `
                                                <div class="priority-gap">

                                                    ${escapeHtml(gap)}

                                                </div>
                                            `;
                                        }


                                        return `
                                            <div class="priority-gap">

                                                <span class="priority-badge">
                                                    ${escapeHtml(
                                                        gap.priority ||
                                                        "medium"
                                                    )}
                                                </span>

                                                <div>

                                                    <strong>
                                                        ${escapeHtml(
                                                            gap.skill ||
                                                            "Skill"
                                                        )}
                                                    </strong>

                                                    ${
                                                        gap.reason
                                                            ? `
                                                                <p>
                                                                    ${escapeHtml(
                                                                        gap.reason
                                                                    )}
                                                                </p>
                                                              `
                                                            : ""
                                                    }

                                                </div>

                                            </div>
                                        `;
                                    }
                                )
                                .join("")}

                        </div>
                      `
                    : ""
            }


            ${
                actions.length
                    ? `
                        <div class="recommended-actions">

                            <h3>
                                ▤ Recommended Actions
                            </h3>

                            <ol>

                                ${actions
                                    .map(
                                        action =>
                                            `
                                            <li>
                                                ${escapeHtml(action)}
                                            </li>
                                            `
                                    )
                                    .join("")}

                            </ol>

                        </div>
                      `
                    : ""
            }

        </div>
    `;
}


/* =========================================================
   APPLICATION TRACKER SETUP
========================================================= */

function initializeExtendedFeatures() {

    const addApplicationButton =
        document.getElementById(
            "add-application-button"
        );


    const refreshApplicationsButton =
        document.getElementById(
            "refresh-applications-button"
        );


    if (addApplicationButton) {

        addApplicationButton.addEventListener(
            "click",
            addApplication
        );
    }


    if (refreshApplicationsButton) {

        refreshApplicationsButton.addEventListener(
            "click",
            loadApplications
        );
    }


    loadApplications();
}


/* =========================================================
   APPLICATION TRACKER
========================================================= */

async function addApplication() {

    const company =
        document.getElementById(
            "application-company"
        )?.value.trim() ||
        "";


    const role =
        document.getElementById(
            "application-role"
        )?.value.trim() ||
        "";


    const jobUrl =
        document.getElementById(
            "application-url"
        )?.value.trim() ||
        "";


    const status =
        document.getElementById(
            "application-status"
        )?.value ||
        "Applied";


    const appliedDate =
        document.getElementById(
            "application-date"
        )?.value ||
        "";


    const notes =
        document.getElementById(
            "application-notes"
        )?.value.trim() ||
        "";


    if (
        !company ||
        !role
    ) {

        alert(
            "Company and role are required."
        );

        return;
    }


    try {

        const response =
            await fetch(
                `${API_BASE_URL}/applications/`,
                {
                    method: "POST",
                    credentials: "include",
                    headers: {
                        "Content-Type":
                            "application/json"
                    },
                    body: JSON.stringify({

                        company:
                            company,

                        role:
                            role,

                        job_url:
                            jobUrl ||
                            null,

                        status:
                            status,

                        applied_date:
                            appliedDate ||
                            null,

                        notes:
                            notes ||
                            null
                    })
                }
            );


        const data =
            await readJsonResponse(
                response
            );


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Could not add application."
            );
        }


        document.getElementById(
            "application-company"
        ).value = "";


        document.getElementById(
            "application-role"
        ).value = "";


        document.getElementById(
            "application-url"
        ).value = "";


        document.getElementById(
            "application-status"
        ).value =
            "Applied";


        document.getElementById(
            "application-date"
        ).value = "";


        document.getElementById(
            "application-notes"
        ).value = "";


        await loadApplications();

    }
    catch (error) {

        console.error(
            "Add application failed:",
            error
        );


        showBackendError(
            error.message
        );
    }
}


/* =========================================================
   LOAD APPLICATIONS
========================================================= */

async function loadApplications() {

    const container =
        document.getElementById(
            "applications-list"
        );


    const loading =
        document.getElementById(
            "application-tracker-loading"
        );


    if (!container) {
        return;
    }


    try {

        if (loading) {

            loading.style.display =
                "flex";
        }


        const response =
            await fetch(
                `${API_BASE_URL}/applications/`,
                {
                    method: "GET",
                    credentials: "include"
                }
            );


        const data =
            await readJsonResponse(
                response
            );


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Could not load applications."
            );
        }


        updateApplicationStatistics(
            data.statistics ||
            {}
        );


        renderApplications(
            data.applications ||
            []
        );

    }
    catch (error) {

        console.error(
            "Load applications failed:",
            error
        );


        container.innerHTML =
            emptyMessage(
                "Could not load applications."
            );

    }
    finally {

        if (loading) {

            loading.style.display =
                "none";
        }
    }
}


/* =========================================================
   APPLICATION STATISTICS
========================================================= */

function updateApplicationStatistics(
    stats
) {

    const mapping = {

        "stat-total":
            "total",

        "stat-applied":
            "applied",

        "stat-interview":
            "interview",

        "stat-offer":
            "offer",

        "stat-rejected":
            "rejected"
    };


    Object.entries(
        mapping
    ).forEach(
        ([elementId, key]) => {

            const element =
                document.getElementById(
                    elementId
                );


            if (element) {

                element.textContent =
                    Number(
                        stats[key] ||
                        0
                    );
            }
        }
    );
}


/* =========================================================
   RENDER APPLICATIONS
========================================================= */

function renderApplications(
    applications
) {

    const container =
        document.getElementById(
            "applications-list"
        );


    if (!container) {
        return;
    }


    applications =
        normalizeArray(
            applications
        );


    if (
        applications.length === 0
    ) {

        container.innerHTML =
            emptyMessage(
                "No applications tracked yet. Add your first application above."
            );

        return;
    }


    const statuses = [

        "Saved",

        "Applied",

        "Screening",

        "Interview",

        "Offer",

        "Rejected",

        "Withdrawn"
    ];


    container.innerHTML =
        applications
            .map(
                application => `

                    <div class="application-card">

                        <div class="application-card-header">

                            <div>

                                <span class="application-company">

                                    ${escapeHtml(
                                        application.company ||
                                        "Company"
                                    )}

                                </span>

                                <h3>

                                    ${escapeHtml(
                                        application.role ||
                                        "Role"
                                    )}

                                </h3>

                            </div>


                            <div class="application-actions">

                                <select
                                    class="application-status-select"
                                    onchange="updateApplicationStatus(
                                        ${Number(application.id)},
                                        this.value
                                    )"
                                >

                                    ${statuses
                                        .map(
                                            status =>
                                                `
                                                <option
                                                    value="${escapeAttribute(status)}"
                                                    ${
                                                        status ===
                                                        application.status
                                                            ? "selected"
                                                            : ""
                                                    }
                                                >
                                                    ${escapeHtml(status)}
                                                </option>
                                                `
                                        )
                                        .join("")}

                                </select>


                                <button
                                    type="button"
                                    class="secondary-button"
                                    onclick="deleteApplication(
                                        ${Number(application.id)}
                                    )"
                                >
                                    Delete
                                </button>

                            </div>

                        </div>


                        <div class="application-meta">

                            ${
                                application.applied_date
                                    ? `
                                        <span>
                                            ▣ ${escapeHtml(
                                                application.applied_date
                                            )}
                                        </span>
                                      `
                                    : ""
                            }


                            ${
                                application.job_url
                                    ? `
                                        <a
                                            class="application-link"
                                            href="${escapeAttribute(
                                                application.job_url
                                            )}"
                                            target="_blank"
                                            rel="noopener noreferrer"
                                        >
                                            Job Posting
                                        </a>
                                      `
                                    : ""
                            }

                        </div>


                        ${
                            application.notes
                                ? `
                                    <div class="application-notes">

                                        ${escapeHtml(
                                            application.notes
                                        )}

                                    </div>
                                  `
                                : ""
                        }

                    </div>
                `
            )
            .join("");
}


/* =========================================================
   UPDATE APPLICATION STATUS
========================================================= */

async function updateApplicationStatus(
    applicationId,
    status
) {

    try {

        const response =
            await fetch(
                `${API_BASE_URL}/applications/${applicationId}`,
                {
                    method: "PUT",
                    credentials: "include",
                    headers: {
                        "Content-Type":
                            "application/json"
                    },
                    body: JSON.stringify({
                        status:
                            status
                    })
                }
            );


        const data =
            await readJsonResponse(
                response
            );


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Could not update application."
            );
        }


        await loadApplications();

    }
    catch (error) {

        console.error(
            "Update application failed:",
            error
        );


        showBackendError(
            error.message
        );


        await loadApplications();
    }
}


/* =========================================================
   DELETE APPLICATION
========================================================= */

async function deleteApplication(
    applicationId
) {

    if (
        !confirm(
            "Are you sure you want to delete this application?"
        )
    ) {

        return;
    }


    try {

        const response =
            await fetch(
                `${API_BASE_URL}/applications/${applicationId}`,
                {
                    method: "DELETE",
                    credentials: "include"
                }
            );


        const data =
            await readJsonResponse(
                response
            );


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Could not delete application."
            );
        }


        await loadApplications();

    }
    catch (error) {

        console.error(
            "Delete application failed:",
            error
        );


        showBackendError(
            error.message
        );
    }
}


/* =========================================================
   NORMALIZE ARRAY
========================================================= */

function normalizeArray(
    value
) {

    if (Array.isArray(value)) {
        return value;
    }


    if (
        value === null ||
        value === undefined
    ) {
        return [];
    }


    if (
        typeof value === "string"
    ) {

        const text =
            value.trim();


        if (!text) {
            return [];
        }


        /*
         * Try JSON array first.
         */

        try {

            const parsed =
                JSON.parse(text);


            if (Array.isArray(parsed)) {
                return parsed;
            }

        }
        catch (error) {
            // Not JSON. Continue.
        }


        /*
         * Support newline-separated values.
         */

        if (
            text.includes("\n")
        ) {

            return text
                .split("\n")
                .map(
                    item =>
                        item.trim()
                )
                .filter(Boolean);
        }


        /*
         * Support comma-separated values.
         */

        if (
            text.includes(",")
        ) {

            return text
                .split(",")
                .map(
                    item =>
                        item.trim()
                )
                .filter(Boolean);
        }


        /*
         * Single string.
         */

        return [text];
    }


    return [value];
}


/* =========================================================
   NORMALIZE EXPERIENCE
========================================================= */

function normalizeExperience(
    experience
) {

    if (
        experience === null ||
        experience === undefined
    ) {

        return [];
    }


    /*
     * Already an array.
     */

    if (
        Array.isArray(experience)
    ) {

        return experience
            .map(
                item => {

                    if (
                        typeof item ===
                        "string"
                    ) {

                        return {
                            text:
                                item,

                            description:
                                item
                        };
                    }


                    if (
                        item &&
                        typeof item ===
                        "object"
                    ) {

                        return item;
                    }


                    return {
                        text:
                            String(item),

                        description:
                            String(item)
                    };
                }
            );
    }


    /*
     * Backend currently returns experience
     * as a single string.
     *
     * Example:
     *
     * "Business Data Analyst at Avecal India Pvt Limited..."
     */

    if (
        typeof experience ===
        "string"
    ) {

        const text =
            experience.trim();


        if (!text) {
            return [];
        }


        return [
            {
                text:
                    text,

                description:
                    text
            }
        ];
    }


    /*
     * Object.
     */

    if (
        typeof experience ===
        "object"
    ) {

        return [
            experience
        ];
    }


    return [
        {
            text:
                String(experience),

            description:
                String(experience)
        }
    ];
}


/* =========================================================
   SCORE BOX
========================================================= */

function scoreBox(
    label,
    value
) {

    return `

        <div class="result-box">

            <span>
                ${escapeHtml(label)}
            </span>

            <strong>
                ${escapeHtml(value)}%
            </strong>

        </div>
    `;
}


/* =========================================================
   SKILL GROUP
========================================================= */

function renderSkillGroup(
    title,
    skills,
    className
) {

    skills =
        normalizeArray(
            skills
        );


    if (
        skills.length === 0
    ) {

        return "";
    }


    return `

        <div class="skill-section">

            <h3>
                ${escapeHtml(title)}
            </h3>

            <div class="skill-tags">

                ${skills
                    .map(
                        skill =>
                            `
                            <span class="skill-tag ${escapeAttribute(className)}">

                                ${escapeHtml(
                                    typeof skill === "string"
                                        ? skill
                                        : JSON.stringify(skill)
                                )}

                            </span>
                            `
                    )
                    .join("")}

            </div>

        </div>
    `;
}


/* =========================================================
   FORMAT LABEL
========================================================= */

function formatLabel(
    value
) {

    return String(
        value
    )
        .replaceAll(
            "_",
            " "
        )
        .replace(
            /\b\w/g,
            character =>
                character.toUpperCase()
        );
}


/* =========================================================
   EMPTY MESSAGE
========================================================= */

function emptyMessage(
    message
) {

    return `

        <div class="empty-message">

            <span>
                ▤
            </span>

            <p>
                ${escapeHtml(message)}
            </p>

        </div>
    `;
}


/* =========================================================
   LOADING
========================================================= */

let loadingTimer = null;

function showLoading(
    message
) {

    const loading = document.getElementById("loading");

    const loadingMessage = document.getElementById("loading-message");

    if (loading) {
        loading.style.display = "block";
    }

    if (!loadingMessage) {
        return;
    }

    const startedAt = Date.now();

    const render = () => {
        const seconds = Math.floor((Date.now() - startedAt) / 1000);
        loadingMessage.textContent = seconds >= 3
            ? `${message} (${seconds}s)`
            : message;
    };

    render();

    if (loadingTimer) {
        clearInterval(loadingTimer);
    }

    loadingTimer = setInterval(render, 1000);
}


/* =========================================================
   HIDE LOADING
========================================================= */

function hideLoading() {

    if (loadingTimer) {
        clearInterval(loadingTimer);
        loadingTimer = null;
    }

    const loading =
        document.getElementById(
            "loading"
        );


    if (loading) {

        loading.style.display =
            "none";
    }
}


/* =========================================================
   BACKEND ERROR
========================================================= */

function showBackendError(
    message
) {

    const errorBox =
        document.getElementById(
            "backend-error"
        );


    if (!errorBox) {

        alert(
            message ||
            "Something went wrong."
        );

        return;
    }


    errorBox.textContent =
        message ||
        "Something went wrong.";


    errorBox.style.display =
        "block";


    setTimeout(
        () => {

            errorBox.style.display =
                "none";

        },
        8000
    );
}


/* =========================================================
   HTML ESCAPING
========================================================= */

function escapeHtml(
    value
) {

    return String(
        value ?? ""
    )
        .replaceAll(
            "&",
            "&amp;"
        )
        .replaceAll(
            "<",
            "&lt;"
        )
        .replaceAll(
            ">",
            "&gt;"
        )
        .replaceAll(
            '"',
            "&quot;"
        )
        .replaceAll(
            "'",
            "&#039;"
        );
}


/* =========================================================
   ATTRIBUTE ESCAPING
========================================================= */

function escapeAttribute(
    value
) {

    return escapeHtml(
        value
    );
}


/* =========================================================
   READ JSON RESPONSE
========================================================= */

async function readJsonResponse(
    response
) {

    const text =
        await response.text();


    if (!text) {
        return {};
    }


    try {

        return JSON.parse(
            text
        );

    }
    catch (error) {

        return {
            detail:
                text
        };
    }
}


/* =========================================================
   SLEEP
========================================================= */

function sleep(
    milliseconds
) {

    return new Promise(
        resolve =>
            setTimeout(
                resolve,
                milliseconds
            )
    );
}
