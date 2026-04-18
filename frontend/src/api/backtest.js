import client from './client';

export const runBacktest = (portfolioId, data) =>
  client.post(`/backtest/${portfolioId}`, data);

export const getBacktestResult = (resultId) =>
  client.get(`/backtest/results/${resultId}`);
