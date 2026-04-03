const CONFIG_PATH = "../config/nodes.json";

async function loadDashboardData() {
    const response = await fetch(CONFIG_PATH);

    if (!response.ok) {
        throw new Error(`Failed to load dashboard config: ${response.status}`);
    }

    return response.json();
}

function setOverview(data) {
    document.getElementById("cluster-name").textContent = data.clusterName || "Cluster Dashboard";
    document.getElementById("environment").textContent = data.environment || "Unknown";
    document.getElementById("last-updated").textContent = data.lastUpdated || "Unknown";
}

function createNodeCard(node) {
    const template = document.getElementById("node-card-template");
    const fragment = template.content.cloneNode(true);

    fragment.querySelector(".card-title").textContent = node.name;
    fragment.querySelector(".status-badge").textContent = node.status;
    fragment.querySelector(".node-role").textContent = node.role;
    fragment.querySelector(".node-model").textContent = node.model;
    fragment.querySelector(".node-ip").textContent = node.ip;
    fragment.querySelector(".node-purpose").textContent = node.purpose;

    return fragment;
}

function renderNodes(nodes) {
    const container = document.getElementById("nodes-grid");
    container.innerHTML = "";

    if (!Array.isArray(nodes) || nodes.length === 0) {
        container.innerHTML = '<p class="empty-text">No nodes configured.</p>';
        return;
    }

    nodes.forEach((node) => {
        container.appendChild(createNodeCard(node));
    });
}

function createServiceCard(service) {
    const template = document.getElementById("service-card-template");

    const fragment = template.content.cloneNode(true);
    const card = fragment.querySelector(".service-card");

    card.href = service.url || "#";
    fragment.querySelector(".card-title").textContent = service.name;
    fragment.querySelector(".service-description").textContent = service.description || "";

    return fragment;
}

function renderServices(services) {
    const container = document.getElementById("services-grid");
    container.innerHTML = "";

    if (!Array.isArray(services) || services.length === 0) {
        container.innerHTML = '<p class="empty-text">No services configured.</p>';
        return;
    }

    services.forEach((service) => {
        container.appendChild(createServiceCard(service));
    });
}

function renderError(message) {
    document.getElementById("nodes-grid").innerHTML = `<p class="error-text">${message}</p>`;
    document.getElementById("services-grid").innerHTML = `<p class="error-text">Unable to load services.</p>`;
}

async function initDashboard() {
    try {
        const data = await loadDashboardData();
        setOverview(data);
        renderNodes(data.nodes);
        renderServices(data.services);
    } catch (error) {
        console.error(error);
        renderError("Unable to load dashboard configuration.");
    }
}

initDashboard();