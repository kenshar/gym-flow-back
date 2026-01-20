export const validateRequest = (schema) => {
  return (req, res, next) => {
    const { error } = schema.validate(req.body, { abortEarly: false });

    if (error) {
      const errors = error.details.map((detail) => detail.message);
      return res.status(400).json({ message: 'Validation error', errors });
    }

    next();
  };
};

// Simple validation helpers
export const validateEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

export const validatePhone = (phone) => {
  const phoneRegex = /^[\d\s\-+()]{10,}$/;
  return phoneRegex.test(phone);
};

export const sanitizeInput = (input) => {
  if (typeof input !== 'string') return input;
  return input.trim().replace(/<[^>]*>/g, '');
};
