import axios from "axios";
import { API_BASE_URL } from "./config";
import {
  clearAccessToken,
  getAccessToken,
  setAccessToken,
} from "./tokenStore";

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
});

api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let refreshPromise = null;

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const isAuthEndpoint = ["/auth/login", "/auth/register", "/auth/refresh"].some(
      (path) => originalRequest?.url?.includes(path),
    );

    if (
      error.response?.status !== 401 ||
      originalRequest?._retry ||
      isAuthEndpoint
    ) {
      return Promise.reject(error);
    }

    originalRequest._retry = true;
    try {
      if (!refreshPromise) {
        refreshPromise = axios
          .post(
            `${API_BASE_URL}/auth/refresh`,
            {},
            { withCredentials: true },
          )
          .then(({ data }) => {
            setAccessToken(data.access_token);
            window.dispatchEvent(
              new CustomEvent("auth:refreshed", { detail: data.user }),
            );
            return data.access_token;
          })
          .finally(() => {
            refreshPromise = null;
          });
      }

      const token = await refreshPromise;
      originalRequest.headers.Authorization = `Bearer ${token}`;
      return api(originalRequest);
    } catch (refreshError) {
      clearAccessToken();
      window.dispatchEvent(new Event("auth:logout"));
      return Promise.reject(refreshError);
    }
  },
);

export default api;
