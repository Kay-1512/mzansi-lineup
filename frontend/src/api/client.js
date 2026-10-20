import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

export const client = axios.create({ baseURL: BASE_URL });

function getTokens() {
  return {
    access: localStorage.getItem("access_token"),
    refresh: localStorage.getItem("refresh_token"),
  };
}

export function setTokens({ access, refresh }) {
  if (access) localStorage.setItem("access_token", access);
  if (refresh) localStorage.setItem("refresh_token", refresh);
}

export function clearTokens() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

client.interceptors.request.use((config) => {
  const { access } = getTokens();
  if (access) config.headers.Authorization = `Bearer ${access}`;
  return config;
});

// A single in-flight refresh is shared across requests that 401 at the same
// time, so a page with several concurrent calls doesn't trigger a refresh storm.
let refreshPromise = null;

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { config, response } = error;
    const { refresh } = getTokens();

    if (response?.status !== 401 || config._retried || !refresh) {
      throw error;
    }
    config._retried = true;

    refreshPromise =
      refreshPromise ||
      axios
        .post(`${BASE_URL}/auth/token/refresh/`, { refresh })
        .then((res) => {
          setTokens({ access: res.data.access });
          return res.data.access;
        })
        .catch((refreshError) => {
          clearTokens();
          window.location.assign("/login");
          throw refreshError;
        })
        .finally(() => {
          refreshPromise = null;
        });

    const newAccess = await refreshPromise;
    config.headers.Authorization = `Bearer ${newAccess}`;
    return client(config);
  }
);
