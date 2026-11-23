const API_URL = "http://127.0.0.1:8000/api";

const $ = (id) => document.getElementById(id);

async function apiRequest(endpoint, options = {}) {
    const response = await fetch(`${API_URL}${endpoint}`, options);

    const data = await response.json().catch(() => ({
        detail: "The server returned an invalid response."
    }));

    if (!response.ok) {
        throw new Error(
            data.detail || "Something went wrong."
        );
    }

    return data;
}

function getFormData(form) {
    return Object.fromEntries(
        new FormData(form).entries()
    );
}

function showMessage(elementId, message, isError = false) {
    const element = $(elementId);

    element.textContent = message;

    element.style.color = isError
        ? "#a33"
        : "#315c45";
}

function escapeHTML(value) {
    return String(value ?? "").replace(
        /[&<>"']/g,
        character => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;"
        })[character]
    );
}

/* Public event summary */

async function loadEventSummary() {
    try {
        const summary = await apiRequest("/public/summary");

        $("attendeeCount").textContent =
            Number(summary.expected_attendees).toLocaleString();

        $("pledgeTotal").textContent =
            `KES ${Number(summary.pledged_total).toLocaleString()}`;

    } catch (error) {
        $("attendeeCount").textContent = "—";
        $("pledgeTotal").textContent = "—";

        console.error("Summary error:", error);
    }
}

/* RSVP form */

$("rsvpForm").addEventListener("submit", async (event) => {
    event.preventDefault();

    const form = event.currentTarget;
    const submitButton = form.querySelector("button[type=submit]");

    const payload = getFormData(form);

    payload.guests = Number(payload.guests);

    submitButton.disabled = true;
    submitButton.textContent = "Submitting...";

    try {
        const result = await apiRequest("/rsvps", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        showMessage(
            "rsvpFeedback",
            result.message
        );

        form.reset();

        await loadEventSummary();

    } catch (error) {
        showMessage(
            "rsvpFeedback",
            error.message,
            true
        );

    } finally {
        submitButton.disabled = false;
        submitButton.innerHTML = "Submit RSVP <span>↗</span>";
    }
});

/* Pledge form */

$("pledgeForm").addEventListener("submit", async (event) => {
    event.preventDefault();

    const form = event.currentTarget;
    const submitButton = form.querySelector("button[type=submit]");

    const payload = getFormData(form);

    payload.amount = Number(payload.amount);

    if (!payload.email) {
        delete payload.email;
    }

    submitButton.disabled = true;
    submitButton.textContent = "Recording...";

    try {
        const result = await apiRequest("/pledges", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        showMessage(
            "pledgeFeedback",
            result.message
        );

        form.reset();

        await loadEventSummary();

    } catch (error) {
        showMessage(
            "pledgeFeedback",
            error.message,
            true
        );

    } finally {
        submitButton.disabled = false;
        submitButton.innerHTML = "Record my pledge <span>↗</span>";
    }
});

/* Organizer modal */

$("openAdmin").addEventListener("click", () => {
    $("adminModal").classList.remove("hidden");
});

$("closeAdmin").addEventListener("click", () => {
    $("adminModal").classList.add("hidden");
});

$("adminModal").addEventListener("click", (event) => {
    if (event.target === $("adminModal")) {
        $("adminModal").classList.add("hidden");
    }
});

document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
        $("adminModal").classList.add("hidden");
    }
});

function adminHeaders() {
    return {
        "X-Admin-Key": $("adminKey").value
    };
}

/* Safe table rendering */

function renderTable(records, columns) {
    if (!records.length) {
        return "<p>No records available.</p>";
    }

    const header = columns
        .map(column => `<th>${escapeHTML(column.label)}</th>`)
        .join("");

    const body = records.map(record => {
        const cells = columns.map(column => {
            return `<td>${escapeHTML(record[column.key])}</td>`;
        }).join("");

        return `<tr>${cells}</tr>`;
    }).join("");

    return `
        <table>
            <thead>
                <tr>${header}</tr>
            </thead>
            <tbody>${body}</tbody>
        </table>
    `;
}

/* Load organizer dashboard */

$("loadDashboard").addEventListener("click", async () => {
    const button = $("loadDashboard");

    button.disabled = true;
    showMessage("adminFeedback", "Loading organizer records...");

    try {
        const headers = adminHeaders();

        const [rsvps, pledges] = await Promise.all([
            apiRequest("/admin/rsvps", { headers }),
            apiRequest("/admin/pledges", { headers })
        ]);

        $("rsvpTable").innerHTML = renderTable(
            rsvps,
            [
                { key: "full_name", label: "Guest" },
                { key: "email", label: "Email" },
                { key: "guests", label: "Guests" },
                { key: "attendance", label: "Response" }
            ]
        );

        $("pledgeTable").innerHTML = renderTable(
            pledges,
            [
                { key: "full_name", label: "Contributor" },
                { key: "amount", label: "Amount" },
                { key: "currency", label: "Currency" },
                { key: "purpose", label: "Purpose" },
                { key: "status", label: "Status" }
            ]
        );

        $("dashboardContent").classList.remove("hidden");

        showMessage(
            "adminFeedback",
            `${rsvps.length} RSVPs and ${pledges.length} pledges loaded.`
        );

    } catch (error) {
        $("dashboardContent").classList.add("hidden");

        showMessage(
            "adminFeedback",
            error.message,
            true
        );

    } finally {
        button.disabled = false;
    }
});

/* CSV exports */

async function downloadCSV(reportType) {
    try {
        const response = await fetch(
            `${API_URL}/admin/export/${reportType}`,
            {
                headers: adminHeaders()
            }
        );

        if (!response.ok) {
            const data = await response.json().catch(() => ({}));

            throw new Error(
                data.detail || "Unable to export this report."
            );
        }

        const blob = await response.blob();

        const downloadURL = URL.createObjectURL(blob);

        const link = document.createElement("a");

        link.href = downloadURL;
        link.download = `${reportType}-report.csv`;

        document.body.appendChild(link);

        link.click();
        link.remove();

        URL.revokeObjectURL(downloadURL);

    } catch (error) {
        showMessage(
            "adminFeedback",
            error.message,
            true
        );
    }
}

$("exportRsvps").addEventListener("click", () => {
    downloadCSV("rsvps");
});

$("exportPledges").addEventListener("click", () => {
    downloadCSV("pledges");
});

/* Initial application setup */

loadEventSummary();
