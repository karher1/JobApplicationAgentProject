"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { authAPI, tokenUtils } from "@/lib/auth-api";

export default function LoginPage() {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setSuccess("");

    try {
      if (isLogin) {
        // Login
        const response = await authAPI.login({ email, password });
        if (response.success && response.token) {
          tokenUtils.saveToken(response.token);
          setSuccess("Login successful! Redirecting...");
          setTimeout(() => {
            router.push("/");
          }, 1000);
        } else {
          setError(response.message || "Login failed");
        }
      } else {
        // Register
        const response = await authAPI.register({
          email,
          password,
          first_name: firstName,
          last_name: lastName,
        });
        if (response.success) {
          setSuccess("Registration successful! Please log in.");
          setIsLogin(true);
          setFirstName("");
          setLastName("");
        } else {
          setError(response.message || "Registration failed");
        }
      }
    } catch (error: any) {
      setError(error.message || "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-[#18122B] via-[#1E1E2F] to-[#232946] px-4">
      <div className="bg-[#232946] rounded-2xl shadow-2xl p-10 w-full max-w-md border border-[#2a2a40]">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold gradient-text mb-2">
            {isLogin ? "Welcome Back" : "Create Account"}
          </h1>
          <p className="text-white/60">
            {isLogin ? "Sign in to your account" : "Join Job Application Agent"}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {!isLogin && (
            <>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-white/80 mb-2">
                    First Name
                  </label>
                  <input
                    type="text"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    required
                    className="w-full px-4 py-3 bg-[#2a2a40] border border-[#3a3a50] rounded-lg text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-[#a18fff] focus:border-transparent"
                    placeholder="John"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-white/80 mb-2">
                    Last Name
                  </label>
                  <input
                    type="text"
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                    required
                    className="w-full px-4 py-3 bg-[#2a2a40] border border-[#3a3a50] rounded-lg text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-[#a18fff] focus:border-transparent"
                    placeholder="Doe"
                  />
                </div>
              </div>
            </>
          )}

          <div>
            <label className="block text-sm font-medium text-white/80 mb-2">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-4 py-3 bg-[#2a2a40] border border-[#3a3a50] rounded-lg text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-[#a18fff] focus:border-transparent"
              placeholder="john@example.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-white/80 mb-2">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
              className="w-full px-4 py-3 bg-[#2a2a40] border border-[#3a3a50] rounded-lg text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-[#a18fff] focus:border-transparent"
              placeholder="••••••••"
            />
          </div>

          {error && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3">
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}

          {success && (
            <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-3">
              <p className="text-green-400 text-sm">{success}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full glow-btn px-6 py-3 font-semibold text-lg disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <div className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                {isLogin ? "Signing in..." : "Creating account..."}
              </div>
            ) : (
              isLogin ? "Sign In" : "Create Account"
            )}
          </button>
        </form>

        <div className="mt-6 text-center">
          <button
            onClick={() => {
              setIsLogin(!isLogin);
              setError("");
              setSuccess("");
            }}
            className="text-[#a18fff] hover:text-[#fbc2eb] transition-colors"
          >
            {isLogin ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
          </button>
        </div>
      </div>
    </div>
  );
} 