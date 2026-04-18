import client from './client';

export const searchTickers = (query) =>
  client.get(`/market/search?q=${encodeURIComponent(query)}`);

export const getTickerInfo = (ticker) => client.get(`/market/info/${ticker}`);

export const getPrices = (ticker, start, end) => {
  const params = new URLSearchParams();
  if (start) params.append('start', start);
  if (end) params.append('end', end);
  return client.get(`/market/prices/${ticker}?${params}`);
};
