// Initialize the map centered on Hyderabad
const map = L.map('map').setView([HYDERABAD_CENTER.lat, HYDERABAD_CENTER.lng], 12);

// Add OpenStreetMap tiles
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

// Custom icon for vendors
const vendorIcon = L.icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

// Function to calculate distance between two points
function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371; // Radius of the Earth in km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return (R * c).toFixed(1); // Distance in km
}

// Function to show vendors on map
function showVendors(category = 'general') {
    // Clear existing markers
    map.eachLayer((layer) => {
        if (layer instanceof L.Marker) {
            map.removeLayer(layer);
        }
    });

    // Add center marker
    L.marker([HYDERABAD_CENTER.lat, HYDERABAD_CENTER.lng], {
        icon: L.icon({
            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
            shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
            shadowSize: [41, 41]
        })
    }).addTo(map).bindPopup('You are here (Hyderabad City Center)');

    // Show vendors for the selected category
    const categoryVendors = vendors[category] || vendors['general'];
    categoryVendors.forEach(vendor => {
        const distance = calculateDistance(
            HYDERABAD_CENTER.lat,
            HYDERABAD_CENTER.lng,
            vendor.lat,
            vendor.lng
        );

        const marker = L.marker([vendor.lat, vendor.lng], {icon: vendorIcon})
            .addTo(map)
            .bindPopup(`
                <div class="vendor-info">
                    <div class="vendor-name">${vendor.name}</div>
                    <div class="vendor-address">${vendor.address}</div>
                    <div class="vendor-description">${vendor.description}</div>
                    <div class="vendor-distance">${distance} km from city center</div>
                </div>
            `);
    });
}

// Function to get vendors list as HTML
function getVendorsListHTML(category = 'general') {
    const categoryVendors = vendors[category] || vendors['general'];
    return categoryVendors.map(vendor => {
        const distance = calculateDistance(
            HYDERABAD_CENTER.lat,
            HYDERABAD_CENTER.lng,
            vendor.lat,
            vendor.lng
        );
        return `
            <div class="vendor-card">
                <h3>${vendor.name}</h3>
                <p>${vendor.description}</p>
                <p><strong>Address:</strong> ${vendor.address}</p>
                <p><strong>Distance:</strong> ${distance} km from city center</p>
            </div>
        `;
    }).join('');
}

// Initialize map with general vendors
showVendors(); 