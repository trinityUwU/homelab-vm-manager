// Client API : wrappers fetch typés sur les routes du backend.

async function request(method, path, body) {
  const opts = { method, headers: { "Content-Type": "application/json" } };
  if (body !== undefined) opts.body = JSON.stringify(body);
  const res = await fetch(path, opts);
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `Erreur ${res.status}`);
  }
  return res.status === 204 ? null : res.json();
}

export const api = {
  listVms: () => request("GET", "/api/vms"),
  refreshVms: () => request("POST", "/api/vms/refresh"),
  getVm: (id) => request("GET", `/api/vms/${id}`),
  refreshVm: (id) => request("GET", `/api/vms/${id}/refresh`),
  createVm: (data) => request("POST", "/api/vms", data),
  updateVm: (id, data) => request("PUT", `/api/vms/${id}`, data),
  deleteVm: (id) => request("DELETE", `/api/vms/${id}`),
  testSsh: (data) => request("POST", "/api/vms/test-ssh", data),
  provision: (id) => request("POST", `/api/vms/${id}/provision`),
  syncVm: (id) => request("POST", `/api/vms/${id}/sync`),
  getUpdates: () => request("GET", "/api/updates"),
  getSettings: () => request("GET", "/api/settings"),
  saveSettings: (data) => request("PUT", "/api/settings", data),
  getMotd: () => request("GET", "/api/motd/template"),
  saveMotd: (template) => request("PUT", "/api/motd/template", { template }),
  previewMotd: (template, vmId) => request("POST", "/api/motd/preview", { template, vm_id: vmId || null }),
};

// Ouvre le flux SSE des logs d'un job de provisioning.
export function openJobStream(jobId, onEvent) {
  const es = new EventSource(`/api/jobs/${jobId}/stream`);
  es.onmessage = (e) => onEvent(JSON.parse(e.data));
  es.onerror = () => es.close();
  return es;
}
