import axios from "axios";

const api = axios.create({ baseURL: "/api" });

// Attach JWT to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("rc_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Auth
export const register = (data) => api.post("/auth/register", data);
export const login = (data) => api.post("/auth/login", data);
export const getMe = () => api.get("/auth/me");

// Resumes
export const getResumes = () => api.get("/resumes");
export const uploadResume = (formData) =>
  api.post("/resumes/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
export const deleteResume = (id) => api.delete(`/resumes/${id}`);

// Ranking
export const rankUpload = (formData) =>
  api.post("/rank/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
export const rankStored = (jd, top_k = 20) =>
  api.post("/rank/stored", { jd, top_k });
export const getHistory = () => api.get("/rank/history");
export const getHistoryItem = (id) => api.get(`/rank/history/${id}`);

export default api;
