export type RegisterValidationInput = {
  name: string;
  age?: string | number | null;
  email: string;
  password: string;
  confirmPassword?: string;
  accepted?: boolean;
};

export function validateFullName(name: string) {
  const cleanName = name.trim().replace(/\s+/g, " ");

  if (!cleanName) return "El nombre completo es obligatorio.";
  if (cleanName.length < 5) return "El nombre completo debe tener al menos 5 caracteres.";
  if (cleanName.length > 80) return "El nombre completo no debe superar los 80 caracteres.";

  const words = cleanName.split(" ");
  if (words.length < 2) return "Debe ingresar nombre y apellido.";

  const validNameRegex = /^[A-Za-zÁÉÍÓÚáéíóúÑñÜü\s]+$/;
  if (!validNameRegex.test(cleanName)) {
    return "El nombre solo debe contener letras y espacios.";
  }

  return "";
}

export function validateAge(age?: string | number | null) {
  if (age === undefined || age === null || age === "") return "";

  const numericAge = Number(age);

  if (Number.isNaN(numericAge)) return "La edad debe ser un número válido.";
  if (!Number.isInteger(numericAge)) return "La edad debe ser un número entero.";
  if (numericAge < 18) return "La edad mínima permitida es 18 años.";
  if (numericAge > 120) return "La edad ingresada no es válida.";

  return "";
}

export function validateEmailFormat(email: string) {
  const cleanEmail = email.trim().toLowerCase();

  if (!cleanEmail) return "El correo electrónico es obligatorio.";
  if (cleanEmail.length > 120) return "El correo electrónico es demasiado largo.";

  const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Za-z]{2,}$/;

  if (!emailRegex.test(cleanEmail)) {
    return "Ingrese un correo electrónico válido.";
  }

  const [localPart, domain] = cleanEmail.split("@");

  if (!localPart || !domain) return "Ingrese un correo electrónico válido.";
  if (localPart.length < 3) return "El correo electrónico no parece válido.";
  if (domain.includes("..")) return "El dominio del correo no es válido.";

  const blockedDomains = [
    "test.com",
    "example.com",
    "correo.com",
    "email.com",
    "fake.com",
    "prueba.com",
  ];

  if (blockedDomains.includes(domain)) {
    return "Use un correo electrónico personal válido.";
  }

  return "";
}

export function validatePassword(password: string, name?: string, email?: string) {
  if (!password) return "La contraseña es obligatoria.";
  if (password.length < 8) return "La contraseña debe tener al menos 8 caracteres.";
  if (password.length > 64) return "La contraseña no debe superar los 64 caracteres.";
  if (/\s/.test(password)) return "La contraseña no debe contener espacios.";

  if (!/[A-ZÁÉÍÓÚÑ]/.test(password)) {
    return "La contraseña debe incluir al menos una letra mayúscula.";
  }

  if (!/[a-záéíóúñ]/.test(password)) {
    return "La contraseña debe incluir al menos una letra minúscula.";
  }

  if (!/[0-9]/.test(password)) {
    return "La contraseña debe incluir al menos un número.";
  }

  if (!/[!@#$%^&*()_\-+=.[\]{};:'",.<>/?\\|`~]/.test(password)) {
    return "La contraseña debe incluir al menos un carácter especial.";
  }

  const lowerPassword = password.toLowerCase();

  if (email) {
    const emailName = email.split("@")[0]?.toLowerCase();

    if (emailName && emailName.length >= 4 && lowerPassword.includes(emailName)) {
      return "La contraseña no debe contener parte del correo electrónico.";
    }
  }

  if (name) {
    const nameParts = name
      .toLowerCase()
      .split(" ")
      .filter((part) => part.length >= 4);

    const containsName = nameParts.some((part) => lowerPassword.includes(part));

    if (containsName) {
      return "La contraseña no debe contener partes del nombre.";
    }
  }

  const weakPasswords = [
    "password",
    "password123",
    "contraseña",
    "contraseña123",
    "admin123",
    "qwerty123",
    "12345678",
    "123456789",
  ];

  if (weakPasswords.includes(lowerPassword)) {
    return "La contraseña es demasiado común.";
  }

  return "";
}

export function validateRegisterInput(input: RegisterValidationInput) {
  const errors: Record<string, string> = {};

  const nameError = validateFullName(input.name);
  if (nameError) errors.name = nameError;

  const ageError = validateAge(input.age);
  if (ageError) errors.age = ageError;

  const emailError = validateEmailFormat(input.email);
  if (emailError) errors.email = emailError;

  const passwordError = validatePassword(input.password, input.name, input.email);
  if (passwordError) errors.password = passwordError;

  if (input.confirmPassword !== undefined && input.password !== input.confirmPassword) {
    errors.confirmPassword = "Las contraseñas no coinciden.";
  }

  if (input.accepted !== undefined && !input.accepted) {
    errors.accepted = "Debe aceptar que el sistema no reemplaza una valoración médica.";
  }

  return {
    valid: Object.keys(errors).length === 0,
    errors,
  };
}