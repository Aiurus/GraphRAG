import { useMantineColorScheme } from "@mantine/core";
import { IconBrightness } from "@tabler/icons-react";
import { NavLink } from "react-router-dom";
import {
  IconBulb,
  IconFileImport,
  IconMessages,
} from "@tabler/icons-react";

import styles from "./styles.module.css";

const MAIN_MENU_LINKS = [
  { link: "/", label: "Introduction", icon: IconBulb },
  { link: "/import-articles/", label: "Import Database", icon: IconFileImport },
  { link: "/fetch-network/", label: "Fetch Network", icon: IconFileImport },
  { link: "/chat-agent/", label: "Chat agent", icon: IconMessages },
];

export function Sidebar() {
  const { setColorScheme, colorScheme } = useMantineColorScheme();

  const handleThemeChange = () => {
    setColorScheme(colorScheme === "dark" ? "light" : "dark");
  };

  const links = MAIN_MENU_LINKS.map((item) => (
    <NavLink
      className={({ isActive }) => (isActive ? styles.active : "")}
      to={item.link}
      key={item.label}
    >
      <item.icon className={styles.linkIcon} stroke={1.5} />
      <span>{item.label}</span>
    </NavLink>
  ));

  return (
    <nav className={styles.navbar}>
      <div className={styles.links}>{links}</div>
      <div className={styles.toolbox}>
        <span onClick={handleThemeChange}>
          <IconBrightness />
        </span>
      </div>
    </nav>
  );
}
