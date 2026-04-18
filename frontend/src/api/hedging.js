import client from "./client";

export const computeBetaHedge = (portfolioId, data) =>
  client.post(`/hedge/${portfolioId}/beta`, data);
