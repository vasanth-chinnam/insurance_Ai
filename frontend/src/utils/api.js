export async function apiFetch(url, options = {}) {
  const token = localStorage.getItem("insureai_token");
  const tenantId = localStorage.getItem("insureai_tenant_id");
  
  const headers = { ...options.headers };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  if (tenantId) {
    headers["X-Tenant-ID"] = tenantId;
  }

  // Auto-detect JSON body
  if (options.body && !(options.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  return fetch(url, {
    ...options,
    headers
  });
}
