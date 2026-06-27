import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { GraduationCap, Menu, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { useAuth } from "@/contexts/AuthContext";
import { useLanguage } from "@/contexts/LanguageContext";

const navLinkClass =
  "text-slate-600 hover:text-[#002FA7] transition-colors";

export const PublicSiteHeader = ({ variant = "full", children }) => {
  const { user } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);

  const closeMobile = () => setMobileOpen(false);

  const primaryAction = user ? (
    <Button
      onClick={() => {
        closeMobile();
        navigate("/dashboard");
      }}
      className="bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm"
      data-testid={variant === "full" ? "get-started-btn" : "dashboard-btn"}
    >
      {t("nav.dashboard")}
    </Button>
  ) : (
    <Button
      onClick={() => {
        closeMobile();
        navigate(variant === "full" ? "/register" : "/login");
      }}
      className="bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm"
      data-testid={variant === "full" ? "get-started-btn" : "login-btn"}
    >
      {variant === "full" ? t("nav.getStarted") : t("nav.login")}
    </Button>
  );

  const navLinks = (
    <>
      {variant === "full" && (
        <Link
          to="/courses"
          className={navLinkClass}
          data-testid="nav-courses"
          onClick={closeMobile}
        >
          {t("nav.courses")}
        </Link>
      )}
      {user ? (
        variant === "full" && (
          <Link
            to="/dashboard"
            className={navLinkClass}
            data-testid="nav-dashboard"
            onClick={closeMobile}
          >
            {t("nav.dashboard")}
          </Link>
        )
      ) : (
        variant === "full" && (
          <Link
            to="/login"
            className={navLinkClass}
            data-testid="nav-login"
            onClick={closeMobile}
          >
            {t("nav.login")}
          </Link>
        )
      )}
      {primaryAction}
      <LanguageSwitcher />
      {children}
    </>
  );

  const mobileLinks = (
    <>
      <Link
        to="/courses"
        className={navLinkClass}
        data-testid="mobile-nav-courses"
        onClick={closeMobile}
      >
        {t("nav.courses")}
      </Link>
      {user ? (
        <Link
          to="/dashboard"
          className={navLinkClass}
          data-testid="mobile-nav-dashboard"
          onClick={closeMobile}
        >
          {t("nav.dashboard")}
        </Link>
      ) : (
        <Link
          to="/login"
          className={navLinkClass}
          data-testid="mobile-nav-login"
          onClick={closeMobile}
        >
          {t("nav.login")}
        </Link>
      )}
      {!user && variant === "full" && (
        <Button
          onClick={() => {
            closeMobile();
            navigate("/register");
          }}
          className="bg-[#002FA7] hover:bg-[#002585] text-white rounded-sm w-full"
          data-testid="mobile-get-started-btn"
        >
          {t("nav.getStarted")}
        </Button>
      )}
      <div className="pt-2">
        <LanguageSwitcher />
      </div>
      {children}
    </>
  );

  return (
    <header className="backdrop-blur-xl bg-white/80 border-b border-slate-200 sticky top-0 z-50">
      <div className="container mx-auto px-6 md:px-12 lg:px-24 py-4 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2" data-testid="logo">
          <GraduationCap className="w-8 h-8 text-[#002FA7]" />
          <span className="text-xl font-medium tracking-tight text-[#0A0B10]">
            LearnHub
          </span>
        </Link>

        <nav className="hidden md:flex items-center gap-4 lg:gap-6">
          {navLinks}
        </nav>

        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="md:hidden rounded-sm"
          onClick={() => setMobileOpen((open) => !open)}
          aria-expanded={mobileOpen}
          aria-label={mobileOpen ? "Close menu" : "Open menu"}
          data-testid="mobile-menu-btn"
        >
          {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </Button>
      </div>

      {mobileOpen && (
        <nav
          className="md:hidden border-t border-slate-200 bg-white px-6 py-4 flex flex-col gap-4"
          data-testid="mobile-nav"
        >
          {mobileLinks}
        </nav>
      )}
    </header>
  );
};
