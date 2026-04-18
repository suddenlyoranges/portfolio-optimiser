import client from "./client";

export const runOptimisation = (portfolioId, data) =>
  client.post(`/optimise/${portfolioId}`, data);

export const getOptimisationResult = (resultId) =>
  client.get(`/optimise/results/${resultId}`);

export const listOptimisations = (portfolioId) =>
  client.get(`/optimise/history/${portfolioId}`);

export const exportOptimisationCsv = (resultId) =>
  client.get(`/optimise/results/${resultId}/csv`, { responseType: "blob" });
