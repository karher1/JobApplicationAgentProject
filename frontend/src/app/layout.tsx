"use client";

import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";
import Link from "next/link";
import { useEffect, useState } from "react";
import { tokenUtils } from "@/lib/auth-api";

const inter = Inter({ subsets: ["latin"] });

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userFirstName, setUserFirstName] = useState("");

  useEffect(() => {
    const updateAuth = () => {
      const token = tokenUtils.getToken();
      if (token && !tokenUtils.isTokenExpired(token)) {
        setIsAuthenticated(true);
        setUserFirstName(token.first_name);
      } else {
        setIsAuthenticated(false);
        setUserFirstName("");
      }
    };
    updateAuth();
    window.addEventListener('storage', updateAuth);
    return () => window.removeEventListener('storage', updateAuth);
  }, []);

  const handleLogout = () => {
    tokenUtils.removeToken();
    setIsAuthenticated(false);
    setUserFirstName("");
    window.location.href = "/";
  };

  return (
    <html lang="en">
      <head>
        <title>Job Application Agent</title>
        <meta name="description" content="AI-powered job search and application automation" />
      </head>
      <body className={`${inter.className} bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 min-h-screen`}>
        <Providers>
          <div className="w-full flex justify-between items-center px-8 py-6 bg-black/20 backdrop-blur-sm border-b border-white/10">
            <Link href="/">
              <h1 className="text-2xl font-bold gradient-text">
                Job Application Agent
              </h1>
            </Link>
            <div className="flex items-center gap-4">
              <nav className="flex gap-4 mr-4">
                <Link href="/" className="text-white/70 hover:text-white transition-colors font-medium">
                  Home
                </Link>
                <Link href="/job-search" className="text-white/70 hover:text-white transition-colors font-medium">
                  Job Search
                </Link>
                <Link href="/chat" className="text-white/70 hover:text-white transition-colors font-medium">
                  AI Assistant
                </Link>
                <Link href="/profile" className="text-white/70 hover:text-white transition-colors font-medium">
                  Profile
                </Link>
                <Link href="/resume-analysis" className="text-white/70 hover:text-white transition-colors font-medium">
                  Resume Analysis
                </Link>
                <Link href="/applications" className="text-white/70 hover:text-white transition-colors font-medium">
                  Applications
                </Link>
                <Link href="/analytics" className="text-white/70 hover:text-white transition-colors font-medium">
                  Analytics
                </Link>
                <Link href="/recommendations" className="text-white/70 hover:text-white transition-colors font-medium">
                  Recommendations
                </Link>
              </nav>
              {isAuthenticated ? (
                <>
                  <span className="text-white/70 text-sm font-medium">Welcome, {userFirstName}</span>
                  <button
                    onClick={handleLogout}
                    className="px-4 py-2 text-white/70 hover:text-white transition-colors font-medium"
                  >
                    Logout
                  </button>
                </>
              ) : (
                <Link href="/login">
                  <button className="glow-btn px-6 py-2 font-semibold text-base">
                    Login
                  </button>
                </Link>
              )}
            </div>
          </div>
          {children}
        </Providers>
      </body>
    </html>
  );
}
