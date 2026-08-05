import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { loginUser } from "../api/authApi";
import { getUserFacingError } from "../api/getUserFacingError";
import { useAuth } from "../context/AuthContext";
import toast from "react-hot-toast";

function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});
  const [formError, setFormError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const { setSession, user, initializing } = useAuth();

  const navigate = useNavigate();

  if (!initializing && user) {
    return <Navigate to="/ask-doubt" replace />;
  }

  const handleChange = (e) => {
    const { name, value } = e.target;
    if (name === "email") setEmail(value);
    if (name === "password") setPassword(value);
    setFieldErrors((prev) => ({ ...prev, [name]: "" }));
    setFormError("");
  };

  const validate = () => {
    const next = {};
    if (!email.trim()) next.email = "Email is required";
    if (!password) next.password = "Password is required";
    setFieldErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate() || submitting) return;

    try {
      setSubmitting(true);
      setFormError("");
      const data = await loginUser({ email, password });
      await setSession(data);
      toast.success("Login successful!");
      navigate("/ask-doubt");
    } catch (error) {
      const message = getUserFacingError(error, "Login failed. Please try again.");
      setFormError(message);
      toast.error(message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-yellow-300 via-green-300 to-green-500 flex items-center justify-center p-4 sm:p-6">
      <div className="w-full max-w-6xl bg-white rounded-3xl shadow-2xl overflow-hidden grid md:grid-cols-2">
        <div className="p-6 sm:p-10 flex flex-col justify-center">
          <h1 className="text-3xl sm:text-4xl font-bold text-green-700 mb-2">
            Welcome Back
          </h1>

          <p className="text-gray-500 mb-6 sm:mb-8 text-sm sm:text-base">
            Login to continue your learning journey
          </p>

          <form onSubmit={handleSubmit} className="space-y-5" noValidate>
            <div>
              <label htmlFor="login-email" className="mb-1.5 block text-sm font-semibold text-slate-700">
                Email
              </label>
              <input
                id="login-email"
                type="email"
                name="email"
                autoComplete="email"
                placeholder="Enter Email"
                value={email}
                onChange={handleChange}
                aria-invalid={Boolean(fieldErrors.email)}
                aria-describedby={fieldErrors.email ? "login-email-error" : undefined}
                className="w-full p-3 border-2 border-green-200 rounded-xl focus:outline-none focus-visible:border-green-500 focus-visible:ring-2 focus-visible:ring-green-400"
              />
              {fieldErrors.email ? (
                <p id="login-email-error" role="alert" className="mt-1 text-sm text-red-600">
                  {fieldErrors.email}
                </p>
              ) : null}
            </div>

            <div>
              <label htmlFor="login-password" className="mb-1.5 block text-sm font-semibold text-slate-700">
                Password
              </label>
              <input
                id="login-password"
                type="password"
                name="password"
                autoComplete="current-password"
                placeholder="Enter Password"
                value={password}
                onChange={handleChange}
                aria-invalid={Boolean(fieldErrors.password)}
                aria-describedby={fieldErrors.password ? "login-password-error" : undefined}
                className="w-full p-3 border-2 border-green-200 rounded-xl focus:outline-none focus-visible:border-green-500 focus-visible:ring-2 focus-visible:ring-green-400"
              />
              {fieldErrors.password ? (
                <p id="login-password-error" role="alert" className="mt-1 text-sm text-red-600">
                  {fieldErrors.password}
                </p>
              ) : null}
            </div>

            {formError ? (
              <p role="alert" className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                {formError}
              </p>
            ) : null}

            <button
              type="submit"
              disabled={submitting}
              aria-busy={submitting}
              className="w-full py-3 rounded-xl text-white font-bold bg-gradient-to-r from-green-500 to-yellow-400 transition duration-300 hover:scale-105 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-green-700 disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:scale-100"
            >
              {submitting ? "Logging in..." : "Login"}
            </button>
          </form>

          <p className="text-center text-gray-600 mt-6">
            Don&apos;t have an account?
            <Link to="/register" className="text-green-600 font-bold ml-1 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-green-700">
              Register
            </Link>
          </p>
        </div>

        <div className="hidden md:flex items-center justify-center bg-green-50 p-8">
          <img
            src="https://bmptranslations.co.uk/wp-content/uploads/2024/02/3.webp"
            alt="Student studying with AI learning assistant illustration"
            className="w-full max-w-md"
          />
        </div>
      </div>
    </div>
  );
}

export default Login;
