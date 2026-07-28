document.addEventListener('DOMContentLoaded', () => {
  const mapElement = document.getElementById('map');
  if (!mapElement) return;

  const map = L.map('map', { zoomControl: false }).setView([6.0900, -0.2600], 15);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap'
  }).addTo(map);

  L.marker([6.0900, -0.2600]).addTo(map);
  L.circle([6.0900, -0.2600], {
    color: '#0284c7',
    fillColor: '#38bdf8',
    fillOpacity: 0.2,
    radius: 250
  }).addTo(map);
});
