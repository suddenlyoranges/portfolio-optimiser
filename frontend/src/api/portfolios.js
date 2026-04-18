import client from "./client";

export const listPortfolios = () => client.get("/portfolios/");
export const getPortfolio = (id) => client.get(`/portfolios/${id}`);
export const createPortfolio = (data) => client.post("/portfolios/", data);
export const updatePortfolio = (id, data) =>
  client.put(`/portfolios/${id}`, data);
export const deletePortfolio = (id) => client.delete(`/portfolios/${id}`);

export const getPortfolioMetrics = (id) =>
  client.get(`/portfolios/${id}/metrics`);

export const addAsset = (portfolioId, data) =>
  client.post(`/portfolios/${portfolioId}/assets/`, data);
export const removeAsset = (portfolioId, assetId) =>
  client.delete(`/portfolios/${portfolioId}/assets/${assetId}`);
export const uploadCsv = (portfolioId, file) => {
  const formData = new FormData();
  formData.append("file", file);
  return client.post(`/portfolios/${portfolioId}/assets/csv`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};
