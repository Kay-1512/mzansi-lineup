import { client } from "./client";

export async function getForYouEvents(params = {}) {
  const { data } = await client.get("/events/", { params });
  return data;
}

export async function getSavedEvents() {
  const { data } = await client.get("/events/saved/");
  return data.results;
}

export async function saveEvent(id) {
  await client.post(`/events/${id}/save/`);
}

export async function unsaveEvent(id) {
  await client.delete(`/events/${id}/save/`);
}

export async function hideEvent(id) {
  await client.post(`/events/${id}/hide/`);
}

export async function getManualEvents() {
  const { data } = await client.get("/manual-events/");
  return data;
}

export async function createManualEvent(payload) {
  const { data } = await client.post("/manual-events/", payload);
  return data;
}

export async function deleteManualEvent(id) {
  await client.delete(`/manual-events/${id}/`);
}

export async function getInstagramPosts() {
  const { data } = await client.get("/instagram-posts/");
  return data.results;
}
