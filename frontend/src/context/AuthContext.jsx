import { createContext, useReducer, useEffect } from 'react';
import { getMe } from '../api/auth';

const AuthContext = createContext(null);

const initialState = {
  user: null,
  token: localStorage.getItem('access_token'),
  loading: true,
};

function authReducer(state, action) {
  switch (action.type) {
    case 'SET_USER':
      return { ...state, user: action.payload, loading: false };
    case 'LOGIN':
      localStorage.setItem('access_token', action.payload.token);
      return {
        ...state,
        token: action.payload.token,
        user: action.payload.user,
        loading: false,
      };
    case 'LOGOUT':
      localStorage.removeItem('access_token');
      return { ...state, token: null, user: null, loading: false };
    case 'LOADED':
      return { ...state, loading: false };
    default:
      return state;
  }
}

export function AuthProvider({ children }) {
  const [state, dispatch] = useReducer(authReducer, initialState);

  useEffect(() => {
    if (state.token) {
      getMe()
        .then((res) => dispatch({ type: 'SET_USER', payload: res.data }))
        .catch(() => dispatch({ type: 'LOGOUT' }));
    } else {
      dispatch({ type: 'LOADED' });
    }
  }, []);

  return (
    <AuthContext.Provider value={{ ...state, dispatch }}>
      {children}
    </AuthContext.Provider>
  );
}

export default AuthContext;
