import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { forgotPassword } from "../api";
import reviewBackground from "../../assets/review_bg.png";

// SVG Brand Mark
function BrandMark() {
  return <span className="brand-mark auth-brand-mark" aria-hidden="true" />;
}

// Google SVG Icon
function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
      <path
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
        fill="#4285F4"
      />
      <path
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
        fill="#34A853"
      />
      <path
        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
        fill="#FBBC05"
      />
      <path
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
        fill="#EA4335"
      />
    </svg>
  );
}

// GitHub SVG Icon
function GitHubIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
      />
    </svg>
  );
}

// Apple SVG Icon
function AppleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
      <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M15.97 6.38c.62-.75 1.04-1.8 0.93-2.85-.9.04-1.98.6-2.61 1.34-.56.63-1.04 1.68-.91 2.7.99.08 2.01-.48 2.59-1.19z" />
    </svg>
  );
}

// Static prompt prefix and dynamic animated suffixes for the right showcase panel
const STATIC_PROMPT_PREFIX = "Ask BuildBuddy to build ";
const CYCLING_SUFFIXES = [
  "your blog.",
  "an AI dashboard.",
  "your SaaS landing page.",
  "an e-commerce store.",
  "your developer portfolio.",
];

export const AuthModal: React.FC = () => {
  const {
    isAuthModalOpen,
    closeAuthModal,
    modalMode,
    login,
    register,
  } = useAuth();

  // Mode: "login" | "signup" | "forgot"
  const [currentMode, setCurrentMode] = useState<"login" | "signup" | "forgot">(
    modalMode
  );

  // Signup step: 1 (credentials) | 2 (onboarding questions)
  const [signupStep, setSignupStep] = useState<1 | 2>(1);

  // Form Fields
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [role, setRole] = useState("Software Engineer / Developer");
  const [buildIntent, setBuildIntent] = useState("Web Applications & MVPs");

  // Status & Feedback
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [infoNotice, setInfoNotice] = useState<string | null>(null);
  const [forgotSuccess, setForgotSuccess] = useState<string | null>(null);

  // Animated Prompt suffix state on right panel
  const [suffixIndex, setSuffixIndex] = useState(0);
  const [displayedSuffix, setDisplayedSuffix] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);

  // Sync mode when modalMode changes
  useEffect(() => {
    setCurrentMode(modalMode);
    setSignupStep(1);
    setErrorMessage(null);
    setInfoNotice(null);
    setForgotSuccess(null);
  }, [modalMode, isAuthModalOpen]);

  // Handle escape key to close modal
  useEffect(() => {
    if (!isAuthModalOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") closeAuthModal();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isAuthModalOpen, closeAuthModal]);

  // Typing animation effect: keeps STATIC_PROMPT_PREFIX static and animates displayedSuffix
  useEffect(() => {
    if (!isAuthModalOpen) return;
    const currentSuffix = CYCLING_SUFFIXES[suffixIndex];
    let timer: ReturnType<typeof setTimeout>;

    if (!isDeleting) {
      if (displayedSuffix.length < currentSuffix.length) {
        timer = setTimeout(() => {
          setDisplayedSuffix(currentSuffix.slice(0, displayedSuffix.length + 1));
        }, 55);
      } else {
        timer = setTimeout(() => setIsDeleting(true), 2400);
      }
    } else {
      if (displayedSuffix.length > 0) {
        timer = setTimeout(() => {
          setDisplayedSuffix(currentSuffix.slice(0, displayedSuffix.length - 1));
        }, 30);
      } else {
        setIsDeleting(false);
        setSuffixIndex((prev) => (prev + 1) % CYCLING_SUFFIXES.length);
      }
    }

    return () => clearTimeout(timer);
  }, [displayedSuffix, isDeleting, suffixIndex, isAuthModalOpen]);

  if (!isAuthModalOpen) return null;

  // Placeholder handler for OAuth buttons
  const handleSocialClick = (provider: string) => {
    setInfoNotice(
      `${provider} sign-in is coming soon. Please continue with your email and password.`
    );
    setTimeout(() => setInfoNotice(null), 4500);
  };

  // Switch between Login and Signup modes
  const switchToSignup = () => {
    setCurrentMode("signup");
    setSignupStep(1);
    setErrorMessage(null);
  };

  const switchToLogin = () => {
    setCurrentMode("login");
    setSignupStep(1);
    setErrorMessage(null);
  };

  const switchToForgot = () => {
    setCurrentMode("forgot");
    setErrorMessage(null);
    setForgotSuccess(null);
  };

  // Handle Login submission
  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!email.trim() || !password) {
      setErrorMessage("Please enter both your email and password.");
      return;
    }

    setIsSubmitting(true);
    try {
      await login(email.trim(), password);
    } catch (err: any) {
      setErrorMessage(err.message || "Invalid email or password.");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle Signup Step 1 (Credentials Validation)
  const handleSignupStep1Submit = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email.trim())) {
      setErrorMessage("Please enter a valid email address.");
      return;
    }

    if (password.length < 8) {
      setErrorMessage("Password must be at least 8 characters long.");
      return;
    }

    // Advance to Step 2 (Onboarding questions)
    setSignupStep(2);
  };

  // Handle Signup Step 2 (Onboarding Details & Account Creation)
  const handleSignupStep2Submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    setIsSubmitting(true);
    try {
      const orgName = fullName.trim()
        ? `${fullName.trim()}'s Workspace`
        : undefined;

      await register(email.trim(), password, orgName, {
        name: fullName.trim() || undefined,
        role: role,
        buildIntent: buildIntent,
      });
    } catch (err: any) {
      setErrorMessage(err.message || "Registration failed. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle Forgot Password submission
  const handleForgotSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setForgotSuccess(null);

    if (!email.trim()) {
      setErrorMessage("Please enter your registered email address.");
      return;
    }

    setIsSubmitting(true);
    try {
      await forgotPassword(email.trim());
      setForgotSuccess(
        "A password reset link has been dispatched! Please check your inbox or terminal output."
      );
    } catch (err: any) {
      setErrorMessage(err.message || "Unable to send password reset link.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-modal-overlay" onClick={closeAuthModal}>
      {/* Outer wrapper to place close button cleanly on the outer frame */}
      <div
        className="auth-modal-outer-frame"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button on the Outer Box */}
        <button
          className="auth-modal-close-btn"
          onClick={closeAuthModal}
          aria-label="Close dialog"
          type="button"
        >
          ✕
        </button>

        {/* Floating Top Banner for Informative Notices (avoids pushing the layout or clipping logo) */}
        {infoNotice && (
          <div className="auth-floating-notice-banner" role="status">
            <span className="notice-icon">ℹ️</span>
            <span>{infoNotice}</span>
          </div>
        )}

        {/* Main Dialog Box */}
        <div className="auth-modal-dialog" role="dialog" aria-modal="true">
          <div className="auth-modal-split-layout">
            {/* ================= LEFT COLUMN: AUTH FORMS ================= */}
            <div className="auth-modal-left-col">
              {/* Top Brand Logo - Anchored at the top, never pushed out of bounds */}
              <div className="auth-header-mark">
                <BrandMark />
              </div>

              {/* Inline Success banner */}
              {forgotSuccess && (
                <div className="auth-inline-banner success-banner">
                  <span className="banner-icon">✅</span>
                  <span>{forgotSuccess}</span>
                </div>
              )}

              {/* ---------- VIEW 1: LOG IN ---------- */}
              {currentMode === "login" && (
                <div className="auth-form-container">
                  <h2 className="auth-title">Log in</h2>

                  {/* Social Login Placeholders (No hardcoded "Last Used" badge) */}
                  <div className="auth-social-buttons">
                    <button
                      type="button"
                      className="auth-social-btn"
                      onClick={() => handleSocialClick("Google")}
                    >
                      <span className="social-icon">
                        <GoogleIcon />
                      </span>
                      <span className="social-label">Continue with Google</span>
                    </button>

                    <button
                      type="button"
                      className="auth-social-btn"
                      onClick={() => handleSocialClick("GitHub")}
                    >
                      <span className="social-icon">
                        <GitHubIcon />
                      </span>
                      <span className="social-label">Continue with GitHub</span>
                    </button>

                    <button
                      type="button"
                      className="auth-social-btn"
                      onClick={() => handleSocialClick("Apple")}
                    >
                      <span className="social-icon">
                        <AppleIcon />
                      </span>
                      <span className="social-label">Continue with Apple</span>
                    </button>
                  </div>

                  {/* OR Divider */}
                  <div className="auth-divider">
                    <span className="divider-text">OR</span>
                  </div>

                  {/* Email & Password Form */}
                  <form onSubmit={handleLoginSubmit} className="auth-fields-form">
                    <div className="auth-input-group">
                      <label htmlFor="login-email" className="auth-label">
                        Email
                      </label>
                      <input
                        id="login-email"
                        type="email"
                        className="auth-input"
                        placeholder="Email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                        autoFocus
                      />
                    </div>

                    <div className="auth-input-group">
                      <div className="auth-label-row">
                        <label htmlFor="login-password" className="auth-label">
                          Password
                        </label>
                        <button
                          type="button"
                          className="auth-link-subtle"
                          onClick={switchToForgot}
                        >
                          Forgot password?
                        </button>
                      </div>
                      <input
                        id="login-password"
                        type="password"
                        className="auth-input"
                        placeholder="Password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                      />
                    </div>

                    {/* Inline Form Error */}
                    {errorMessage && (
                      <div className="auth-inline-banner error-banner">
                        <span className="banner-icon">⚠️</span>
                        <span>{errorMessage}</span>
                      </div>
                    )}

                    {/* Primary Continue Button - Solid, No Gradient */}
                    <button
                      type="submit"
                      className="auth-primary-btn"
                      disabled={isSubmitting}
                    >
                      {isSubmitting ? "Logging in..." : "Continue"}
                    </button>
                  </form>

                  {/* Toggle Link */}
                  <div className="auth-toggle-footer">
                    <span className="toggle-text">Don't have an account? </span>
                    <button
                      type="button"
                      className="auth-toggle-link"
                      onClick={switchToSignup}
                    >
                      Create your account
                    </button>
                  </div>

                </div>
              )}

              {/* ---------- VIEW 2: SIGN UP STEP 1 (Credentials) ---------- */}
              {currentMode === "signup" && signupStep === 1 && (
                <div className="auth-form-container">
                  <h2 className="auth-title">Create an account</h2>

                  {/* Social Sign up Placeholders */}
                  <div className="auth-social-buttons">
                    <button
                      type="button"
                      className="auth-social-btn"
                      onClick={() => handleSocialClick("Google")}
                    >
                      <span className="social-icon">
                        <GoogleIcon />
                      </span>
                      <span className="social-label">Continue with Google</span>
                    </button>

                    <button
                      type="button"
                      className="auth-social-btn"
                      onClick={() => handleSocialClick("GitHub")}
                    >
                      <span className="social-icon">
                        <GitHubIcon />
                      </span>
                      <span className="social-label">Continue with GitHub</span>
                    </button>

                    <button
                      type="button"
                      className="auth-social-btn"
                      onClick={() => handleSocialClick("Apple")}
                    >
                      <span className="social-icon">
                        <AppleIcon />
                      </span>
                      <span className="social-label">Continue with Apple</span>
                    </button>
                  </div>

                  {/* OR Divider */}
                  <div className="auth-divider">
                    <span className="divider-text">OR</span>
                  </div>

                  {/* Email & Password Form */}
                  <form onSubmit={handleSignupStep1Submit} className="auth-fields-form">
                    <div className="auth-input-group">
                      <label htmlFor="signup-email" className="auth-label">
                        Email
                      </label>
                      <input
                        id="signup-email"
                        type="email"
                        className="auth-input"
                        placeholder="Email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                        autoFocus
                      />
                    </div>

                    <div className="auth-input-group">
                      <label htmlFor="signup-password" className="auth-label">
                        Password
                      </label>
                      <input
                        id="signup-password"
                        type="password"
                        className="auth-input"
                        placeholder="At least 8 characters"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                      />
                    </div>

                    {/* Inline Form Error */}
                    {errorMessage && (
                      <div className="auth-inline-banner error-banner">
                        <span className="banner-icon">⚠️</span>
                        <span>{errorMessage}</span>
                      </div>
                    )}

                    {/* Primary Continue Button - Solid, No Gradient */}
                    <button type="submit" className="auth-primary-btn">
                      Continue
                    </button>
                  </form>

                  {/* Toggle Link */}
                  <div className="auth-toggle-footer">
                    <span className="toggle-text">Already have an account? </span>
                    <button
                      type="button"
                      className="auth-toggle-link"
                      onClick={switchToLogin}
                    >
                      Log in
                    </button>
                  </div>

                </div>
              )}

              {/* ---------- VIEW 3: SIGN UP STEP 2 (Onboarding Details) ---------- */}
              {currentMode === "signup" && signupStep === 2 && (
                <div className="auth-form-container">
                  <div className="auth-step-header">
                    <span className="auth-step-badge">Step 2 of 2</span>
                    <h2 className="auth-title">Tell us about yourself</h2>
                    <p className="auth-subtitle">
                      A few quick details to personalize your BuildBuddy workspace.
                    </p>
                  </div>

                  <form onSubmit={handleSignupStep2Submit} className="auth-fields-form">
                    {/* Question 1: Name */}
                    <div className="auth-input-group">
                      <label htmlFor="signup-fullname" className="auth-label">
                        What is your full name?
                      </label>
                      <input
                        id="signup-fullname"
                        type="text"
                        className="auth-input"
                        placeholder="e.g. Alex Morgan"
                        value={fullName}
                        onChange={(e) => setFullName(e.target.value)}
                        required
                        autoFocus
                      />
                    </div>

                    {/* Question 2: What do you do? */}
                    <div className="auth-input-group">
                      <label className="auth-label">
                        What best describes what you do?
                      </label>
                      <div className="auth-chip-grid">
                        {[
                          "Software Engineer",
                          "Designer",
                          "Founder / PM",
                          "Student / Learner",
                          "Other",
                        ].map((item) => (
                          <button
                            key={item}
                            type="button"
                            className={`auth-select-chip ${role === item ? "selected" : ""
                              }`}
                            onClick={() => setRole(item)}
                          >
                            {item}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Question 3: What are you planning to build? */}
                    <div className="auth-input-group">
                      <label className="auth-label">
                        What things will you build?
                      </label>
                      <div className="auth-chip-grid">
                        {[
                          "Web Applications",
                          "Landing Pages",
                          "Internal Tools",
                          "AI Prototypes",
                        ].map((item) => (
                          <button
                            key={item}
                            type="button"
                            className={`auth-select-chip ${buildIntent === item ? "selected" : ""
                              }`}
                            onClick={() => setBuildIntent(item)}
                          >
                            {item}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Inline Form Error */}
                    {errorMessage && (
                      <div className="auth-inline-banner error-banner">
                        <span className="banner-icon">⚠️</span>
                        <span>{errorMessage}</span>
                      </div>
                    )}

                    {/* Button Row: Back & Submit */}
                    <div className="auth-step-button-row">
                      <button
                        type="button"
                        className="auth-secondary-btn"
                        onClick={() => setSignupStep(1)}
                        disabled={isSubmitting}
                      >
                        Back
                      </button>
                      <button
                        type="submit"
                        className="auth-primary-btn"
                        disabled={isSubmitting}
                      >
                        {isSubmitting ? "Creating workspace..." : "Create Account"}
                      </button>
                    </div>
                  </form>
                </div>
              )}

              {/* ---------- VIEW 4: FORGOT PASSWORD ---------- */}
              {currentMode === "forgot" && (
                <div className="auth-form-container">
                  <h2 className="auth-title">Reset password</h2>
                  <p className="auth-subtitle">
                    Enter your email address and we'll send you instructions to
                    reset your password.
                  </p>

                  <form onSubmit={handleForgotSubmit} className="auth-fields-form">
                    <div className="auth-input-group">
                      <label htmlFor="forgot-email" className="auth-label">
                        Email
                      </label>
                      <input
                        id="forgot-email"
                        type="email"
                        className="auth-input"
                        placeholder="Email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                        autoFocus
                      />
                    </div>

                    {/* Inline Form Error */}
                    {errorMessage && (
                      <div className="auth-inline-banner error-banner">
                        <span className="banner-icon">⚠️</span>
                        <span>{errorMessage}</span>
                      </div>
                    )}

                    <button
                      type="submit"
                      className="auth-primary-btn"
                      disabled={isSubmitting}
                    >
                      {isSubmitting ? "Sending..." : "Send Reset Link"}
                    </button>
                  </form>

                  <div className="auth-toggle-footer">
                    <button
                      type="button"
                      className="auth-toggle-link"
                      onClick={switchToLogin}
                    >
                      ← Back to log in
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* ================= RIGHT COLUMN: PREVIEW CARD WITH REVIEW_BG.PNG ================= */}
            <div className="auth-modal-right-col">
              <div
                className="auth-preview-card"
                style={{ backgroundImage: `url(${reviewBackground})` }}
              >
                {/* Subtle gradient vignette overlay */}
                <div className="auth-preview-overlay" />

                {/* Floating Prompt Bar matching Lovable Screenshot */}
                <div className="auth-floating-prompt-bar">
                  <div className="prompt-text-wrapper">
                    {/* Static prefix */}
                    <span className="prompt-static-prefix">
                      {STATIC_PROMPT_PREFIX}
                    </span>
                    {/* Animated dynamic suffix */}
                    <span className="prompt-dynamic-suffix">
                      {displayedSuffix}
                    </span>
                    {/* Blinking cursor */}
                    <span className="blinking-caret" />
                  </div>

                  {/* Circular Submit Button - Purely FOR SHOW, not clickable/interactive */}
                  <div
                    className="prompt-action-circle for-show"
                    aria-hidden="true"
                    role="presentation"
                  >
                    <span className="prompt-arrow-icon">↑</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
