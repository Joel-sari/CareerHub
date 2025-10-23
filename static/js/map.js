(function () {
  let map, markers = [], clusterer, jobs = [], selectedId = null;

  const listEl = document.getElementById('nearbyList');
  const radiusSelect = document.getElementById('radiusSelect');
  const refreshBtn = document.getElementById('refreshNearby');
  const resultCount = document.getElementById('resultCount');

  // Pleasant light map style
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
    { featureType: "water", stylers: [{ color: "#c9e7ff" }] }
  ];

  // Haversine distance (miles)
  function distMiles(a, b) {
    const R = 3958.8, toRad = d => d * Math.PI/180;
    const dLat = toRad(b.lat - a.lat), dLng = toRad(b.lng - a.lng);
    const lat1 = toRad(a.lat), lat2 = toRad(b.lat);
    const x = Math.sin(dLat/2)**2 + Math.cos(lat1)*Math.cos(lat2)*Math.sin(dLng/2)**2;
    return 2 * R * Math.asin(Math.sqrt(x));
  }

  // Simple brand-colored SVG marker
  function svgPin(active=false) {
    const fill = active ? "#2563eb" : "#ef4444";
    return {
      path: "M12 2C7.58 2 4 5.58 4 10c0 5.25 8 12 8 12s8-6.75 8-12c0-4.42-3.58-8-8-8zm0 10.5a2.5 2.5 0 1 1 0-5 2.5 2.5 0 0 1 0 5z",
      fillColor: fill, fillOpacity: 1, strokeWeight: 0, scale: 1, anchor: new google.maps.Point(12, 24)
    };
  }

  function createMarker(j) {
    const m = new google.maps.Marker({
      position: { lat: j.lat, lng: j.lng },
      map,
      title: `${j.title} · ${j.company || ''}`.trim(),
      icon: svgPin(false)
    });
    m.__jobId = j.id;

    const iw = new google.maps.InfoWindow({
      content: `
        <div style="max-width:240px">
          <div style="font-weight:600">${j.title}</div>
          <div style="color:#555">${j.company || ''}</div>
          <div style="color:#666">${j.location || ''}</div>
          <a href="${j.detailUrl}" target="_blank" rel="noopener" style="color:#2563eb">View details</a>
        </div>`
    });

    m.addListener('click', () => {
      selectJob(j.id, true);
      iw.open({ anchor: m, map });
    });

    return m;
  }

  function markerForJobId(id) {
    return markers.find(m => m && m.__jobId === id);
  }

  function fitToMarkers() {
    const valid = markers.filter(Boolean);
    if (!valid.length) return;
    const b = new google.maps.LatLngBounds();
    valid.forEach(m => b.extend(m.getPosition()));
    map.fitBounds(b);
  }

  function renderList(nearby) {
    resultCount.textContent = nearby.length;
    listEl.innerHTML = nearby.length ? nearby.map(x => `
      <li class="job-card" data-id="${x.id}">
        <div class="job-title">${x.title}</div>
        <div class="job-meta">${x.company || ''}</div>
        <div class="job-meta">${x.location || ''}</div>
        <div class="job-distance">~ ${x.distance.toFixed(1)} mi away</div>
        <a class="link-primary small" href="${x.detailUrl}" target="_blank" rel="noopener">Open</a>
      </li>
    `).join('') : `
      <li class="p-3 text-secondary">No nearby jobs within ${radiusSelect.value} miles.</li>
    `;

    // hover + click sync
    listEl.querySelectorAll('.job-card').forEach(li => {
      const id = parseInt(li.dataset.id);
      li.addEventListener('mouseenter', () => highlightMarker(id, true));
      li.addEventListener('mouseleave', () => highlightMarker(id, false));
      li.addEventListener('click', () => selectJob(id, true));
    });

    // set selected styling if exists
    if (selectedId) {
      const active = listEl.querySelector(`.job-card[data-id="${selectedId}"]`);
      if (active) active.classList.add('active');
    }
  }

    function highlightMarker(id, on) {
      const m = markerForJobId(id);
      if (!m) return;
      // just change color; no animation
      m.setIcon(svgPin(on || id === selectedId));
    }

    function selectJob(id, panToMarker = false) {
      // list styling
      listEl.querySelectorAll('.job-card').forEach(el => el.classList.remove('active'));
      const active = listEl.querySelector(`.job-card[data-id="${id}"]`);
      if (active) active.classList.add('active');

      // update marker colors
      if (selectedId && selectedId !== id) highlightMarker(selectedId, false);
      selectedId = id;
      highlightMarker(id, true);

      // pan + zoom
      if (panToMarker) {
        const m = markerForJobId(id);
        if (m) {
          map.panTo(m.getPosition());
          const targetZoom = 13; // tweak if you want closer/farther
          if (map.getZoom() < targetZoom) map.setZoom(targetZoom);
        }
      }
    }

  function computeNearby(user) {
    const radius = parseFloat(radiusSelect.value);
    return jobs
      .filter(j => j.lat != null && j.lng != null)
      .map(j => ({ ...j, distance: user ? distMiles(user, {lat:j.lat, lng:j.lng}) : Infinity }))
      .filter(x => x.distance <= radius)
      .sort((a,b) => a.distance - b.distance)
      .slice(0, 50);
  }

  function locateAndRender() {
    const render = (user) => {
      const nearby = computeNearby(user);
      renderList(nearby);
    };

    if (!navigator.geolocation) return render(null);
    navigator.geolocation.getCurrentPosition(
      pos => render({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      ()  => render(null),
      { enableHighAccuracy: true, timeout: 8000 }
    );
  }

  async function boot() {
    map = new google.maps.Map(document.getElementById('map'), {
      center: { lat: 20, lng: 0 },
      zoom: 2,
      mapTypeControl: false,
      streetViewControl: false,
      styles: MAP_STYLE
    });

    // Fetch jobs
    const res = await fetch(window.CAREERHUB.jobsApiUrl, { credentials: "same-origin" });
    const { jobs: items } = await res.json();
    jobs = (items || []).filter(j => j.lat != null && j.lng != null);

    // Build markers
    markers = jobs.map(createMarker).filter(Boolean);

    // Cluster markers (nicer in dense cities)
    if (window.markerClusterer) {
      clusterer = new markerClusterer.MarkerClusterer({ map, markers });
    }

    fitToMarkers();
    locateAndRender();

    refreshBtn?.addEventListener('click', locateAndRender);
    radiusSelect?.addEventListener('change', locateAndRender);
  }

  // Wait for Google Maps to load
  const wait = setInterval(() => {
    if (window.google && window.google.maps) { clearInterval(wait); boot(); }
  }, 80);
})();
