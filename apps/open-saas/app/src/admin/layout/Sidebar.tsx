import { LayoutDashboard, Sheet, X } from "lucide-react";
import { useEffect, useRef } from "react";
import { NavLink } from "react-router";
import Logo from "../../client/static/logo.webp";
import { cn } from "../../client/utils";

interface SidebarProps {
  sidebarOpen: boolean;
  setSidebarOpen: (arg: boolean) => void;
}

const Sidebar = ({ sidebarOpen, setSidebarOpen }: SidebarProps) => {
  const trigger = useRef<any>(null);
  const sidebar = useRef<any>(null);

  // close on click outside
  useEffect(() => {
    const clickHandler = ({ target }: MouseEvent) => {
      if (!sidebar.current || !trigger.current) return;
      if (
        !sidebarOpen ||
        sidebar.current.contains(target) ||
        trigger.current.contains(target)
      )
        return;
      setSidebarOpen(false);
    };
    document.addEventListener("click", clickHandler);
    return () => document.removeEventListener("click", clickHandler);
  });

  // close if the esc key is pressed
  useEffect(() => {
    const keyHandler = ({ keyCode }: KeyboardEvent) => {
      if (!sidebarOpen || keyCode !== 27) return;
      setSidebarOpen(false);
    };
    document.addEventListener("keydown", keyHandler);
    return () => document.removeEventListener("keydown", keyHandler);
  });

  return (
    <aside
      ref={sidebar}
      className={cn(
        "bg-muted absolute top-0 left-0 z-9999 flex h-screen w-72.5 flex-col overflow-y-hidden border-r duration-300 ease-linear lg:static lg:translate-x-0",
        {
          "translate-x-0": sidebarOpen,
          "-translate-x-full": !sidebarOpen,
        },
      )}
    >
      {/* <!-- SIDEBAR HEADER --> */}
      <div className="flex items-center justify-between gap-2 px-6 py-5.5 lg:py-6.5">
        <NavLink to="/">
          <img src={Logo} alt="Logo" width={50} />
        </NavLink>

        <button
          ref={trigger}
          onClick={() => setSidebarOpen(!sidebarOpen)}
          aria-controls="sidebar"
          aria-expanded={sidebarOpen}
          className="block lg:hidden"
        >
          <X />
        </button>
      </div>
      {/* <!-- SIDEBAR HEADER --> */}

      <div className="no-scrollbar flex flex-col overflow-y-auto duration-300 ease-linear">
        {/* <!-- Sidebar Menu --> */}
        <nav className="mt-5 px-4 py-4 lg:mt-9 lg:px-6">
          {/* <!-- Menu Group --> */}
          <div>
            <h3 className="text-muted-foreground mb-4 ml-4 text-sm font-semibold">
              MENU
            </h3>

            <ul className="mb-6 flex flex-col gap-1.5">
              {/* <!-- Menu Item Dashboard --> */}
              <NavLink
                to="/admin"
                end
                className={({ isActive }) =>
                  cn(
                    "text-muted-foreground hover:bg-accent hover:text-accent-foreground group relative flex items-center gap-2.5 rounded-sm px-4 py-2 font-medium duration-300 ease-in-out",
                    {
                      "bg-accent text-accent-foreground": isActive,
                    },
                  )
                }
              >
                <LayoutDashboard />
                Dashboard
              </NavLink>

              {/* <!-- Menu Item Dashboard --> */}

              {/* <!-- Menu Item Users --> */}
              <li>
                <NavLink
                  to="/admin/users"
                  end
                  className={({ isActive }) =>
                    cn(
                      "text-muted-foreground hover:bg-accent hover:text-accent-foreground group relative flex items-center gap-2.5 rounded-sm px-4 py-2 font-medium duration-300 ease-in-out",
                      {
                        "bg-accent text-accent-foreground": isActive,
                      },
                    )
                  }
                >
                  <Sheet />
                  Users
                </NavLink>
              </li>
              {/* <!-- Menu Item Users --> */}

            </ul>
          </div>
        </nav>
        {/* <!-- Sidebar Menu --> */}
      </div>
    </aside>
  );
};

export default Sidebar;
