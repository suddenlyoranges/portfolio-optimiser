import { createContext, useReducer } from 'react';

const PortfolioContext = createContext(null);

const initialState = {
  portfolios: [],
  currentPortfolio: null,
  optimisationResult: null,
  backtestResult: null,
  loading: false,
  error: null,
};

function portfolioReducer(state, action) {
  switch (action.type) {
    case 'SET_PORTFOLIOS':
      return { ...state, portfolios: action.payload, loading: false };
    case 'SET_CURRENT':
      return { ...state, currentPortfolio: action.payload, loading: false };
    case 'SET_OPTIMISATION':
      return { ...state, optimisationResult: action.payload, loading: false };
    case 'SET_BACKTEST':
      return { ...state, backtestResult: action.payload, loading: false };
    case 'SET_LOADING':
      return { ...state, loading: true, error: null };
    case 'SET_ERROR':
      return { ...state, error: action.payload, loading: false };
    case 'CLEAR_RESULTS':
      return { ...state, optimisationResult: null, backtestResult: null };
    default:
      return state;
  }
}

export function PortfolioProvider({ children }) {
  const [state, dispatch] = useReducer(portfolioReducer, initialState);

  return (
    <PortfolioContext.Provider value={{ ...state, dispatch }}>
      {children}
    </PortfolioContext.Provider>
  );
}

export default PortfolioContext;
