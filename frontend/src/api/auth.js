import { client, clearTokens, setTokens } from "./client";

export async function register(email, password) {
  await client.post("/auth/register/", { email, password });
}

export async function login(email, password) {
  const { data } = await client.post("/auth/token/", { username: email, password });
  setTokens({ access: data.access, refresh: data.refresh });
}

export function logout() {
  clearTokens();
}

export async function getProfile() {
  const { data } = await client.get("/profile/");
  return data;
}

export async function updateProfile(patch) {
  const { data } = await client.patch("/profile/", patch);
  return data;
}
