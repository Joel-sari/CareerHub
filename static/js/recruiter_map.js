// static/js/recruiter_map.js
(function () {
  let map;
  let mode = "jobs"; // "jobs" | "applicants"
  let jobMarkers = [];
  let applicantMarkers = [];

  const payload = window.CAREERHUB_RECRUITER || {};
  const jobs = payload.jobs || [];
  const applicants = payload.applicants || [];

  const jobListEl = document.getElementById("jobList");
  const btnJobs = document.getElementById("btn-job-locations");
  const btnApplicants = document.getElementById("btn-applicant-focus");

  // === Sorting & Filtering Dropdown Elements (added for improved recruiter UX) ===
  // These dropdowns should exist in the HTML:
  // <select id="sortJobs">...</select>
  // <select id="filterJobs">...</select>
  const sortSelect = document.getElementById("sortJobs");
  const filterSelect = document.getElementById("filterJobs");

  // --- Sort job list based on selected criteria ---
  // Supports sorting by title, company, or applicant count.
  function sortJobs(list) {
    if (!sortSelect) return list; // No UI, skip

    const mode = sortSelect.value;

    return [...list].sort((a, b) => {
      if (mode === "title") return a.title.localeCompare(b.title);
      if (mode === "company")
        return (a.company || "").localeCompare(b.company || "");
      if (mode === "applicants") {
        const acA = applicantCountById.get(a.id) || 0;
        const acB = applicantCountById.get(b.id) || 0;
        return acB - acA; // Highest first
      }
      return 0;
    });
  }

  // --- Filter jobs (only ones with applicants, etc.) ---
  function filterJobs(list) {
    if (!filterSelect) return list;

    const mode = filterSelect.value;
    if (mode === "withApplicants") {
      return list.filter((j) => (applicantCountById.get(j.id) || 0) > 0);
    }
    return list;
  }

  // Same light style as job seeker map
  const MAP_STYLE = [
    { elementType: "geometry", stylers: [{ color: "#f5f5f5" }] },
    { elementType: "labels.icon", stylers: [{ visibility: "off" }] },
    { elementType: "labels.text.fill", stylers: [{ color: "#616161" }] },
    { elementType: "labels.text.stroke", stylers: [{ color: "#f5f5f5" }] },
    {
      featureType: "administrative.land_parcel",
      stylers: [{ visibility: "off" }],
    },
    { featureType: "poi", stylers: [{ visibility: "off" }] },
    { featureType: "road", stylers: [{ color: "#ffffff" }] },
    { featureType: "road.arterial", stylers: [{ color: "#ffffff" }] },
    { featureType: "road.highway", stylers: [{ color: "#e5e5e5" }] },
    { featureType: "water", stylers: [{ color: "#c9e7ff" }] },
  ];

  // Map of job_id -> applicant count
  const applicantCountById = new Map();
  (applicants || []).forEach((a) => {
    applicantCountById.set(a.id, a.applicants || 0);
  });

  function basePin() {
    return {
      path: "M12 2C7.58 2 4 5.58 4 10c0 5.25 8 12 8 12s8-6.75 8-12c0-4.42-3.58-8-8-8zm0 10.5a2.5 2.5 0 1 1 0-5 2.5 2.5 0 0 1 0 5z",
      fillColor: "#2563eb", // blue
      fillOpacity: 1,
      strokeWeight: 0,
      scale: 1,
      anchor: new google.maps.Point(12, 24),
    };
  }

  function heatPin(count) {
    const scale = 0.9 + Math.min(count, 15) * 0.1;
    return {
      path: "M12 2C7.58 2 4 5.58 4 10c0 5.25 8 12 8 12s8-6.75 8-12c0-4.42-3.58-8-8-8zm0 10.5a2.5 2.5 0 1 1 0-5 2.5 2.5 0 0 1 0 5z",
      fillColor: "#f97316", // orange
      fillOpacity: 0.95,
      strokeWeight: 0,
      scale,
      anchor: new google.maps.Point(12, 24),
    };
  }

  function createMarkers() {
    jobMarkers = [];
    applicantMarkers = [];

    (jobs || []).forEach((j) => {
      if (j.lat == null || j.lng == null) return;

      const pos = { lat: j.lat, lng: j.lng };
      const title = `${j.title} · ${j.company || ""}`.trim();

      const infoHtml = `
        <div style="max-width:240px">
          <div style="font-weight:600">${j.title}</div>
          <div style="color:#555">${j.company || ""}</div>
          <div style="color:#666">${j.location || ""}</div>
          <a href="${
            j.detailUrl
          }" target="_blank" rel="noopener" style="color:#2563eb">
            View details
          </a>
        </div>
      `;

      const infoWindow = new google.maps.InfoWindow({ content: infoHtml });

      // Normal job location marker (blue)
      const mJob = new google.maps.Marker({
        position: pos,
        map,
        title,
        icon: basePin(),
      });
      mJob.addListener("click", () => infoWindow.open({ anchor: mJob, map }));
      jobMarkers.push(mJob);

      // Applicant “heat” marker (orange, scaled)
      const count = applicantCountById.get(j.id) || 0;
      if (count > 0) {
        const mApp = new google.maps.Marker({
          position: pos,
          map: null, // toggled per mode
          title: `${title} · ${count} applicants`,
          icon: heatPin(count),
        });
        mApp.addListener("click", () => infoWindow.open({ anchor: mApp, map }));
        applicantMarkers.push(mApp);
      }
    });
  }

  function fitToMarkers(markers) {
    const valid = (markers || []).filter(Boolean);
    if (!valid.length) return;
    const bounds = new google.maps.LatLngBounds();
    valid.forEach((m) => bounds.extend(m.getPosition()));
    map.fitBounds(bounds);
    // Prevent the map from zooming in too close when only one or few markers exist
    google.maps.event.addListenerOnce(map, "idle", () => {
      const currentZoom = map.getZoom();
      // Force a wider, more zoomed‑out default view
      if (currentZoom > 8) {
        map.setZoom(8);
      }
    });
  }

  // === Render the job list with redesigned UI, hover effects, and map-panning ===
  function renderList() {
    if (!jobListEl) return;

    // Apply filters then sorting
    let list = jobs || [];
    list = filterJobs(list);
    list = sortJobs(list);

    // Empty-state UI
    if (!list.length) {
      jobListEl.innerHTML =
        '<li class="p-3 text-secondary small">No jobs match the selected filter.</li>';
      return;
    }

    // Build new recruiter job cards
    jobListEl.innerHTML = list
      .map((j) => {
        const count = applicantCountById.get(j.id) || 0;

        // Badge color logic (visual heatmap)
        const badgeColor =
          count === 0
            ? "#aaa" // No applicants → gray
            : count < 5
            ? "#2563eb" // Low activity → blue
            : count < 20
            ? "#f97316" // Medium activity → orange
            : "#dc2626"; // High activity → red

        return `
          <li class="job-card" data-id="${j.id}"
            style="
              background:#fff;
              border-radius:12px;
              padding:16px;
              margin-bottom:12px;
              box-shadow:0 1px 3px rgba(0,0,0,0.08);
              transition:0.2s ease;
              cursor:pointer;
            "
          >
            <!-- Job Title -->
            <div style="font-weight:600; font-size:15px;">${j.title}</div>

            <!-- Company -->
            <div style="color:#555; margin-top:2px;">${j.company || ""}</div>

            <!-- Location -->
            <div style="color:#666; font-size:13px;">${j.location || ""}</div>

            <!-- Applicant count badge -->
            <span style="
              display:inline-block;
              margin-top:8px;
              padding:3px 10px;
              background:${badgeColor};
              color:white;
              border-radius:20px;
              font-size:12px;
            ">
              ${count} applicant${count === 1 ? "" : "s"}
            </span>

            <!-- Link to job detail page -->
            <a class="small" href="${j.detailUrl}"
              target="_blank" rel="noopener"
              style="display:block; margin-top:10px; color:#2563eb; font-size:13px;">
              Open job
            </a>
          </li>
        `;
      })
      .join("");

    // === Add interactive behavior for each card ===
    document.querySelectorAll(".job-card").forEach((el) => {
      // Hover effect (scale + stronger shadow)
      el.addEventListener("mouseenter", () => {
        el.style.transform = "scale(1.02)";
        el.style.boxShadow = "0 4px 12px rgba(0,0,0,0.12)";
      });
      el.addEventListener("mouseleave", () => {
        el.style.transform = "scale(1)";
        el.style.boxShadow = "0 1px 3px rgba(0,0,0,0.08)";
      });

      // Clicking a job card pans the map to that job’s marker
      el.addEventListener("click", () => {
        const id = parseInt(el.getAttribute("data-id"));
        const job = jobs.find((j) => j.id === id);
        if (!job) return;

        // Find corresponding marker on the map
        const marker = jobMarkers.find((m) => {
          const pos = m.getPosition();
          return pos.lat() === job.lat && pos.lng() === job.lng;
        });

        if (marker) {
          map.panTo(marker.getPosition());
          map.setZoom(8); // Ensure reasonable zoom level

          // Automatically open its InfoWindow
          google.maps.event.trigger(marker, "click");
        }
      });
    });
  }

  function setMode(newMode) {
    mode = newMode;

    // Toggle button styles
    if (btnJobs && btnApplicants) {
      if (mode === "jobs") {
        btnJobs.classList.add("btn-primary");
        btnJobs.classList.remove("btn-outline-primary");
        btnApplicants.classList.remove("btn-primary");
        btnApplicants.classList.add("btn-outline-primary");
      } else {
        btnApplicants.classList.add("btn-primary");
        btnApplicants.classList.remove("btn-outline-primary");
        btnJobs.classList.remove("btn-primary");
        btnJobs.classList.add("btn-outline-primary");
      }
    }

    // Show/hide markers
    jobMarkers.forEach((m) => m.setMap(mode === "jobs" ? map : null));
    applicantMarkers.forEach((m) =>
      m.setMap(mode === "applicants" ? map : null)
    );

    const active = mode === "jobs" ? jobMarkers : applicantMarkers;
    fitToMarkers(active.length ? active : jobMarkers);
  }

  function boot() {
    map = new google.maps.Map(document.getElementById("map"), {
      center: { lat: 20, lng: 0 },
      zoom: 4,
      mapTypeControl: false,
      streetViewControl: false,
      styles: MAP_STYLE,
    });

    createMarkers();
    renderList();
    setMode("jobs");

    btnJobs && btnJobs.addEventListener("click", () => setMode("jobs"));
    btnApplicants &&
      btnApplicants.addEventListener("click", () => setMode("applicants"));
  }

  // Wait until Google Maps JS is ready
  const wait = setInterval(() => {
    if (window.google && window.google.maps) {
      clearInterval(wait);
      boot();
    }
  }, 80);
})();
