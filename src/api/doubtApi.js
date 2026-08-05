import api from "./axios";

export const getHistory = async (params = {}) => {
  const response = await api.get("/user_doubts", { params });
  return response.data;
};

export const solveDoubt = async (data) => {
  const response = await api.post("/doubts/solve-doubt", data);
  return response.data;
};

export const submitFeedback = async (data) => {
  const response = await api.post("/feedback", data);
  return response.data;
};

export const get_user_doubts = async (params = {}) => {
  const response = await api.get("/user_doubts", { params });
  return response.data;
};

export const submitBookmark = async (data) => {
  const response = await api.post("/bookmark", data);
  return response.data;
};

export const get_bookmarked_doubts = async (params = {}) => {
  const response = await api.get("/bookmarked_doubts", { params });
  return response.data;
};
