import axios from "axios";

const api = axios.create({ baseURL: "/api" });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const isLoginEndpoint = err.config?.url?.includes("/auth/login");
    if (err.response?.status === 401 && !isLoginEndpoint) {
      // Expired/invalid session → kick to login
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
    // For the login endpoint itself, just reject so the form can show the error
    return Promise.reject(err);
  }
);

export default api;
