import { NavLink } from "react-router-dom";
import styles from "./Sidebar.module.css";

const navItems = [
  { path: "/", label: "Dashboard" /*, icon: "\u{1F4CA}"*/ },
  { path: "/compare", label: "Compare" /*, icon: "\u{2696}\uFE0F"*/ },
];

export default function Sidebar() {
  return (
    <aside className={styles.sidebar}>
      <div className={styles.logo}>
        <h2>PortfolioOpt</h2>
      </div>
      <nav className={styles.nav}>
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end
            className={({ isActive }) =>
              `${styles.link} ${isActive ? styles.active : ""}`
            }
          >
            <span className={styles.icon}>{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
