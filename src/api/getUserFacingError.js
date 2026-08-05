const DEFAULT_MESSAGE = "Something went wrong. Please try again.";

const STATUS_MESSAGES = {
  401: "Please sign in again.",
  403: "You don't have permission to do that.",
  404: "We couldn't find what you're looking for.",
  413: "That file is too large. Please try a smaller one.",
  422: "Please check your input and try again.",
  429: "Too many requests. Please try again later.",
  500: DEFAULT_MESSAGE,
  502: DEFAULT_MESSAGE,
  503: DEFAULT_MESSAGE,
};

/** Words that mean the message is too technical for end users. */
const TECHNICAL_PATTERN =
  /\b(api|database|sql|token|jwt|stack|traceback|axios|exception|postgres|redis|openai|gemini|internal server|status code|request failed|network error)\b/i;

function looksTechnical(message) {
  return TECHNICAL_PATTERN.test(message);
}

/**
 * Prefer a simple backend message; never show raw Axios / network strings.
 */
export function getUserFacingError(err, fallback = DEFAULT_MESSAGE) {
  const apiMessage = err?.response?.data?.error?.message;
  if (
    typeof apiMessage === "string" &&
    apiMessage.trim() &&
    !looksTechnical(apiMessage)
  ) {
    return apiMessage.trim();
  }

  const status = err?.response?.status;
  if (status && STATUS_MESSAGES[status]) {
    return STATUS_MESSAGES[status];
  }

  if (!err?.response) {
    return "Unable to connect. Please check your internet and try again.";
  }

  return fallback;
}

export function getErrorCode(err) {
  return err?.response?.data?.error?.code || null;
}
