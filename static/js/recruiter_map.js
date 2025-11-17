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

  // Same light style as job seeker map
  const MAP_STYLE = [
    { elementType: "geometry", stylers: [{ color: "#f5f5f5" }] },
    { elementType: "labels.icon", stylers: [{ visibility: "off" }] },
    { elementType: "labels.text.fill", stylers: [{ color: "#616161" }] },
    { elementType: "labels.text.stroke", stylers: [{ color: "#f5f5f5" }] },
    { featureType: "administrative.land_parcel", stylers: [{ visibility: "off" }] },
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
          <a href="${j.detailUrl}" target="_blank" rel="noopener" style="color:#2563eb">
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
  }

  function renderList() {
    if (!jobListEl) return;

    if (!jobs || !jobs.length) {
      jobListEl.innerHTML =
        '<li class="p-3 text-secondary small">You have no live roles with locations yet.</li>';
      return;
    }

    jobListEl.innerHTML = jobs
      .map((j) => {
        const count = applicantCountById.get(j.id) || 0;
        const label = count === 0 ? "No applicants yet" : `${count} applicant${count === 1 ? "" : "s"}`;
        return `
          <li class="job-card" data-id="${j.id}">
            <div class="job-title">${j.title}</div>
            <div class="job-meta">${j.company || ""}</div>
            <div class="job-meta">${j.location || ""}</div>
            <div class="job-distance">${label}</div>
            <a class="link-primary small" href="${j.detailUrl}" target="_blank" rel="noopener">
              Open job
            </a>
          </li>
        `;
      })
      .join("");
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
    applicantMarkers.forEach((m) => m.setMap(mode === "applicants" ? map : null));

    const active = mode === "jobs" ? jobMarkers : applicantMarkers;
    fitToMarkers(active.length ? active : jobMarkers);
  }

  function boot() {
    map = new google.maps.Map(document.getElementById("map"), {
      center: { lat: 20, lng: 0 },
      zoom: 2,
      mapTypeControl: false,
      streetViewControl: false,
      styles: MAP_STYLE,
    });

    createMarkers();
    renderList();
    setMode("jobs");

    btnJobs && btnJobs.addEventListener("click", () => setMode("jobs"));
    btnApplicants && btnApplicants.addEventListener("click", () => setMode("applicants"));
  }

  // Wait until Google Maps JS is ready
  const wait = setInterval(() => {
    if (window.google && window.google.maps) {
      clearInterval(wait);
      boot();
    }
  }, 80);
})();
