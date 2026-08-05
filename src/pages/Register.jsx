import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { registerUser } from "../api/authApi";
import { getUserFacingError } from "../api/getUserFacingError";
import { useAuth } from "../context/AuthContext";
import toast from "react-hot-toast";

function Register() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});
  const [formError, setFormError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const { setSession, user, initializing } = useAuth();

  const navigate = useNavigate();

  if (!initializing && user) {
    return <Navigate to="/ask-doubt" replace />;
  }

  const handleChange = (e) => {
    const { name: field, value } = e.target;
    if (field === "name") setName(value);
    if (field === "email") setEmail(value);
    if (field === "password") setPassword(value);
    if (field === "confirmPassword") setConfirmPassword(value);
    setFieldErrors((prev) => ({ ...prev, [field]: "" }));
    setFormError("");
  };

  const validate = () => {
    const next = {};
    if (!name.trim()) next.name = "Name is required";
    if (!email.trim()) next.email = "Email is required";
    if (!password) next.password = "Password is required";
    if (!confirmPassword) next.confirmPassword = "Confirm your password";
    else if (password !== confirmPassword) {
      next.confirmPassword = "Passwords do not match";
    }
    setFieldErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate() || submitting) return;

    try {
      setSubmitting(true);
      setFormError("");
      const data = await registerUser({ name, email, password });
      await setSession(data);
      toast.success("Registration successful!");
      navigate("/ask-doubt");
    } catch (error) {
      const message = getUserFacingError(
        error,
        "Registration failed. Please try again.",
      );
      setFormError(message);
      toast.error(message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-600 via-pink-500 to-orange-400 flex items-center justify-center p-4 sm:p-6">
      <div className="w-full max-w-6xl bg-white rounded-3xl shadow-2xl overflow-hidden grid md:grid-cols-2">
        <div className="p-6 sm:p-10 flex flex-col justify-center">
          <h1 className="text-3xl sm:text-4xl font-bold mb-2">Create Account</h1>

          <p className="text-gray-500 mb-6 sm:mb-8 text-sm sm:text-base">
            Join the AI Doubt Solver Platform
          </p>

          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            <div>
              <label htmlFor="register-name" className="mb-1.5 block text-sm font-semibold text-slate-700">
                Name
              </label>
              <input
                id="register-name"
                type="text"
                name="name"
                autoComplete="name"
                placeholder="Name"
                value={name}
                onChange={handleChange}
                aria-invalid={Boolean(fieldErrors.name)}
                aria-describedby={fieldErrors.name ? "register-name-error" : undefined}
                className="w-full p-3 border rounded-xl focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-600"
              />
              {fieldErrors.name ? (
                <p id="register-name-error" role="alert" className="mt-1 text-sm text-red-600">
                  {fieldErrors.name}
                </p>
              ) : null}
            </div>

            <div>
              <label htmlFor="register-email" className="mb-1.5 block text-sm font-semibold text-slate-700">
                Email
              </label>
              <input
                id="register-email"
                type="email"
                name="email"
                autoComplete="email"
                placeholder="Email"
                value={email}
                onChange={handleChange}
                aria-invalid={Boolean(fieldErrors.email)}
                aria-describedby={fieldErrors.email ? "register-email-error" : undefined}
                className="w-full p-3 border rounded-xl focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-600"
              />
              {fieldErrors.email ? (
                <p id="register-email-error" role="alert" className="mt-1 text-sm text-red-600">
                  {fieldErrors.email}
                </p>
              ) : null}
            </div>

            <div>
              <label htmlFor="register-password" className="mb-1.5 block text-sm font-semibold text-slate-700">
                Password
              </label>
              <input
                id="register-password"
                type="password"
                name="password"
                autoComplete="new-password"
                placeholder="Password"
                value={password}
                onChange={handleChange}
                aria-invalid={Boolean(fieldErrors.password)}
                aria-describedby={fieldErrors.password ? "register-password-error" : undefined}
                className="w-full p-3 border rounded-xl focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-600"
              />
              {fieldErrors.password ? (
                <p id="register-password-error" role="alert" className="mt-1 text-sm text-red-600">
                  {fieldErrors.password}
                </p>
              ) : null}
            </div>

            <div>
              <label htmlFor="register-confirm-password" className="mb-1.5 block text-sm font-semibold text-slate-700">
                Confirm Password
              </label>
              <input
                id="register-confirm-password"
                type="password"
                name="confirmPassword"
                autoComplete="new-password"
                placeholder="Confirm Password"
                value={confirmPassword}
                onChange={handleChange}
                aria-invalid={Boolean(fieldErrors.confirmPassword)}
                aria-describedby={
                  fieldErrors.confirmPassword
                    ? "register-confirm-password-error"
                    : undefined
                }
                className="w-full p-3 border rounded-xl focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-600"
              />
              {fieldErrors.confirmPassword ? (
                <p
                  id="register-confirm-password-error"
                  role="alert"
                  className="mt-1 text-sm text-red-600"
                >
                  {fieldErrors.confirmPassword}
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
              className="w-full py-3 rounded-xl text-white font-bold bg-gradient-to-r from-purple-600 via-pink-500 to-orange-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-800 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {submitting ? "Creating account..." : "Register"}
            </button>
          </form>
          <p className="text-center text-gray-600 mt-6">
            Already have an account?
            <Link to="/" className="text-purple-600 font-bold ml-1 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-700">
              Login
            </Link>
          </p>
        </div>

        <div className="hidden md:flex items-center justify-center bg-purple-50 p-8">
          <img
            src="https://www.logicalclass.com/assets/assets2/img/gallery/Ai.png"
            alt="AI tutor helping a student with academic questions"
            className="w-full max-w-md"
          />
        </div>
      </div>
    </div>
  );
}

export default Register;
