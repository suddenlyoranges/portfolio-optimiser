import { useAuth } from '../../hooks/useAuth';
import styles from './Navbar.module.css';

export default function Navbar() {
  const { user, dispatch } = useAuth();

  const handleLogout = () => {
    dispatch({ type: 'LOGOUT' });
  };

  return (
    <header className={styles.navbar}>
      <div className={styles.spacer} />
      <div className={styles.userArea}>
        {user && (
          <>
            <span className={styles.username}>
              {user.is_guest ? 'Guest' : user.username}
            </span>
            <button className={styles.logoutBtn} onClick={handleLogout}>
              Log out
            </button>
          </>
        )}
      </div>
    </header>
  );
}
