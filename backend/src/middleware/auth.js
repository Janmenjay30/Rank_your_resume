import jwt from "jsonwebtoken";

const SECRET = process.env.JWT_SECRET || "change_me_in_production";

/**
 * Verify the Authorization: Bearer <token> header.
 * Attaches req.user = { id, email, role } on success.
 */
export function protect(req, res, next) {
  const header = req.headers.authorization;
  if (!header || !header.startsWith("Bearer ")) {
    return res.status(401).json({ error: "No token provided." });
  }

  const token = header.split(" ")[1];
  try {
    const decoded = jwt.verify(token, SECRET);
    req.user = decoded;
    next();
  } catch {
    return res.status(401).json({ error: "Invalid or expired token." });
  }
}

export function signToken(payload) {
  return jwt.sign(payload, SECRET, { expiresIn: "7d" });
}
